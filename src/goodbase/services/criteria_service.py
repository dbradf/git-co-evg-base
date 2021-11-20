"""Service for working with criteria."""
from pathlib import Path
from typing import List

import inject

from goodbase.build_checker import BuildChecks
from goodbase.goodbase_options import GoodBaseOptions
from goodbase.services.config_service import (
    ConfigurationService,
    CriteriaConfiguration,
    CriteriaGroup,
)
from goodbase.services.file_service import FileService


class CriteriaService:
    """A service for working with criteria."""

    @inject.autoparams()
    def __init__(
        self,
        config_service: ConfigurationService,
        file_service: FileService,
        options: GoodBaseOptions,
    ) -> None:
        """
        Initialize the service.

        :param config_service: Service for working with configuration.
        :param file_service: Service for working with files.
        :param options: Goodbase options.
        """
        self.config_service = config_service
        self.file_service = file_service
        self.options = options

    def save_criteria(self, name: str, build_checks: BuildChecks) -> None:
        """
        Save the given criteria under the given name.

        :param name: Name to save criteria under.
        :param build_checks: Criteria to save.
        """
        configuration = self.config_service.get_config()
        configuration.add_criteria(name, build_checks, self.options.override_criteria)
        self.config_service.save_config(configuration)

    def lookup_criteria(self, name: str) -> List[BuildChecks]:
        """
        Lookup the specified criteria in the config file.

        :param name: Name of criteria to lookup.
        :return: Saved criteria.
        """
        configuration = self.config_service.get_config()
        criteria = configuration.get_criteria_group(name)
        if not criteria.rules:
            raise ValueError("Not criteria found")
        return criteria.rules

    def export_criteria(self, rules: List[str], destination: Path) -> None:
        """
        Export the given rules to the destination file.

        :param rules: Names of rules to export.
        :param destination: Path of file to export to.
        """
        rules_set = set(rules)
        configuration = self.config_service.get_config()
        rules_to_export = [rule for rule in configuration.saved_criteria if rule.name in rules_set]
        export_config = CriteriaConfiguration(saved_criteria=rules_to_export)
        self.file_service.write_yaml_file(destination, export_config.dict(exclude_none=True))

    def import_criteria(self, import_file: Path) -> None:
        """
        Import rules from the given file.

        :param import_file: File containing rules to import.
        """
        configuration = self.config_service.get_config()
        import_file_contents = self.file_service.read_yaml_file(import_file)
        import_criteria = CriteriaConfiguration(**import_file_contents)
        for rule in import_criteria.saved_criteria:
            for criteria in rule.rules:
                configuration.add_criteria(rule.name, criteria, self.options.override_criteria)
        self.config_service.save_config(configuration)

    def get_all_criteria(self) -> List[CriteriaGroup]:
        """Get all saved criteria."""
        configuration = self.config_service.get_config()
        return configuration.saved_criteria
