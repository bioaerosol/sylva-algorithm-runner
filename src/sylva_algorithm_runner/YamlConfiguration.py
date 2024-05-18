import yaml
from typing import Any
from functools import reduce
import operator

class YamlConfiguration():
    """ Class to read a yaml configuration file and return the values of the keys. """
    __configuration = []

    def __init__(self, configuration_file) -> None:
        with open(configuration_file, 'r') as cf:
            self.__configuration = yaml.load(cf, Loader=yaml.FullLoader)

    def get(self, *kwargs) -> Any:
        return reduce(operator.getitem, kwargs, self.__configuration)