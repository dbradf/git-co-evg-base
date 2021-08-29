"""Service to interact with evergreen."""
from concurrent.futures import ThreadPoolExecutor as Executor
from typing import Callable, List

import inject
from evergreen import EvergreenApi, Version

from goodbase.build_checker import BuildChecks
from goodbase.models.build_status import BuildStatus

N_THREADS = 16

BuildVariantPredicate = Callable[[str], bool]


class EvergreenService:
    """A service to interact with Evergreen."""

    @inject.autoparams()
    def __init__(self, evg_api: EvergreenApi, bv_predicate: BuildVariantPredicate) -> None:
        """
        Initialize the service.

        :param evg_api: Evergreen API client.
        :param bv_predicate: Predicate to check with build variants to check.
        """
        self.evg_api = evg_api
        self.bv_predicate = bv_predicate

    def analyze_build(self, build_id: str) -> BuildStatus:
        """
        Get a summary of results for the given build.

        :param build_id: ID of build to analyze.
        :return: Summary of build.
        """
        build = self.evg_api.build_by_id(build_id)
        tasks = build.get_tasks()
        successful_tasks = {task.display_name for task in tasks if task.is_success()}
        inactive_tasks = {task.display_name for task in tasks if task.is_undispatched()}
        all_tasks = {task.display_name for task in tasks}

        return BuildStatus(
            build_name=build.display_name,
            successful_tasks=successful_tasks,
            inactive_tasks=inactive_tasks,
            all_tasks=all_tasks,
        )

    def check_version(self, evg_version: Version, build_checks: BuildChecks) -> bool:
        """
        Check if the given version meets the specified criteria.

        :param evg_version: Evergreen version to check.
        :param build_checks: Build criteria to use.
        :return: True if the version matches the specified criteria.
        """
        build_status_list = self.get_build_statuses_for_version(evg_version)
        return all(build_checks.check(bs) for bs in build_status_list)

    def get_build_statuses_for_version(self, evg_version: Version) -> List[BuildStatus]:
        """
        Get the build status for this version that match the predicate.

        :param evg_version: Evergreen version to check.
        :return: List of build statuses.
        """
        with Executor(max_workers=N_THREADS) as exe:
            jobs = [
                exe.submit(self.analyze_build, build_id)
                for bv, build_id in evg_version.build_variants_map.items()
                if self.bv_predicate(bv)
            ]

        return [j.result() for j in jobs]
