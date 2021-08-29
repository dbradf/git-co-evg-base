"""Criteria for checking an evergreen build."""
from dataclasses import dataclass
from typing import Optional, Set

from goodbase.models.build_status import BuildStatus


@dataclass
class BuildChecks:
    """
    Set of checks to perform to check build criteria.

    success_threshold: Percentage of tasks that need to pass to use the build.
    run_threshold: Percentage of tasks that need to have run to use the build.
    successful_tasks: Set of tasks that need to have passed to use the build.
    active_tasks: Set of tasks that need to have run to use the build.
    """

    success_threshold: Optional[float] = None
    run_threshold: Optional[float] = None
    successful_tasks: Optional[Set[str]] = None
    active_tasks: Optional[Set[str]] = None

    def check(self, build_status: BuildStatus) -> bool:
        """
        Check if the given build stats meet the specified criteria.

        :param build_status: Status of build to check.
        :return: True if the build matches the criteria.
        """
        if self.success_threshold and build_status.success_pct() < self.success_threshold:
            return False

        if self.run_threshold and build_status.active_pct() < self.run_threshold:
            return False

        if self.successful_tasks:
            if any(
                task not in build_status.successful_tasks and task in build_status.all_tasks
                for task in self.successful_tasks
            ):
                return False

        if self.active_tasks:
            if any(
                task in build_status.inactive_tasks and task in build_status.all_tasks
                for task in self.active_tasks
            ):
                return False

        return True
