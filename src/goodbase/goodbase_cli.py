"""Command line entry point to application."""
import json
import logging
import os.path
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional

import click
import inject
import structlog
import yaml
from evergreen import EvergreenApi, RetryingEvergreenApi
from plumbum import ProcessExecutionError
from rich.console import Console
from rich.table import Table
from structlog.stdlib import LoggerFactory

from goodbase.build_checker import BuildChecks
from goodbase.goodbase_options import GoodBaseOptions, OutputFormat
from goodbase.services.criteria_service import CriteriaService
from goodbase.services.evg_service import EvergreenService
from goodbase.services.git_service import GitAction, GitService
from goodbase.services.search_service import SearchService

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


class RevisionInformation(NamedTuple):
    """
    Details about what revision(s) were found.

    revision: Revision of base project.
    module_revisions: Revisions of any modules associated with the project.
    errors: Errors encountered while performing git operations.
    """

    revision: str
    module_revisions: Dict[str, str]
    errors: Optional[Dict[str, str]] = None


class GoodBaseOrchestrator:
    """Orchestrator for checking base commits."""

    @inject.autoparams()
    def __init__(
        self,
        evg_service: EvergreenService,
        git_service: GitService,
        criteria_service: CriteriaService,
        search_service: SearchService,
        options: GoodBaseOptions,
        console: Console,
    ) -> None:
        """
        Initialize the orchestrator.

        :param evg_service:  Evergreen Service.
        :param git_service: Git Service.
        :param criteria_service: Service for working with criteria.
        :param search_service: Service to search revisions.
        :param options: Options for execution.
        :param console: Rich console to print to.
        """
        self.evg_service = evg_service
        self.git_service = git_service
        self.criteria_service = criteria_service
        self.search_service = search_service
        self.options = options
        self.console = console

    def attempt_git_operation(
        self, operation: GitAction, revision: str, directory: Optional[Path] = None
    ) -> Optional[str]:
        """
        Attempt to perform the specified git operation.

        :param operation: Git operation to perform.
        :param revision: Git revision to perform operation on.
        :param directory: Directory of git repository.
        :return: Error message if an error was encountered.
        """
        try:
            self.git_service.perform_action(
                operation, revision, directory, self.options.branch_name
            )
        except ProcessExecutionError:
            LOGGER.warning("Error encountered during git operation", exc_info=True)
            return f"Encountered error performing '{operation}' on '{revision}'"
        return None

    def checkout_modules(
        self, evg_project: str, module_revisions: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Checkout existing modules to the specified revisions.

        :param evg_project: Evergreen project of modules.
        :param module_revisions: Dictionary of module names and git revisions to check out.
        :return: Dictionary of error encountered.
        """
        if self.options.operation == GitAction.NONE:
            return {}

        module_locations = self.evg_service.get_module_locations(evg_project)
        LOGGER.debug(
            "Checking out modules",
            module_locations=module_locations,
            module_revisions=module_revisions,
        )
        errors_encountered = {}
        for module, module_rev in module_revisions.items():
            directory = Path(module_locations[module]) / module
            if directory.exists():
                errmsg = self.attempt_git_operation(self.options.operation, module_rev, directory)
                if errmsg:
                    errors_encountered[module] = errmsg

        return errors_encountered

    def checkout_good_base(
        self,
        evg_project: str,
        build_checks: List[BuildChecks],
    ) -> Optional[RevisionInformation]:
        """
        Find the latest git revision that matches the criteria and check it out in git.

        :param evg_project: Evergreen project to check.
        :param build_checks: Criteria to enforce.
        :return: Revision that was checked out, if it exists.
        """
        revision = self.search_service.find_revision(evg_project, build_checks)
        if revision:
            module_revisions = self.evg_service.get_modules_revisions(evg_project, revision)
            errmsg = self.attempt_git_operation(self.options.operation, revision)
            errors_encountered = self.checkout_modules(evg_project, module_revisions)
            if errmsg:
                errors_encountered["BASE"] = errmsg

            return RevisionInformation(
                revision=revision, module_revisions=module_revisions, errors=errors_encountered
            )
        return None

    def save_criteria(self, name: str, build_checks: BuildChecks) -> None:
        """
        Save the given criteria under the given name.

        :param name: Name to save criteria under.
        :param build_checks: Criteria to save.
        """
        self.criteria_service.save_criteria(name, build_checks)

    def lookup_criteria(self, name: str) -> List[BuildChecks]:
        """
        Lookup the specified criteria in the config file.

        :param name: Name of criteria to lookup.
        :return: Saved criteria.
        """
        return self.criteria_service.lookup_criteria(name)

    def export_criteria(self, rules: List[str], destination: Path) -> None:
        """
        Export the given rules to the destination file.

        :param rules: Names of rules to export.
        :param destination: Path of file to export to.
        """
        self.criteria_service.export_criteria(rules, destination)

    def import_criteria(self, import_file: Path) -> None:
        """
        Import rules from the given file.

        :param import_file: File containing rules to import.
        """
        self.criteria_service.import_criteria(import_file)

    def display_criteria(self) -> None:
        """Display saved criteria."""
        for group in self.criteria_service.get_all_criteria():
            table = Table(title=group.name, show_lines=True)
            table.add_column("Build Variant Regexes")
            table.add_column("Success %")
            table.add_column("Run %")
            table.add_column("Successful Tasks")
            table.add_column("Run Tasks")

            for rule in group.rules:
                table.add_row(
                    "\n".join(rule.build_variant_regex),
                    f"{rule.success_threshold}" if rule.success_threshold else "",
                    f"{rule.run_threshold}" if rule.run_threshold else "",
                    "\n".join(rule.successful_tasks) if rule.successful_tasks else "",
                    "\n".join(rule.active_tasks) if rule.active_tasks else "",
                )

            self.console.print(table)


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
    help="Regex of Build variants to check (can be specified multiple times).",
)
@click.option(
    "--commit-lookback",
    type=int,
    default=MAX_LOOKBACK,
    help="Number of commits to check before giving up",
)
@click.option("--timeout-secs", type=int, help="Number of seconds to search for before giving up.")
@click.option(
    "--commit-limit",
    type=str,
    help="Oldest commit to check before giving up.",
)
@click.option(
    "--git-operation",
    type=click.Choice([a.value for a in GitAction]),
    default=GitAction.CHECKOUT,
    help="Git operations to perform with found commit [default=checkout].",
)
@click.option("-b", "--branch", help="Name of branch to create on checkout.")
@click.option(
    "--save-criteria",
    type=str,
    help="Save the specified criteria rules under the specified name for future use.",
)
@click.option("--use-criteria", type=str, help="Use previously save criteria rules.")
@click.option("--list-criteria", is_flag=True, help="Display saved criteria.")
@click.option(
    "--override",
    is_flag=True,
    default=False,
    help="Override saved conflicting save criteria rules.",
)
@click.option(
    "--export-criteria", multiple=True, help="Specify saved criteria to export to a file."
)
@click.option("--export-file", type=click.Path(), help="File to write exported rules to.")
@click.option(
    "--import-criteria", type=click.Path(exists=True), help="Import previously exported criteria."
)
@click.option(
    "--output-format",
    type=click.Choice([f.value for f in OutputFormat]),
    default=OutputFormat.PLAINTEXT,
    help="Format of the command output [default=plaintext].",
)
@click.option("--verbose", is_flag=True, default=False, help="Enable debug logging.")
def main(
    passing_task: List[str],
    run_task: List[str],
    run_threshold: float,
    pass_threshold: float,
    evg_config_file: str,
    evg_project: str,
    build_variant: List[str],
    commit_lookback: int,
    commit_limit: Optional[str],
    timeout_secs: Optional[int],
    git_operation: GitAction,
    branch: Optional[str],
    save_criteria: Optional[str],
    use_criteria: Optional[str],
    list_criteria: bool,
    export_criteria: List[str],
    export_file: str,
    import_criteria: Optional[str],
    output_format: OutputFormat,
    override: bool,
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
        max_lookback=commit_lookback,
        commit_limit=commit_limit,
        operation=git_operation,
        override_criteria=override,
        timeout_secs=timeout_secs,
        branch_name=branch,
        output_format=output_format,
    )

    build_variant_checks = [".*-required$"]

    if build_variant:
        build_variant_checks = build_variant

    build_checks = BuildChecks(build_variant_regex=build_variant_checks)
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

    def dependencies(binder: inject.Binder) -> None:
        binder.bind(EvergreenApi, evg_api)
        binder.bind(GoodBaseOptions, options)

    inject.configure(dependencies)

    orchestrator = GoodBaseOrchestrator()
    if list_criteria:
        orchestrator.display_criteria()

    elif save_criteria:
        try:
            orchestrator.save_criteria(save_criteria, build_checks)
        except ValueError as err:
            click.echo(click.style(f"Could not save: {save_criteria}", fg="red"))
            click.echo(click.style(str(err), fg="red"))
            sys.exit(1)

    elif export_criteria:
        if not export_file:
            click.echo(
                click.style("Export file needs to be specified with `--export-file`", fg="red")
            )
            sys.exit(1)

        orchestrator.export_criteria(export_criteria, Path(export_file))

    elif import_criteria:
        try:
            orchestrator.import_criteria(Path(import_criteria))
        except ValueError as err:
            click.echo(click.style(f"Could not import from: {import_criteria}", fg="red"))
            click.echo(click.style(str(err), fg="red"))
            sys.exit(1)

    else:
        criteria = [build_checks]
        if use_criteria:
            try:
                criteria = orchestrator.lookup_criteria(use_criteria)
            except ValueError as err:
                click.echo(click.style(f"Could not use: {save_criteria}", fg="red"))
                click.echo(click.style(str(err), fg="red"))
                sys.exit(1)

        LOGGER.debug("criteria", criteria=build_checks)

        revision = orchestrator.checkout_good_base(evg_project, criteria)

        if revision:
            revision_dict = {
                module_name: module_revision
                for module_name, module_revision in revision.module_revisions.items()
            }
            revision_dict["stable_revision"] = revision.revision

            if output_format == OutputFormat.YAML:
                print(yaml.dump(revision_dict, sort_keys=False))
            elif output_format == OutputFormat.JSON:
                print(json.dumps(revision_dict))
            else:  # "plaintext"
                click.echo(click.style(f"Found revision: {revision.revision}", fg="green"))
                for module_name, module_revision in revision.module_revisions.items():
                    click.echo(click.style(f"\t{module_name}: {module_revision}", fg="green"))

            if revision.errors:
                click.echo(
                    click.style(
                        f"Encountered {len(revision.errors)} errors performing git operations",
                        fg="yellow",
                        bold=True,
                    )
                )
                click.echo(click.style("Conflicts may need to be manually resolved."))
                for module, errmsg in revision.errors.items():
                    click.echo(click.style(f"\t{module}: {errmsg}", fg="yellow"))
        else:
            click.echo(click.style("No revision found", fg="red"))
            sys.exit(1)


if __name__ == "__main__":
    main()
