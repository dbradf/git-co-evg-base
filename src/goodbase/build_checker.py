"""Criteria for checking an evergreen build."""
from dataclasses import dataclass
from typing import Optional, Set

import structlog

from goodbase.models.build_status import BuildStatus

LOGGER = structlog.get_logger(__name__)


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
            LOGGER.debug(
                "Unmet criteria, success_threshold",
                build=build_status.build_name,
                expected_success=self.success_threshold,
                actual_success=build_status.success_pct(),
            )
            return False

        if self.run_threshold and build_status.active_pct() < self.run_threshold:
            LOGGER.debug(
                "Unmet criteria, run_threshold",
                build=build_status.build_name,
                expected_run=self.success_threshold,
                actual_run=build_status.success_pct(),
            )
            return False

        if self.successful_tasks:
            if any(
                task in build_status.all_tasks and task not in build_status.successful_tasks
                for task in self.successful_tasks
            ):
                LOGGER.debug(
                    "Unmet criteria, successful_tasks",
                    build=build_status.build_name,
                    expected_tasks=self.successful_tasks,
                )
                return False

        if self.active_tasks:
            if any(
                task in build_status.all_tasks and task in build_status.inactive_tasks
                for task in self.active_tasks
            ):
                LOGGER.debug(
                    "Unmet criteria, active_tasks",
                    build=build_status.build_name,
                    expected_tasks=self.active_tasks,
                )
                return False

        return True
