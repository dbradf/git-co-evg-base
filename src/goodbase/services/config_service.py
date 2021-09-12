"""Service for working with configuration."""
from __future__ import annotations

from typing import List

import inject
from pydantic import BaseModel
from xdg import xdg_config_home

from goodbase.build_checker import BuildChecks
from goodbase.services.file_service import FileService

CONFIG_FILE_LOCATION = xdg_config_home() / "git_co_evg_base.yml"


class CriteriaGroup(BaseModel):
    """A saved set of criteria that can be reused."""

    name: str
    rules: List[BuildChecks]

    def add_build_checks(self, build_checks: BuildChecks, override: bool = False) -> None:
        """
        Add the given build checks to this criteria group.

        :param build_checks: checks to add.
        :param override: Overwrite checks if they already exist.
        """
        existing_rules = [
            bc for bc in self.rules if bc.build_variant_regex == build_checks.build_variant_regex
        ]
        other_rules = [
            bc for bc in self.rules if bc.build_variant_regex != build_checks.build_variant_regex
        ]
        if existing_rules and not override:
            raise ValueError("Rule already exists, use `--override` to override it.")
        self.rules = other_rules
        self.rules.append(build_checks)


class CriteriaConfiguration(BaseModel):
    """Configuration file format."""

    saved_criteria: List[CriteriaGroup]

    @classmethod
    def new(cls) -> CriteriaConfiguration:
        """Create a new instance of the config file."""
        return cls(saved_criteria=[])

    def get_criteria_group(self, name: str) -> CriteriaGroup:
        """
        Get the specified criteria group.

        :param name: Name of criteria group to query.
        :return: Queried criteria group or empty group if it doesn't exist.
        """
        existing_criteria = [criteria for criteria in self.saved_criteria if criteria.name == name]
        if len(existing_criteria) > 0:
            return existing_criteria[0]
        else:
            return CriteriaGroup(name=name, rules=[])

    def save_criteria_group(self, name: str, group: CriteriaGroup) -> None:
        """
        Save the specified criteria group.

        :param name: Name to save group under.
        :param group: Group to save.
        """
        other_criteria = [c for c in self.saved_criteria if c.name != name]
        self.saved_criteria = other_criteria
        self.saved_criteria.append(group)

    def add_criteria(self, name: str, build_checks: BuildChecks, override: bool = False) -> None:
        """
        Add the given criteria to the specified criteria group.

        :param name: Name of criteria group.
        :param build_checks: criteria to add.
        :param override: Should criteria overwrite existing criteria.
        """
        criteria = self.get_criteria_group(name)
        criteria.add_build_checks(build_checks, override)
        self.save_criteria_group(name, criteria)


class ConfigurationService:
    """Service for working with configuration."""

    @inject.autoparams()
    def __init__(self, file_service: FileService) -> None:
        """
        Initialize the service.

        :param file_service: Service for working with files.
        """
        self.file_service = file_service

    def get_config(self) -> CriteriaConfiguration:
        """Get the saved configuration or create a new empty configuration."""
        if self.file_service.path_exists(CONFIG_FILE_LOCATION):
            config_file_contents = self.file_service.read_yaml_file(CONFIG_FILE_LOCATION)
            return CriteriaConfiguration(**config_file_contents)
        else:
            return CriteriaConfiguration.new()

    def save_config(self, config: CriteriaConfiguration) -> None:
        """
        Save the given config.

        :param config: Configuration to save.
        """
        self.file_service.write_yaml_file(CONFIG_FILE_LOCATION, config.dict(exclude_none=True))
