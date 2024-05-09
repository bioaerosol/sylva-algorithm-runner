import yaml
from typing import List, Any
from functools import reduce
import operator

class YamlConfiguration():
    __configuration = []

    def __init__(self, configuration_file) -> None:
        with open(configuration_file, 'r') as cf:
            self.__configuration = yaml.load(cf, Loader=yaml.FullLoader)

    def get(self, attributes: List[str]) -> Any:
        return reduce(operator.getitem, attributes, self.__configuration)