import yaml


class Config:
    def __init__(self, path):
        self.__config = None
        with open(path, 'r') as config:
            self.__config = yaml.safe_load(config)

    def __getitem__(self, key):
        return self.__config[key]
