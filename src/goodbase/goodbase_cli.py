"""Command line entry point to application."""
import os.path
from typing import Optional

import click
import inject
from evergreen import EvergreenApi, RetryingEvergreenApi

from goodbase.build_checker import BuildChecks
from goodbase.services.evg_service import BuildVariantPredicate, EvergreenService
from goodbase.services.git_service import GitService

DEFAULT_EVG_CONFIG = "~/.evergreen.yml"
DEFAULT_EVG_PROJECT = "mongodb-mongo-master"
MAX_LOOKBACK = 15
DEFAULT_THRESHOLD = 0.95


class GoodBaseOrchestrator:
    @inject.autoparams()
    def __init__(self, evg_api: EvergreenApi, evg_service: EvergreenService, git_service: GitService) -> None:
        self.evg_api = evg_api
        self.evg_service = evg_service
        self.git_service = git_service

    def find_revision(self, evg_project: str, build_checks: BuildChecks) -> Optional[str]:
        for idx, evg_version in enumerate(self.evg_api.versions_by_project(evg_project)):
            if idx > MAX_LOOKBACK:
                return None

            if self.evg_service.check_version(evg_version, build_checks):
                return evg_version.revision

        return None

    def checkout_good_base(self, evg_project, build_checks: BuildChecks) -> Optional[str]:
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
    passing_task,
    run_task,
    run_threshold,
    pass_threshold,
    evg_config_file,
    evg_project,
    build_variant,
) -> None:
    """
    Hello World
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

    bv_check = lambda bv: bv.endswith("required")
    if build_variant:
        build_variant_set = set(build_variant)
        bv_check = lambda bv: bv in build_variant_set

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
