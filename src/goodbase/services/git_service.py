"""A service for interacting with git."""
from enum import Enum
from pathlib import Path
from typing import Optional

from plumbum import local


class GitAction(str, Enum):
    """
    Git action to perform.

    checkout: Checkout a specific git commit.
    rebase: Rebase changes onto a specific git commit.
    merge: Merge changes from a specific commit onto branch.
    none: Do not perform any actions.
    """

    CHECKOUT = "checkout"
    REBASE = "rebase"
    MERGE = "merge"
    NONE = "none"


class GitService:
    """A service for interacting with git."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.git = local.cmd.git

    def perform_action(
        self,
        action: GitAction,
        revision: str,
        directory: Optional[Path] = None,
        branch_name: Optional[str] = None,
    ) -> None:
        """
        Perform the given git operation.

        :param action: Git operation to perform.
        :param revision: Git revision to perform operation with.
        :param directory: Directory of git repository.
        :param branch_name: Name of branch for git checkout.
        """
        if action == GitAction.NONE:
            return

        self.fetch(directory)
        if action == GitAction.CHECKOUT:
            self.checkout(revision, directory, branch_name)
        elif action == GitAction.REBASE:
            self.rebase(revision, directory)
        elif action == GitAction.MERGE:
            self.merge(revision, directory)

    def checkout(
        self, revision: str, directory: Optional[Path] = None, branch_name: Optional[str] = None
    ) -> None:
        """
        Checkout the given revision.

        :param revision: Revision to checkout.
        :param directory: Directory to execute command at.
        :param branch_name: Name of branch for git checkout.
        """
        args = ["checkout"]
        if branch_name is not None:
            args += ["-b", branch_name]
        args.append(revision)
        with local.cwd(self._determine_directory(directory)):
            self.git[args]()

    def fetch(self, directory: Optional[Path] = None) -> None:
        """
        Check the latest code from origin.

        :param directory: Directory to execute command at.
        """
        with local.cwd(self._determine_directory(directory)):
            self.git["fetch", "origin"]()

    def rebase(self, revision: str, directory: Optional[Path] = None) -> None:
        """
        Rebase on the given revision.

        :param revision: Revision to rebase on.
        :param directory: Directory to execute command at.
        """
        with local.cwd(self._determine_directory(directory)):
            self.git["rebase", revision]()

    def merge(self, revision: str, directory: Optional[Path] = None) -> None:
        """
        Merge the given revision.

        :param revision: Revision to merge.
        :param directory: Directory to execute command at.
        """
        with local.cwd(self._determine_directory(directory)):
            self.git["merge", revision]()

    @staticmethod
    def _determine_directory(directory: Optional[Path] = None) -> Path:
        """
        Determine which directory to run git command in.

        :param directory: Directory containing it repository.
        :return: Path to run git commands in.
        """
        if directory is None:
            return Path(local.cwd)
        elif not directory.is_absolute():
            return Path(local.cwd / directory)
        return directory
