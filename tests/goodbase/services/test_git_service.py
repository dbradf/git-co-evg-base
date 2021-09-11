"""Unit tests for git_service.py."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import goodbase.services.git_service as under_test


@pytest.fixture()
def mock_git():
    git_mock = MagicMock()
    git_mock.assert_git_call = lambda args: git_mock.__getitem__.assert_any_call(args)
    return git_mock


@pytest.fixture()
def evg_service(mock_git):
    git_service = under_test.GitService()
    git_service.git = mock_git
    return git_service


class TestPerformAction:
    def test_none_action_should_not_perform_any_actions(self, evg_service, mock_git):
        evg_service.perform_action(under_test.GitAction.NONE, "revision1234")

        mock_git.__getitem__.assert_not_called()

    def test_checkout_action_should_call_git_checkout(self, evg_service, mock_git):
        revision = "revision123"
        evg_service.perform_action(under_test.GitAction.CHECKOUT, revision)

        mock_git.assert_git_call(("fetch", "origin"))
        mock_git.assert_git_call(("checkout", revision))

    def test_rebase_action_should_call_git_rebase(self, evg_service, mock_git):
        revision = "revision123"
        evg_service.perform_action(under_test.GitAction.REBASE, revision)

        mock_git.assert_git_call(("fetch", "origin"))
        mock_git.assert_git_call(("rebase", revision))

    def test_merge_action_should_call_git_merge(self, evg_service, mock_git):
        revision = "revision123"
        evg_service.perform_action(under_test.GitAction.MERGE, revision)

        mock_git.assert_git_call(("fetch", "origin"))
        mock_git.assert_git_call(("merge", revision))


class TestDetermineDirectory:
    def test_no_directory_should_return_cwd(self):
        assert Path.cwd() == under_test.GitService._determine_directory()

    def test_absolute_directory_should_return_self(self):
        directory = Path("/path/to/directory")

        assert directory == under_test.GitService._determine_directory(directory)

    def test_relative_directory_should_return_absolute_directory(self):
        directory = Path("path/to/directory")

        assert Path.cwd() / directory == under_test.GitService._determine_directory(directory)
