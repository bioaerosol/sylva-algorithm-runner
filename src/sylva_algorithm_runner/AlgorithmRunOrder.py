import yaml

from enum import Enum


class AlgorithmRunOrderStatus(Enum):
    CREATED = "CREATED"
    INVALID = "INVALID"

class AlgorithmRunOrder():
    """ Class to represent an order to run an algorithm. Basically a mapping between database document and Python object. """
    _id: str = None
    status = AlgorithmRunOrderStatus.CREATED

    sourceId: str
    source: dict

    algorithm: str = None
    algorithmRepository: str = None
    algorithmVersion: str = None

    dataset: str = None
    localpath: str = None

    def __init__(self, source_id: str, source: dict, algorithm: str, algorithm_repository: str, algorithm_version: str, dataset_id: str, localpath: str, _id: str = None) -> None:
        self.sourceId = source_id
        self.source = source
        self.algorithm = algorithm
        self.algorithmRepository = algorithm_repository
        self.algorithmVersion = algorithm_version
        self.dataset = dataset_id
        self.localpath = localpath
        self._id = _id


    def is_valid(self) -> bool:
        return self.algorithm is not None and self.algorithmRepository is not None and self.algorithmVersion is not None and (self.dataset is not None) != (self.localpath is not None)


    def to_dict(self) -> dict:
        return {
            'status': self.status.value,
            'sourceId': self.sourceId,
            'source': self.source,
            'algorithm': self.algorithm,
            'algorithmRepository': self.algorithmRepository,
            'algorithmVersion': self.algorithmVersion,
            'dataset': self.dataset,
            'localpath': self.localpath
        }
    

    @staticmethod
    def from_dict(data: dict) -> 'AlgorithmRunOrder':
        source_id = data.get('sourceId')
        source = data.get('source')

        algorithm = data.get('algorithm')
        algorithm_repository = data.get('algorithmRepository')
        algorithm_version = data.get('algorithmVersion')

        dataset_id = data.get('dataset')
        localpath = data.get('localpath')

        _id = data.get('_id')

        return AlgorithmRunOrder(source_id, source, algorithm, algorithm_repository, algorithm_version, dataset_id, localpath, _id)
    
    
    @staticmethod
    def from_source(source_id: str, source: str) -> None:
        algorithm = None
        algorithmRepository = None
        algorithmVersion = None
        dataset = None
        localpath = None

        try:
            yaml_source = yaml.safe_load(source)

            if 'algorithm' in yaml_source:
                algorithm = yaml_source['algorithm']['name']
                algorithmRepository = yaml_source['algorithm']['repository']
                algorithmVersion = yaml_source['algorithm']['version']

            if 'dataset' in yaml_source:
                dataset = yaml_source['dataset']['name'] if 'name' in yaml_source['dataset'] else None         
                localpath = yaml_source['dataset']['localpath'] if 'localpath' in yaml_source['dataset'] else None

        except Exception as e:
            # no-op by intention
            pass

        return AlgorithmRunOrder(source_id, source, algorithm, algorithmRepository, algorithmVersion, dataset, localpath)
