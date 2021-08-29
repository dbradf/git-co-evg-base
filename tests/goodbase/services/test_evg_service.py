"""Unit tests for evg_service.py."""
from enum import Enum
from typing import Dict, List
from unittest.mock import MagicMock

from evergreen import Build, EvergreenApi, Task, Version

import goodbase.services.evg_service as under_test
from goodbase.build_checker import BuildChecks


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
    mock_build = MagicMock(spec_set=Build, display_name=name)
    mock_build.get_tasks.return_value = task_list
    return mock_build


def build_mock_version(build_names: List[str]) -> Version:
    mock_version = MagicMock(spec=Version)
    mock_version.build_variants_map = {build_name: build_name for build_name in build_names}
    return mock_version


def build_mock_evg_api(task_list_for_build: Dict[str, List[Task]]) -> EvergreenApi:
    mock_build_map = {b: build_mock_build(b, tl) for b, tl in task_list_for_build.items()}
    mock_evg_api = MagicMock(spec_set=EvergreenApi)
    mock_evg_api.build_by_id = lambda b: mock_build_map.get(b)
    return mock_evg_api


class TestAnalyzeBuild:
    def test_build_with_all_tasks_run(self):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.SUCCESS) for i in range(n_tasks)]
        mock_evg_api = build_mock_evg_api({"my build": mock_task_list})
        evg_service = under_test.EvergreenService(mock_evg_api, lambda _: True)

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {task.display_name for task in mock_task_list}
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_no_tasks_run(self):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.INACTIVE) for i in range(n_tasks)]
        mock_evg_api = build_mock_evg_api({"my build": mock_task_list})
        evg_service = under_test.EvergreenService(mock_evg_api, lambda _: True)

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == set()
        assert build_status.inactive_tasks == {task.display_name for task in mock_task_list}
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_all_failed_tasks(self):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.FAILED) for i in range(n_tasks)]
        mock_evg_api = build_mock_evg_api({"my build": mock_task_list})
        evg_service = under_test.EvergreenService(mock_evg_api, lambda _: True)

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == set()
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_a_mix_of_status(self):
        n_tasks = 9
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus(i % 3)) for i in range(n_tasks)]
        mock_evg_api = build_mock_evg_api({"my build": mock_task_list})
        evg_service = under_test.EvergreenService(mock_evg_api, lambda _: True)

        build_status = evg_service.analyze_build("my build")

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {"task_0", "task_3", "task_6"}
        assert build_status.inactive_tasks == {"task_2", "task_5", "task_8"}
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}


class TestGetBuildStatusesForVersion:
    def test_all_builds_meet_predicate(self):
        n_builds = 5
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(b):
            return b.startswith("build")

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)

        build_status_list = evg_service.get_build_statuses_for_version(mock_version)

        assert len(build_status_list) == n_builds

    def test_no_builds_meet_predicate(self):
        n_builds = 5
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(b):
            return b.startswith("hello_world")

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)

        build_status_list = evg_service.get_build_statuses_for_version(mock_version)

        assert len(build_status_list) == 0

    def test_some_builds_meet_predicate(self):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(b):
            return b.startswith("build_1")

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)

        build_status_list = evg_service.get_build_statuses_for_version(mock_version)

        assert len(build_status_list) == 11


class TestCheckVersion:
    def test_no_build_meet_checks(self):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.INACTIVE) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(_):
            return True

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)
        build_checks = BuildChecks(run_threshold=0.9)

        result = evg_service.check_version(mock_version, build_checks)

        assert not result

    def test_all_build_meet_checks(self):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(_):
            return True

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)
        build_checks = BuildChecks(run_threshold=0.9)

        result = evg_service.check_version(mock_version, build_checks)

        assert result

    def test_some_build_meet_checks(self):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus(i % 3)) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(_):
            return True

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)
        build_checks = BuildChecks(run_threshold=0.9)

        result = evg_service.check_version(mock_version, build_checks)

        assert not result

    def test_some_build_meet_checks_but_are_filtered_out(self):
        n_builds = 20
        mock_build_map = {
            f"build_{i}": [build_mock_task(f"task_{j}", TaskStatus(i % 3)) for j in range(10)]
            for i in range(n_builds)
        }
        mock_evg_api = build_mock_evg_api(mock_build_map)

        def mock_predicate(b):
            return b == "build_0"

        mock_version = build_mock_version([build_name for build_name in mock_build_map.keys()])
        evg_service = under_test.EvergreenService(mock_evg_api, mock_predicate)
        build_checks = BuildChecks(run_threshold=0.9)

        result = evg_service.check_version(mock_version, build_checks)

        assert result
