"""Command line entry point to application."""
import logging
import os.path
import sys
from pathlib import Path
from time import perf_counter
from typing import Dict, List, NamedTuple, Optional

import click
import inject
import structlog
from evergreen import EvergreenApi, RetryingEvergreenApi
from structlog.stdlib import LoggerFactory

from goodbase.build_checker import BuildChecks
from goodbase.services.evg_service import BuildVariantPredicate, EvergreenService
from goodbase.services.git_service import GitService

LOGGER = structlog.get_logger(__name__)

DEFAULT_EVG_CONFIG = os.path.expanduser("~/.evergreen.yml")
DEFAULT_EVG_PROJECT = "mongodb-mongo-master"
DEFAULT_EVG_PROJECT_CONFIG = "etc/evergreen.yml"
MAX_LOOKBACK = 50
DEFAULT_THRESHOLD = 0.95
EXTERNAL_LOGGERS = [
    "evergreen",
    "inject",
    "urllib3",
]


class GoodBaseOptions(NamedTuple):
    """
    Options for execution.

    * perform_checkout: Run git checkout on the found commit.
    * max_lookback: Number of commits to scan before giving up.
    * timeouts_secs: Number of seconds to scan before timing out.
    """

    perform_checkout: bool
    max_lookback: int
    timeout_secs: Optional[int] = None


class RevisionInformation(NamedTuple):
    """
    Details about what revision(s) were found.

    revision: Revision of base project.
    module_revisions: Revisions of any modules associated with the project.
    """

    revision: str
    module_revisions: Dict[str, str]


class GoodBaseOrchestrator:
    """Orchestrator for checking base commits."""

    @inject.autoparams()
    def __init__(
        self,
        evg_api: EvergreenApi,
        evg_service: EvergreenService,
        git_service: GitService,
        options: GoodBaseOptions,
    ) -> None:
        """
        Initialize the orchestrator.

        :param evg_api: Evergreen API Client.
        :param evg_service:  Evergreen Service.
        :param git_service: Git Service.
        :param options: Options for execution.
        """
        self.evg_api = evg_api
        self.evg_service = evg_service
        self.git_service = git_service
        self.options = options

    def find_revision(self, evg_project: str, build_checks: BuildChecks) -> Optional[str]:
        """
        Iterate through revisions until one is found that matches the given criteria.

        :param evg_project: Evergreen project to check.
        :param build_checks: Criteria to enforce.
        :return: First git revision to match the given criteria if it exists.
        """
        start_time = perf_counter()
        with click.progressbar(
            self.evg_api.versions_by_project(evg_project),
            length=self.options.max_lookback,
            label=f"Searching {evg_project} revisions",
        ) as bar:
            for idx, evg_version in enumerate(bar):
                if idx > self.options.max_lookback:
                    LOGGER.debug(
                        "Max lookback hit", max_lookback=self.options.max_lookback, commit_idx=idx
                    )
                    return None

                LOGGER.debug("Checking version", commit=evg_version.revision)

                if self.evg_service.check_version(evg_version, build_checks):
                    return evg_version.revision

                current_time = perf_counter()
                elapsed_time = current_time - start_time
                if self.options.timeout_secs and elapsed_time > self.options.timeout_secs:
                    LOGGER.debug(
                        "Timeout hit",
                        timeout_secs=self.options.timeout_secs,
                        elapsed_time=elapsed_time,
                    )
                    return None

        return None

    def checkout_modules(self, evg_project: str, module_revisions: Dict[str, str]) -> None:
        """
        Checkout existing modules to the specified revisions.

        :param evg_project: Evergreen project of modules.
        :param module_revisions: Dictionary of module names and git revisions to check out.
        """
        module_locations = self.evg_service.get_module_locations(evg_project)
        LOGGER.debug(
            "Checking out modules",
            module_locations=module_locations,
            module_revisions=module_revisions,
        )
        for module, module_rev in module_revisions.items():
            directory = Path(module_locations[module]) / module
            if directory.exists():
                self.git_service.fetch_and_checkout(module_rev, directory)

    def checkout_good_base(
        self, evg_project: str, build_checks: BuildChecks
    ) -> Optional[RevisionInformation]:
        """
        Find the latest git revision that matches the criteria and check it out in git.

        :param evg_project: Evergreen project to check.
        :param build_checks: Criteria to enforce.
        :return: Revision that was checked out, if it exists.
        """
        revision = self.find_revision(evg_project, build_checks)
        if revision:
            module_revisions = self.evg_service.get_modules_revisions(evg_project, revision)
            if self.options.perform_checkout:
                self.git_service.fetch_and_checkout(revision)
                self.checkout_modules(evg_project, module_revisions)

            return RevisionInformation(revision=revision, module_revisions=module_revisions)
        return None


def configure_logging(verbose: bool) -> None:
    """
    Configure logging.

    :param verbose: Enable verbose logging.
    """
    structlog.configure(logger_factory=LoggerFactory())
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        format="[%(asctime)s - %(name)s - %(levelname)s] %(message)s",
        level=level,
        stream=sys.stderr,
    )
    for log_name in EXTERNAL_LOGGERS:
        logging.getLogger(log_name).setLevel(logging.WARNING)


@click.command(context_settings=dict(max_content_width=100))
@click.option(
    "--passing-task",
    type=str,
    multiple=True,
    help="Specify a task that needs to be passing (can be specified multiple times).",
)
@click.option(
    "--run-task",
    type=str,
    multiple=True,
    help="Specify a task that needs to be run (can be specified multiple times).",
)
@click.option(
    "--run-threshold", type=float, help="Specify the percentage of tasks that need to be run."
)
@click.option(
    "--pass-threshold",
    type=float,
    help="Specify the percentage of tasks that need to be successful.",
)
@click.option(
    "--evg-config-file",
    default=DEFAULT_EVG_CONFIG,
    type=click.Path(exists=True),
    help="File containing evergreen authentication information.",
)
@click.option(
    "--evg-project", default=DEFAULT_EVG_PROJECT, help="Evergreen project to query against."
)
@click.option(
    "--build-variant",
    multiple=True,
    help="Build variant to check (can be specified multiple times).",
)
@click.option(
    "--perform-checkout/--no-perform-checkout",
    is_flag=True,
    default=True,
    help="Whether git checkout should be run on found command.",
)
@click.option(
    "--commit-lookback",
    type=int,
    default=MAX_LOOKBACK,
    help="Number of commits to check before giving up",
)
@click.option("--timeout-secs", type=int, help="Number of seconds to search for before giving up.")
@click.option("--verbose", is_flag=True, default=False, help="Enable debug logging.")
def main(
    passing_task: List[str],
    run_task: List[str],
    run_threshold: float,
    pass_threshold: float,
    evg_config_file: str,
    evg_project: str,
    build_variant: List[str],
    perform_checkout: bool,
    commit_lookback: int,
    timeout_secs: Optional[int],
    verbose: bool,
) -> None:
    """
    Find and checkout a recent git commit that matches the specified criteria.

    When running an Evergreen patch build, it can be useful that base your changes on a commit
    in which the tests in Evergreen have already been run. This way if you encounter any failures
    in your patch build, you can easily compare the failure with what was seen in the base commit
    to understand if your changes may have introduced the failure.

    This command allows you to specify criteria to use to find and checkout a git commit to
    start work from.

    Criteria

    There are 4 criteria that can be specified:

    * The percentage of tasks that have passed in each build.\n
    * The percentage of tasks that have run in each build.\n
    * Specific tasks that must have passed in each build (if they are part of that build).\n
    * Specific tasks that must have run in each build (if they are part of that build).\n

    If not criteria are specified, a success threshold of 0.95 will be used.

    Additionally, you can specify which build variants the criteria should be checked against. By
    default, only builds that end in 'required' will be checked.

    Notes

    If you have any evergreen modules with local checkouts in the location specified in your
    project's evergreen.yml configuration file. They will automatically be checked out to the
    revision that was run in Evergreen with the revision of the base project.

    Examples

    Working on a fix for a task 'replica_sets' on the build variants 'enterprise-rhel-80-64-bit' and
    'enterprise-windows', to ensure the task has been run on those build variants:

      \b
      git co-evg-base --run-task replica_sets --build-variant enterprise-rhel-80-64-bit --build-variant enterprise-windows

    Starting a new change, to ensure that there are no systemic failures on the base commit:

      \b
      git co-evg-base --pass-threshold 0.98

    """
    configure_logging(verbose)

    evg_config_file = os.path.expanduser(evg_config_file)
    evg_api = RetryingEvergreenApi.get_api(config_file=evg_config_file)

    options = GoodBaseOptions(
        perform_checkout=perform_checkout,
        max_lookback=commit_lookback,
        timeout_secs=timeout_secs,
    )

    build_checks = BuildChecks()
    if pass_threshold is not None:
        build_checks.success_threshold = pass_threshold

    if run_threshold is not None:
        build_checks.run_threshold = run_threshold

    if passing_task is not None:
        build_checks.successful_tasks = set(passing_task)

    if run_task is not None:
        build_checks.active_tasks = set(run_task)

    # If no criteria were specified, use the default.
    if not any([pass_threshold, run_threshold, passing_task, run_task]):
        build_checks.success_threshold = DEFAULT_THRESHOLD

    LOGGER.debug("criteria", criteria=build_checks)

    if build_variant:
        build_variant_set = set(build_variant)

        def bv_check(bv: str) -> bool:
            return bv in build_variant_set

    else:

        def bv_check(bv: str) -> bool:
            return bv.endswith("required")

    def dependencies(binder: inject.Binder) -> None:
        binder.bind(EvergreenApi, evg_api)
        binder.bind(BuildVariantPredicate, bv_check)
        binder.bind(GoodBaseOptions, options)

    inject.configure(dependencies)

    orchestrator = GoodBaseOrchestrator()
    revision = orchestrator.checkout_good_base(evg_project, build_checks)

    if revision:
        click.echo(click.style(f"Found revision: {revision.revision}", fg="green"))
        for module_name, module_revision in revision.module_revisions.items():
            click.echo(click.style(f"\t{module_name}: {module_revision}", fg="green"))
    else:
        click.echo(click.style("No revision found", fg="red"))
        sys.exit(1)


if __name__ == "__main__":
    main()
