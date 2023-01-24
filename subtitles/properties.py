from copy import deepcopy
from dotenv import load_dotenv
import os.path
import yaml

DEFAULT_PROPERTIES = {
    'api': {'port': 50055},
    'receiver': {'host': 'localhost', 'port': '50053'},
    'transcriber': 'whisper',
    'vosk': {
        'model_dir': '/tmp',
        'download_urls': [],
        'models': []
    },
    'whisper': {'model': 'tiny'},
    'max_threads': None,
    'cnt_workers': 1,
}


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
        """Initialize Config with a given .env file."""
        if default is None:
            default = {}
        self._default = default
        load_dotenv()

    def get(self) -> dict:
        """Reads the properties file, overwrites defaults, and returns a dictionary.

        Returns:
            Dictionary containing the properties.
        """
        properties = deepcopy(self._default)
        properties['api']['port'] = os.getenv('API_PORT', properties['api']['port'])
        properties['receiver']['host'] = os.getenv('REC_HOST', properties['receiver']['host'])
        properties['receiver']['port'] = os.getenv('REC_PORT', properties['receiver']['port'])

        properties['transcriber'] = os.getenv('TRANSCRIBER', properties['transcriber'])

        properties['vosk']['model_dir'] = os.getenv('VOSK_MODEL_DIR', properties['vosk']['model_dir'])

        # format: https://x.com,https://y.com
        if os.getenv('VOSK_DWNLD_URLS'):
            properties['vosk']['download_urls'] = os.getenv('VOSK_DWNLD_URLS').split(',')

        # format: /models/de:de,/models/en:en
        if os.getenv('VOSK_MODELS'):
            models = [self.__to_model_obj(model)
                      for model in os.getenv('VOSK_MODELS').split(',')]

            properties['vosk']['models'] = models

        properties['whisper']['model'] = os.getenv('WHISPER_MODEL', properties['whisper']['model'])

        max_threads = os.getenv('MAX_THREADS', properties['max_threads'])
        if max_threads:
            properties['max_threads'] = int(max_threads)

        cnt_workers = os.getenv('CNT_WORKERS', properties['cnt_workers'])
        if cnt_workers:
            properties['cnt_workers'] = int(cnt_workers)

        return properties

    def __to_model_obj(self, model: str):
        model_lang_pair = model.split(':')
        return {'name': model_lang_pair[0], 'lang': model_lang_pair[1]}


def _validate(file_path: str, file_type: str) -> None:
    if not file_path.endswith(file_type):
        raise PropertyError(f'must be a {file_type} file: {file_path}')
    if not os.path.exists(file_path):
        raise PropertyError(f'can not find {file_type} file {file_path}')
