"""Unit tests for criteria_service.py."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import goodbase.services.criteria_service as under_test
from goodbase.build_checker import BuildChecks
from goodbase.services.config_service import (
    ConfigurationService,
    CriteriaConfiguration,
    CriteriaGroup,
)
from goodbase.services.file_service import FileService
from goodbase.services.git_service import GitAction


@pytest.fixture()
def config_service():
    mock_config_service = MagicMock(spec_set=ConfigurationService)
    return mock_config_service


@pytest.fixture()
def file_service():
    mock_file_service = MagicMock(spec_set=FileService)
    return mock_file_service


@pytest.fixture()
def options():
    mock_options = MagicMock(
        max_lookback=20,
        commit_limit=None,
        operation=GitAction.NONE,
        override_criteria=False,
        timeout_secs=None,
        branch_name=None,
    )
    return mock_options


@pytest.fixture()
def criteria_service(config_service, file_service, options):
    return under_test.CriteriaService(config_service, file_service, options)


class TestSaveCriteria:
    def test_that_added_criteria_shoule_be_saved(self, criteria_service, config_service):
        criteria_name = "my criteria"
        build_checks = MagicMock()

        criteria_service.save_criteria(criteria_name, build_checks)

        configuration = config_service.get_config.return_value
        configuration.add_criteria.assert_called_with(criteria_name, build_checks, False)
        config_service.save_config.assert_called_with(configuration)

    def test_that_added_criteria_can_be_overridden(self, criteria_service, config_service, options):
        criteria_name = "my criteria"
        build_checks = MagicMock()
        options.override_criteria = True

        criteria_service.save_criteria(criteria_name, build_checks)

        configuration = config_service.get_config.return_value
        configuration.add_criteria.assert_called_with(criteria_name, build_checks, True)


class TestLookupCriteria:
    def test_criteria_in_configuration_should_be_returned(self, criteria_service, config_service):
        criteria_name = "my criteria"

        found_criteria = criteria_service.lookup_criteria(criteria_name)

        configuration = config_service.get_config.return_value
        configuration.get_criteria_group.assert_called_with(criteria_name)
        assert found_criteria == configuration.get_criteria_group.return_value.rules

    def test_unknown_criteria_should_raise_an_exception(self, criteria_service, config_service):
        criteria_name = "missing criteria"
        config_service.get_config.return_value.get_criteria_group.return_value.rules = []

        with pytest.raises(ValueError):
            criteria_service.lookup_criteria(criteria_name)


def build_mock_group(name):
    build_checks = [
        BuildChecks(build_variant_regex=["bv"], success_threshold=0.97),
        BuildChecks(build_variant_regex=["bv"], active_tasks={"task0", "task1"}),
    ]
    return CriteriaGroup(name=name, rules=build_checks)


def build_mock_config(count):
    groups = [build_mock_group(f"group_{i}") for i in range(count)]
    return CriteriaConfiguration(saved_criteria=groups)


class TestExportCriteria:
    def test_export_should_write_rules_to_specified_file(
        self, criteria_service, config_service, file_service
    ):
        config = build_mock_config(3)
        config_service.get_config.return_value = config
        expected_dest = Path("/path/to/dest")

        criteria_service.export_criteria(["group_0", "group_2"], expected_dest)

        expected_output = {
            "saved_criteria": [
                config.saved_criteria[0].dict(exclude_none=True),
                config.saved_criteria[2].dict(exclude_none=True),
            ]
        }
        file_service.write_yaml_file.assert_called_with(expected_dest, expected_output)


class TestImportCriteria:
    def test_import_criteria_should_add_new_criteria_to_config(
        self, criteria_service, config_service, file_service, options
    ):
        options.override_criteria = False
        criteria = [build_mock_group(f"criteria {i}") for i in range(2)]
        file_service.read_yaml_file.return_value = {
            "saved_criteria": [c.dict(exclude_none=True) for c in criteria]
        }
        expected_path = Path("/path/to/import")

        criteria_service.import_criteria(expected_path)

        config = config_service.get_config.return_value
        config_service.save_config.assert_called_with(config)
        file_service.read_yaml_file.assert_called_with(expected_path)
        for rule in criteria[0].rules:
            config.add_criteria.assert_any_call("criteria 0", rule, False)
        for rule in criteria[1].rules:
            config.add_criteria.assert_any_call("criteria 1", rule, False)

    def test_import_criteria_should_override_existing_criteria(
        self, criteria_service, config_service, file_service, options
    ):
        options.override_criteria = True
        criteria = [build_mock_group(f"criteria {i}") for i in range(2)]
        file_service.read_yaml_file.return_value = {
            "saved_criteria": [c.dict(exclude_none=True) for c in criteria]
        }
        expected_path = Path("/path/to/import")

        criteria_service.import_criteria(expected_path)

        config = config_service.get_config.return_value
        config_service.save_config.assert_called_with(config)
        file_service.read_yaml_file.assert_called_with(expected_path)
        for rule in criteria[0].rules:
            config.add_criteria.assert_any_call("criteria 0", rule, True)
        for rule in criteria[1].rules:
            config.add_criteria.assert_any_call("criteria 1", rule, True)


class TestGetAllCriteria:
    def test_get_all_criteria_should_return_all_criteria(self, criteria_service, config_service):
        n_groups = 3
        config = build_mock_config(n_groups)
        config_service.get_config.return_value = config

        groups = criteria_service.get_all_criteria()

        assert n_groups == len(groups)
        actual_names = [g.name for g in groups]
        for i in range(n_groups):
            assert f"group_{i}" in actual_names
