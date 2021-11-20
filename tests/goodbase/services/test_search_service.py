"""Unit tests for search_service.py."""
from unittest.mock import MagicMock

import pytest
from click._termui_impl import ProgressBar
from evergreen import EvergreenApi, Version

import goodbase.services.search_service as under_test
from goodbase.build_checker import BuildChecks
from goodbase.goodbase_options import OutputFormat
from goodbase.services.evg_service import EvergreenService
from goodbase.services.git_service import GitAction


@pytest.fixture()
def evg_api():
    mock_evg_api = MagicMock(spec_set=EvergreenApi)
    return mock_evg_api


@pytest.fixture()
def evg_service():
    mock_evg_service = MagicMock(spec_set=EvergreenService)
    return mock_evg_service


@pytest.fixture()
def options():
    mock_options = MagicMock(
        max_lookback=20,
        commit_limit=None,
        operation=GitAction.NONE,
        override_criteria=False,
        timeout_secs=None,
        branch_name=None,
        output_format=OutputFormat.PLAINTEXT,
    )
    mock_options.lookback_limit_hit.return_value = False
    return mock_options


@pytest.fixture()
def search_service(evg_api, evg_service, options):
    service = under_test.SearchService(evg_api, evg_service, options)
    return service


class TestFindRevision:
    def test_find_revision_should_use_progressbar_for_plaintext(self, search_service):
        def assert_progress_bar(bar, _checks):
            assert isinstance(bar, ProgressBar)

        search_service._find_stable_revision = assert_progress_bar

        search_service.find_revision("project", [])

    @pytest.mark.parametrize("format", [OutputFormat.YAML, OutputFormat.JSON])
    def test_find_revision_should_not_use_progressbar_for_non_plaintest(
        self, format, search_service, options
    ):
        def assert_no_progress_bar(bar, _checks):
            assert not isinstance(bar, ProgressBar)

        options.output_format = format
        search_service._find_stable_revision = assert_no_progress_bar

        search_service.find_revision("project", [])


class TestFindStableRevision:
    def test_a_good_revision_should_be_returned(self, search_service, evg_service):
        version_list = [MagicMock(spec=Version, revision=f"abc_{i}") for i in range(20)]
        checks = [MagicMock(spec=BuildChecks)]
        evg_service.check_version.side_effect = [False, False, False, True, True, False]

        revision = search_service._find_stable_revision(version_list, checks)

        assert version_list[3].revision == revision
        evg_service.check_version.assert_any_call(version_list[0], checks)

    def test_no_good_revision_should_be_return_none(self, search_service, evg_service):
        version_list = [MagicMock(spec=Version, revision=f"abc_{i}") for i in range(20)]
        checks = [MagicMock(spec=BuildChecks)]
        evg_service.check_version.return_value = False

        revision = search_service._find_stable_revision(version_list, checks)

        assert revision is None
        evg_service.check_version.assert_any_call(version_list[0], checks)

    def test_no_good_revision_before_limit_should_be_return_none(
        self, search_service, evg_service, options
    ):
        version_list = [MagicMock(spec=Version, revision=f"abc_{i}") for i in range(20)]
        checks = [MagicMock(spec=BuildChecks)]
        evg_service.check_version.side_effect = [False, False, False, True, True, False]
        options.lookback_limit_hit.side_effect = [False, False, True]

        revision = search_service._find_stable_revision(version_list, checks)

        assert revision is None
        evg_service.check_version.assert_any_call(version_list[0], checks)
