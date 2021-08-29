"""Model for evergreen build status."""
from dataclasses import dataclass
from typing import Set


@dataclass
class BuildStatus:
    """
    A summary of the results of an evergreen build.

    build_name: Name of build results are for.
    successful_task: Set of tasks that were successful.
    inactive_tasks: Set of tasks that have not be run.
    all_tasks: Set of all tasks in the build.
    """

    build_name: str
    successful_tasks: Set[str]
    inactive_tasks: Set[str]
    all_tasks: Set[str]

    def success_pct(self) -> float:
        """Percentage of tasks that were successful."""
        return len(self.successful_tasks) / len(self.all_tasks)

    def active_pct(self) -> float:
        """Percent of tasks that were activated."""
        return 1.0 - len(self.inactive_tasks) / len(self.all_tasks)
