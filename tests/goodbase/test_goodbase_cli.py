"""Unit tests for goodbase_cli.py."""
import pytest

import goodbase.goodbase_cli as under_test
from goodbase.services.git_service import GitAction


class TestLookbackLimitHit:
    @pytest.mark.parametrize(
        "max_lookback,commit_limit,timeout_secs,index,revision,seconds",
        [
            (50, None, None, 15, "abc123", 3),
            (50, "def1234", None, 15, "abc123", 3),
            (50, None, 60, 15, "abc123", 3),
        ],
    )
    def test_lookback_limit_not_hit(
        self, max_lookback, commit_limit, timeout_secs, index, revision, seconds
    ):
        options = under_test.GoodBaseOptions(
            max_lookback=max_lookback,
            commit_limit=commit_limit,
            operation=GitAction.NONE,
            override_criteria=False,
            timeout_secs=timeout_secs,
            branch_name=None,
        )

        assert not options.lookback_limit_hit(index, revision, seconds)

    @pytest.mark.parametrize(
        "max_lookback,commit_limit,timeout_secs,index,revision,seconds",
        [
            (50, None, None, 51, "abc123", 3),
            (50, "def1234", None, 15, "def1234", 3),
            (50, None, 60, 15, "abc123", 61),
        ],
    )
    def test_lookback_limit_hit(
        self, max_lookback, commit_limit, timeout_secs, index, revision, seconds
    ):
        options = under_test.GoodBaseOptions(
            max_lookback=max_lookback,
            commit_limit=commit_limit,
            operation=GitAction.NONE,
            override_criteria=False,
            timeout_secs=timeout_secs,
            branch_name=None,
        )

        assert options.lookback_limit_hit(index, revision, seconds)
