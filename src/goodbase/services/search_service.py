"""A service to search for revisions."""
from time import perf_counter
from typing import Iterable, List, Optional

import click
import inject
import structlog
from evergreen import EvergreenApi, Version

from goodbase.build_checker import BuildChecks
from goodbase.goodbase_options import GoodBaseOptions, OutputFormat
from goodbase.services.evg_service import EvergreenService

LOGGER = structlog.get_logger(__name__)


class SearchService:
    """A service to search for revisions."""

    @inject.autoparams()
    def __init__(
        self, evg_api: EvergreenApi, evg_service: EvergreenService, options: GoodBaseOptions
    ) -> None:
        """
        Initialize the service.

        :param evg_api: Client to query evergreen API.
        :param evg_service: Service to work with evergreen.
        :param options: Good Base options for execution.
        """
        self.evg_api = evg_api
        self.evg_service = evg_service
        self.options = options

    def find_revision(self, evg_project: str, build_checks: List[BuildChecks]) -> Optional[str]:
        """
        Iterate through revisions until one is found that matches the given criteria.

        :param evg_project: Evergreen project to check.
        :param build_checks: Criteria to enforce.
        :return: First git revision to match the given criteria if it exists.
        """
        versions = self.evg_api.versions_by_project(evg_project)

        if self.options.output_format in {OutputFormat.YAML, OutputFormat.JSON}:
            stable_revision = self._find_stable_revision(versions, build_checks)
        else:  # plaintext: show progress bar
            with click.progressbar(
                versions,
                length=self.options.max_lookback,
                label=f"Searching {evg_project} revisions",
            ) as bar:
                stable_revision = self._find_stable_revision(bar, build_checks)

        return stable_revision

    def _find_stable_revision(
        self, evg_versions: Iterable[Version], build_checks: List[BuildChecks]
    ) -> Optional[str]:
        """
        Find the latest revision that matches the specified criteria.

        :param evg_versions: Evergreen versions to iterate over.
        :param build_checks: Criteria to enforce.
        :return: First git revision to match the given criteria if it exists.
        """
        start_time = perf_counter()
        for idx, evg_version in enumerate(evg_versions):
            current_time = perf_counter()
            elapsed_time = current_time - start_time
            if self.options.lookback_limit_hit(idx, evg_version.revision, elapsed_time):
                return None

            LOGGER.debug("Checking version", commit=evg_version.revision)

            if self.evg_service.check_version(evg_version, build_checks):
                return evg_version.revision

        return None
