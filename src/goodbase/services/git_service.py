"""A service for interacting with git."""
from pathlib import Path
from typing import Optional

from plumbum import local


class GitService:
    """A service for interacting with git."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.git = local.cmd.git

    def fetch_and_checkout(self, revision: str, directory: Optional[Path] = None) -> None:
        """
        Fetch the latest data from origin and checkout the given commit.

        :param revision: commit revision to checkout.
        :param directory: Directory to execute command at.
        """
        self.fetch(directory)
        self.checkout(revision, directory)

    def checkout(self, revision: str, directory: Optional[Path] = None) -> None:
        """
        Checkout the given revision.

        :param revision: Revision to checkout.
        :param directory: Directory to execute command at.
        """
        if directory is None:
            directory = local.cwd
        elif not directory.is_absolute():
            directory = local.cwd / directory

        with local.cwd(directory):
            self.git["checkout", revision]()

    def fetch(self, directory: Optional[Path] = None) -> None:
        """
        Check the latest code from origin.

        :param directory: Directory to execute command at.
        """
        if directory is None:
            directory = local.cwd
        elif not directory.is_absolute():
            directory = local.cwd / directory

        with local.cwd(directory):
            self.git["fetch", "origin"]()
