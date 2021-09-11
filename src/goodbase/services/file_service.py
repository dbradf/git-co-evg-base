"""A service for working with files."""
from pathlib import Path
from typing import Any, Dict

import yaml


class FileService:
    """A service for working with files."""

    @staticmethod
    def read_yaml_file(file_path: Path) -> Dict[str, Any]:
        """
        Read the given yaml file into a dictionary.

        :param file_path: Path to yaml file to read.
        :return: Dictionary of yaml contents.
        """
        with open(file_path) as file_contents:
            return yaml.safe_load(file_contents)
