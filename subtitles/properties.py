import os.path
from copy import deepcopy
from dotenv import load_dotenv
import yaml


class PropertyError(Exception):
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
        self._validate_path()

    def get(self) -> dict:
        """Reads the properties file, overwrites defaults, and returns a dictionary.

        Returns:
            Dictionary (dict) containing the properties.
        """
        properties = deepcopy(self._default)
        with open(self._path, 'r') as file:
            properties.update(yaml.safe_load(file))
        return properties

    def _validate_path(self) -> None:
        """Validate path to properties file"""
        _validate(self._path, ".yml")


class EnvProperties:
    """Config which can be loaded with environment variables file"""

    def __init__(self, default=None) -> None:
        """Initialize Config with a given YAML file.

        Args:
            path (str): The path to a YAML file.
        """
        if default is None:
            default = {}
        self._default = default
        load_dotenv()

    def get(self) -> dict:
        """Reads the properties file, overwrites defaults, and returns a dictionary.

        Returns:
            Dictionary (dict) containing the properties.
        """
        properties = deepcopy(self._default)
        properties['api']['port'] = os.getenv('API_PORT', properties['api']['port'])
        properties['receiver']['host'] = os.getenv('REC_HOST', properties['receiver']['host'])
        properties['receiver']['port'] = os.getenv('REC_PORT', properties['receiver']['port'])

        # format: /models/de:de,/models/en:en
        if os.getenv('VOSK_MODELS'):
            models = [{'path': model.split(':')[0], 'lang': model.split(':')[1]}
                      for model in os.getenv('VOSK_MODELS').split(',')]

            properties['vosk']['models'] = models
        return properties


def _validate(file_path: str, file_type: str) -> None:
    if not file_path.endswith(file_type):
        raise PropertyError(f'must be a {file_type} file: {file_path}')
    if not os.path.exists(file_path):
        raise PropertyError(f'can not find {file_type} file {file_path}')
