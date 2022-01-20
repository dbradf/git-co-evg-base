"""Unit tests for evg_service.py."""
from enum import Enum
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest
from evergreen import Build, EvergreenApi, Manifest, Project, Task, Version
from evergreen.manifest import ManifestModule
from requests.exceptions import HTTPError

import goodbase.services.evg_service as under_test
from goodbase.build_checker import BuildChecks
from goodbase.services.file_service import FileService


class TaskStatus(int, Enum):
    SUCCESS = 0
    FAILED = 1
    INACTIVE = 2


def build_mock_task(name: str, status: TaskStatus) -> Task:
    mock_task = MagicMock(spec_set=Task, display_name=name)
    if status == TaskStatus.SUCCESS or status == TaskStatus.FAILED:
        mock_task.is_undispatched.return_value = False
        mock_task.is_success.return_value = status == TaskStatus.SUCCESS
    else:
        mock_task.is_undispatched.return_value = True
        mock_task.is_success.return_value = False
    return mock_task


def build_mock_build(name: str, task_list: List[Task]) -> Build:
    mock_build = MagicMock(spec_set=Build, display_name=name, build_variant=name)
    mock_build.get_tasks.return_value = task_list
    return mock_build


def build_mock_version(build_names: List[str]) -> Version:
    mock_version = MagicMock(spec=Version)
    mock_version.build_variants_map = {build_name: build_name for build_name in build_names}
    return mock_version


def build_mock_project(index):
    mock_project = MagicMock(
        spec=Project, identifier=f"project {index}", remote_path=f"remote/path/{index}"
    )
    return mock_project


def build_mock_manifest(modules: Optional[Dict[str, str]]) -> Manifest:
    mock_manifest = MagicMock(spec=Manifest)
    if modules is not None:
        mock_manifest.modules = {
            k: MagicMock(spec=ManifestModule, revision=v) for k, v in modules.items()
        }
    else:
        mock_manifest.modules = None
    return mock_manifest


def build_mock_project_config() -> Dict[str, Any]:
    project_config = {
        "modules": [{"name": f"module {i}", "prefix": f"path/to/{i}"} for i in range(4)]
    }
    return project_config


@pytest.fixture()
def file_service():
    file_service = MagicMock(spec_set=FileService)
    file_service.read_yaml_file.return_value = build_mock_project_config()
    return file_service


@pytest.fixture()
def evergreen_api():
    mock_evg_api = MagicMock(spec_set=EvergreenApi)
    project_list = [build_mock_project(i) for i in range(10)]
    mock_evg_api.all_projects = lambda project_filter_fn: [
        p for p in project_list if project_filter_fn(p)
    ]
    return mock_evg_api


@pytest.fixture()
def evg_service(evergreen_api, file_service):
    evg_service = under_test.EvergreenService(evergreen_api, file_service)
    return evg_service


def mock_project_config(service, project_config):
    service.file_service.read_yaml_file.return_value = project_config


def mock_task_list_for_build(service, task_list: Dict[str, List[Task]]):
    mock_build_map = {b: build_mock_build(b, tl) for b, tl in task_list.items()}
    service.evg_api.build_by_id = lambda b: mock_build_map.get(b)


def mock_evg_manifest(service, manifest):
    service.evg_api.manifest.return_value = manifest


def set_build_variant_predicate(service, predicate):
    service.bv_predicate = predicate


class TestAnalyzeBuild:
    def test_build_with_all_tasks_run(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.SUCCESS) for i in range(n_tasks)]
        mock_task_list_for_build(evg_service, {"my build": mock_task_list})

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {task.display_name for task in mock_task_list}
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_no_tasks_run(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.INACTIVE) for i in range(n_tasks)]
        mock_task_list_for_build(evg_service, {"my build": mock_task_list})

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == set()
        assert build_status.inactive_tasks == {task.display_name for task in mock_task_list}
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_all_failed_tasks(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.FAILED) for i in range(n_tasks)]
        mock_task_list_for_build(evg_service, {"my build": mock_task_list})

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == set()
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_a_mix_of_status(self, evg_service):
        n_tasks = 9
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus(i % 3)) for i in range(n_tasks)]
        mock_task_list_for_build(evg_service, {"my build": mock_task_list})

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {"task_0", "task_3", "task_6"}
        assert build_status.inactive_tasks == {"task_2", "task_5", "task_8"}
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}


class TestGetBuildStatusesForVersion:
    def test_all_builds_meet_predicate(self, evg_service):
        n_builds = 5
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        build_checks = [BuildChecks(build_variant_regex=["^build"])]
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert len(build_status_list) == n_builds

    def test_no_builds_meet_predicate(self, evg_service):
        n_builds = 5
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        build_checks = [BuildChecks(build_variant_regex=["^hello_world"])]
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert len(build_status_list) == 0

    def test_some_builds_meet_predicate(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        build_checks = [BuildChecks(build_variant_regex=["^build_1"])]
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert len(build_status_list) == 11


class TestCheckVersion:
    def test_no_build_meet_checks(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.INACTIVE) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        build_checks = BuildChecks(build_variant_regex=[".*"], run_threshold=0.9)

        result = evg_service.check_version(mock_version, [build_checks])

        assert not result

    def test_all_build_meet_checks(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        build_checks = BuildChecks(build_variant_regex=[".*"], run_threshold=0.9)

        result = evg_service.check_version(mock_version, [build_checks])

        assert result

    def test_some_build_meet_checks(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus(i % 3)) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        build_checks = BuildChecks(build_variant_regex=[".*"], run_threshold=0.9)

        result = evg_service.check_version(mock_version, [build_checks])

        assert not result

    def test_some_build_meet_checks_but_are_filtered_out(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus(i % 3)) for j in range(10)]
            for i in range(n_builds)
        }
        mock_task_list_for_build(evg_service, mock_build_map)
        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        build_checks = BuildChecks(build_variant_regex=["^build_0$"], run_threshold=0.9)

        result = evg_service.check_version(mock_version, [build_checks])

        assert result


class TestGetModulesRevisions:
    def test_empty_modules_returned(self, evg_service):
        modules = {}
        mock_evg_manifest(evg_service, build_mock_manifest(modules))

        assert modules == evg_service.get_modules_revisions("project id", "gitrevision")

    def test_no_modules_returned(self, evg_service):
        modules = None
        mock_evg_manifest(evg_service, build_mock_manifest(modules))

        assert {} == evg_service.get_modules_revisions("project id", "gitrevision")

    def test_multiple_modules_returned(self, evg_service):
        modules = {
            "module 1": "abc123",
            "module 2": "def456",
        }
        mock_evg_manifest(evg_service, build_mock_manifest(modules))

        assert modules == evg_service.get_modules_revisions("project id", "gitrevision")

    def test_manifest_endpoint_returns_404(self, evg_service):
        http_response = MagicMock(status_code=404)

        evg_service.evg_api.manifest.side_effect = HTTPError(response=http_response)

        assert {} == evg_service.get_modules_revisions("project id", "gitrevision")


class TestGetProjectConfigLocation:
    def test_remote_path_is_returned(self, evg_service):
        assert "remote/path/3" == evg_service.get_project_config_location("project 3")

    def test_missing_project_should_throw_exception(self, evg_service):
        with pytest.raises(ValueError) as exp:
            evg_service.get_project_config_location("non-existing-project")
            assert "non-existing-project" in exp.value

    def test_more_than_one_matching_project_should_throw_exception(self, evg_service):
        project_list = [build_mock_project(5) for _ in range(10)]
        evg_service.evg_api.all_projects = lambda project_filter_fn: [
            p for p in project_list if project_filter_fn(p)
        ]

        with pytest.raises(ValueError) as exp:
            evg_service.get_project_config_location("project_5")
            assert "project_5" in exp.value


class TestGetModuleLocations:
    def test_module_locations_should_be_returned(self, evg_service):
        project_locations = evg_service.get_module_locations("project 2")

        assert project_locations == {f"module {i}": f"path/to/{i}" for i in range(4)}

    def test_module_locations__with_no_modules_in_project_should_be_empty(self, evg_service):
        mock_project_config(evg_service, {})
        project_locations = evg_service.get_module_locations("project 2")

        assert project_locations == {}
