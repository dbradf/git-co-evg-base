"""Command line entry point to application."""
import os.path
from typing import List, Optional

import click
import inject
from evergreen import EvergreenApi, RetryingEvergreenApi

from goodbase.build_checker import BuildChecks
from goodbase.services.evg_service import BuildVariantPredicate, EvergreenService
from goodbase.services.git_service import GitService

DEFAULT_EVG_CONFIG = "~/.evergreen.yml"
DEFAULT_EVG_PROJECT = "mongodb-mongo-master"
MAX_LOOKBACK = 50
DEFAULT_THRESHOLD = 0.95


class GoodBaseOrchestrator:
    """Orchestrator for checking base commits."""

    @inject.autoparams()
    def __init__(
        self, evg_api: EvergreenApi, evg_service: EvergreenService, git_service: GitService
    ) -> None:
        """
        Initialize the orchestrator.

        :param evg_api: Evergreen API Client.
        :param evg_service:  Evergreen Service.
        :param git_service: Git Service.
        """
        self.evg_api = evg_api
        self.evg_service = evg_service
        self.git_service = git_service

    def find_revision(self, evg_project: str, build_checks: BuildChecks) -> Optional[str]:
        """
        Iterate through revisions until one is found that matches the given criteria.

        :param evg_project: Evergreen project to check.
        :param build_checks: Criteria to enforce.
        :return: First git revision to match the given criteria if it exists.
        """
        with click.progressbar(
            self.evg_api.versions_by_project(evg_project),
            length=MAX_LOOKBACK,
            label=f"Searching {evg_project} revisions",
        ) as bar:
            for idx, evg_version in enumerate(bar):
                if idx > MAX_LOOKBACK:
                    return None

                if self.evg_service.check_version(evg_version, build_checks):
                    return evg_version.revision

        return None

    def checkout_good_base(self, evg_project: str, build_checks: BuildChecks) -> Optional[str]:
        """
        Find the latest git revision that matches the criteria and check it out in git.

        :param evg_project: Evergreen project to check.
        :param build_checks: Criteria to enforce.
        :return: Revision that was checked out, if it exists.
        """
        revision = self.find_revision(evg_project, build_checks)
        if revision:
            self.git_service.checkout(revision)
        return revision


@click.command()
@click.option("--passing-task", type=str, multiple=True)
@click.option("--run-task", type=str, multiple=True)
@click.option("--run-threshold", type=float)
@click.option("--pass-threshold", type=float)
@click.option("--evg-config-file", default=DEFAULT_EVG_CONFIG)
@click.option("--evg-project", default=DEFAULT_EVG_PROJECT)
@click.option("--build-variant", multiple=True)
def main(
    passing_task: List[str],
    run_task: List[str],
    run_threshold: float,
    pass_threshold: float,
    evg_config_file: str,
    evg_project: str,
    build_variant: List[str],
) -> None:
    """
    Find and checkout a recent git commit that matches the specified criteria.

    When running an Evergreen patch build, it can be useful that base your changes on a commit
    in which the tests in Evergreen have already been run. This way if you encounter any failures
    in your patch build, you can easily compare the failure with what was seen in the base commit
    to understand if your changes may have introduced the failure.

    This command allows you to specify criteria to use to find and checkout a git commit to
    start work from.
    """
    evg_config_file = os.path.expanduser(evg_config_file)
    evg_api = RetryingEvergreenApi.get_api(config_file=evg_config_file)

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
    if not all([passing_task, run_threshold, passing_task, run_task]):
        build_checks.success_threshold = DEFAULT_THRESHOLD

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

    inject.configure(dependencies)

    orchestrator = GoodBaseOrchestrator()
    revision = orchestrator.checkout_good_base(evg_project, build_checks)

    if revision:
        click.echo(click.style(f"Found revision: {revision}", fg="green"))
    else:
        click.echo(click.style("No revision found", fg="red"))


if __name__ == "__main__":
    main()
