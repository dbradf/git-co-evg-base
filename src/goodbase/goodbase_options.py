"""Options for running goodbase."""
from enum import Enum
from typing import NamedTuple, Optional

import structlog

from goodbase.services.git_service import GitAction

LOGGER = structlog.get_logger(__name__)


class OutputFormat(str, Enum):
    """Format to display output in."""

    PLAINTEXT = "plaintext"
    YAML = "yaml"
    JSON = "json"


class GoodBaseOptions(NamedTuple):
    """
    Options for execution.

    * max_lookback: Number of commits to scan before giving up.
    * commit_limit: Oldest commit to look at before giving up.
    * operation: Type of git operation to perform.
    * override_criteria: Override conflicting save criteria.
    * timeouts_secs: Number of seconds to scan before timing out.
    * branch_name: Name of branch to create on checkout.
    * output_format: Format to display output in.
    """

    max_lookback: int
    commit_limit: Optional[str]
    operation: GitAction
    override_criteria: bool
    timeout_secs: Optional[int] = None
    branch_name: Optional[str] = None
    output_format: OutputFormat = OutputFormat.PLAINTEXT

    def lookback_limit_hit(self, index: int, revision: str, elapsed_seconds: float) -> bool:
        """
        Determine if the limits of looking back have been hit.

        :param index: Index of version being checked.
        :param revision: git revision being checked.
        :param elapsed_seconds: Number of seconds that have passed since operation started.
        :return: True if we have hit the limit of version of check.
        """
        if index > self.max_lookback:
            LOGGER.debug("Max lookback hit", max_lookback=self.max_lookback, commit_idx=index)
            return True

        if self.commit_limit and revision.startswith(self.commit_limit):
            LOGGER.debug("Commit limit hit", commit_limit=self.commit_limit)
            return True

        if self.timeout_secs and elapsed_seconds > self.timeout_secs:
            LOGGER.debug(
                "Timeout hit",
                timeout_secs=self.timeout_secs,
                elapsed_seconds=elapsed_seconds,
            )
            return True

        return False
