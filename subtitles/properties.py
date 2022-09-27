import os.path
from copy import deepcopy

import yaml


class YAMLPropertiesFileError(Exception):
    pass


class YAMLPropertiesFile:
    """Config which can be loaded with a given YAML file."""

    def __init__(self, path: str, default=None) -> None:
        """Initialize Config with a given YAML file.

        Args:
            path (str): The path to a YAML file.
        """
        if default is None:
            default = {}
        self._path = path
        self._default = default
        self._validate_path(path)

    def get(self) -> dict:
        """Reads the properties file, overwrites defaults, and returns a dictionary.

        Returns:
            Dictionary (dict) containing the properties.
        """
        properties = deepcopy(self._default)
        with open(self._path, 'r') as file:
            properties.update(yaml.safe_load(file))
        return properties

    def _validate_path(self, path: str) -> None:
        """Validate path to properties file"""
        if not path.endswith(".yml"):
            raise YAMLPropertiesFileError(f'must be a YAML file: {path}')
        if not os.path.exists(path):
            raise YAMLPropertiesFileError(f'can not find properties file {path}')
