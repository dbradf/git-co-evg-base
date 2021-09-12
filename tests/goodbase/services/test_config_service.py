"""Unit tests for config_service.py."""
from unittest.mock import MagicMock

import pytest

import goodbase.services.config_service as under_test
from goodbase.build_checker import BuildChecks
from goodbase.services.file_service import FileService


@pytest.fixture()
def file_service():
    file_service = MagicMock(spec_set=FileService)
    return file_service


@pytest.fixture()
def configuration_service(file_service):
    configuration_service = under_test.ConfigurationService(file_service)
    return configuration_service


class TestAddBuildChecks:
    def test_adding_to_empty_rules_should_add_check(self):
        group = under_test.CriteriaGroup(name="my group", rules=[])
        build_check = BuildChecks(
            build_variant_regex=[".*"],
            success_threshold=0.95,
        )

        group.add_build_checks(build_check)

        assert len(group.rules) == 1
        assert group.rules[0] == build_check

    def test_adding_with_existing_rules_should_add_check(self):
        group = under_test.CriteriaGroup(
            name="my group",
            rules=[
                BuildChecks(
                    build_variant_regex=[".*-required"],
                    run_threshold=0.85,
                ),
                BuildChecks(
                    build_variant_regex=[".*-suggested"],
                    active_tasks={"compile_dist_test"},
                ),
            ],
        )
        build_check = BuildChecks(
            build_variant_regex=[".*"],
            success_threshold=0.95,
        )

        group.add_build_checks(build_check)

        assert len(group.rules) == 3
        assert build_check in group.rules

    def test_adding_conflicting_rules_should_raise_exception(self):
        group = under_test.CriteriaGroup(
            name="my group",
            rules=[
                BuildChecks(
                    build_variant_regex=[".*-required"],
                    run_threshold=0.85,
                ),
                BuildChecks(
                    build_variant_regex=[".*"],
                    active_tasks={"compile_dist_test"},
                ),
            ],
        )
        build_check = BuildChecks(
            build_variant_regex=[".*"],
            success_threshold=0.95,
        )

        with pytest.raises(ValueError):
            group.add_build_checks(build_check)

    def test_adding_conflicting_rules_can_be_overridden(self):
        group = under_test.CriteriaGroup(
            name="my group",
            rules=[
                BuildChecks(
                    build_variant_regex=[".*-required"],
                    run_threshold=0.85,
                ),
                BuildChecks(
                    build_variant_regex=[".*"],
                    active_tasks={"compile_dist_test"},
                ),
            ],
        )
        build_check = BuildChecks(
            build_variant_regex=[".*"],
            success_threshold=0.95,
        )

        group.add_build_checks(build_check, override=True)

        assert len(group.rules) == 2
        assert build_check in group.rules


class TestGetCriteriaGroup:
    def test_get_a_non_existing_group_should_create_new_group(self):
        config = under_test.CriteriaConfiguration.new()

        group = config.get_criteria_group("new group")

        assert group.name == "new group"
        assert group.rules == []

    def test_get_a_non_existing_group_with_other_groups_should_create_new_group(self):
        existing_group = under_test.CriteriaGroup(
            name="existing group",
            rules=[
                BuildChecks(
                    build_variant_regex=[".*-required"],
                    run_threshold=0.85,
                ),
                BuildChecks(
                    build_variant_regex=[".*"],
                    active_tasks={"compile_dist_test"},
                ),
            ],
        )
        config = under_test.CriteriaConfiguration(saved_criteria=[existing_group])

        group = config.get_criteria_group("new group")

        assert group.name == "new group"
        assert group.rules == []

    def test_get_an_existing_group_should_return_that_group(self):
        existing_group = under_test.CriteriaGroup(
            name="existing group",
            rules=[
                BuildChecks(
                    build_variant_regex=[".*-required"],
                    run_threshold=0.85,
                ),
                BuildChecks(
                    build_variant_regex=[".*"],
                    active_tasks={"compile_dist_test"},
                ),
            ],
        )
        config = under_test.CriteriaConfiguration(saved_criteria=[existing_group])

        group = config.get_criteria_group("existing group")

        assert group == existing_group


class TestAddCriteria:
    def test_adding_new_criteria_should_be_added(self):
        config = under_test.CriteriaConfiguration.new()
        build_checks = BuildChecks(
            build_variant_regex=[".*"],
            run_threshold=0.9,
        )

        config.add_criteria("my criteria", build_checks)

        assert len(config.saved_criteria) == 1
        assert "my criteria" == config.saved_criteria[0].name
        assert build_checks in config.saved_criteria[0].rules

    def test_adding_to_existing_criteria_should_be_added(self):
        config = under_test.CriteriaConfiguration(
            saved_criteria=[
                under_test.CriteriaGroup(
                    name="my criteria",
                    rules=[
                        BuildChecks(
                            build_variant_regex=[".*-required"],
                            success_threshold=0.85,
                        ),
                    ],
                )
            ]
        )
        build_checks = BuildChecks(
            build_variant_regex=[".*"],
            run_threshold=0.9,
        )

        config.add_criteria("my criteria", build_checks)

        assert len(config.saved_criteria) == 1
        assert "my criteria" == config.saved_criteria[0].name
        assert build_checks in config.saved_criteria[0].rules
        assert len(config.saved_criteria[0].rules) == 2

    def test_adding_conflicting_criteria_should_raise_exception(self):
        config = under_test.CriteriaConfiguration(
            saved_criteria=[
                under_test.CriteriaGroup(
                    name="my criteria",
                    rules=[
                        BuildChecks(
                            build_variant_regex=[".*-required"],
                            success_threshold=0.85,
                        ),
                    ],
                )
            ]
        )
        build_checks = BuildChecks(
            build_variant_regex=[".*-required"],
            run_threshold=0.9,
        )

        with pytest.raises(ValueError):
            config.add_criteria("my criteria", build_checks)

            assert len(config.saved_criteria) == 1
            assert "my criteria" == config.saved_criteria[0].name
            assert build_checks not in config.saved_criteria[0].rules
            assert len(config.saved_criteria[0].rules) == 1

    def test_adding_conflicting_criteria_can_be_overridden(self):
        config = under_test.CriteriaConfiguration(
            saved_criteria=[
                under_test.CriteriaGroup(
                    name="my criteria",
                    rules=[
                        BuildChecks(
                            build_variant_regex=[".*-required"],
                            success_threshold=0.85,
                        ),
                    ],
                )
            ]
        )
        build_checks = BuildChecks(
            build_variant_regex=[".*-required"],
            run_threshold=0.9,
        )

        config.add_criteria("my criteria", build_checks, override=True)

        assert len(config.saved_criteria) == 1
        assert "my criteria" == config.saved_criteria[0].name
        assert build_checks in config.saved_criteria[0].rules
        assert len(config.saved_criteria[0].rules) == 1


class TestGetConfig:
    def test_non_existing_config_create_new(self, configuration_service, file_service):
        file_service.path_exists.return_value = False

        config = configuration_service.get_config()

        assert len(config.saved_criteria) == 0

    def test_existing_config_should_return_config_contents(
        self, configuration_service, file_service
    ):
        existing_config = under_test.CriteriaConfiguration(
            saved_criteria=[
                under_test.CriteriaGroup(
                    name="my criteria",
                    rules=[
                        BuildChecks(
                            build_variant_regex=[".*-required"],
                            success_threshold=0.85,
                        ),
                    ],
                )
            ]
        )
        file_service.path_exists.return_value = True
        file_service.read_yaml_file.return_value = existing_config.dict(exclude_none=True)

        config = configuration_service.get_config()

        assert config == existing_config
