import yaml


class Config:
    """Config which can be loaded with a given YAML file."""

    def __init__(self, path: str) -> None:
        """Initialize Config with a given YAML file.

        Args:
            path (str): The path to a YAML file.
        """
        self.__config = None
        with open(path, 'r') as config:
            self.__config = yaml.safe_load(config)

    def __getitem__(self, key: str):
        """Access configuration value with key.

        Args:
            key (str): The key for a value of the config.

        Returns:
            The value for a given key.
        """
        return self.__config[key]
