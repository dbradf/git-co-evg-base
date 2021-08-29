"""A service for interacting with git."""
from plumbum import local


class GitService:
    """A service for interacting with git."""

    def __init__(self) -> None:
        """Initialize the service."""
        self.git = local.cmd.git

    def checkout(self, revision: str) -> None:
        """
        Checkout the given revision.

        :param revision: Revision to checkout.
        """
        self.git["checkout", revision]()

    def fetch(self) -> None:
        """Check the latest code from origin."""
        self.git["fetch", "origin"]()
