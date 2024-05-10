import yaml

from enum import Enum
from collections import MutableMapping

class AlgorithmRunOrderStatus(Enum):
    CREATED = "CREATED"
    INVALID = "INVALID"

class AlgorithmRunOrder():
    status = AlgorithmRunOrderStatus.CREATED

    sourceId: str
    source: dict

    algorithm: str = None
    algorithmRepository: str = None
    algorithmVersion: str = None

    datasetId: str = None

    def __init__(self, source_id: str, source: dict, algorithm: str, algorithm_repository: str, algorithm_version: str, dataset_id: str) -> None:
        self.sourceId = source_id
        self.source = source
        self.algorithm = algorithm
        self.algorithmRepository = algorithm_repository
        self.algorithmVersion = algorithm_version
        self.datasetId = dataset_id

    def is_valid(self) -> bool:
        return self.algorithm is not None and self.algorithmRepository is not None and self.algorithmVersion is not None and self.datasetId is not None

    def to_dict(self) -> dict:
        return {
            'status': self.status.value,
            'sourceId': self.sourceId,
            'source': self.source,
            'algorithm': self.algorithm,
            'algorithmRepository': self.algorithmRepository,
            'algorithmVersion': self.algorithmVersion,
            'datasetId': self.datasetId
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'AlgorithmRunOrder':
        source_id = data.get('sourceId')
        source = data.get('source')

        algorithm = data.get('algorithm')
        algorithm_repository = data.get('algorithmRepository')
        algorithm_version = data.get('algorithmVersion')

        dataset_id = data.get('datasetId')

        return AlgorithmRunOrder(source_id, source, algorithm, algorithm_repository, algorithm_version, dataset_id)
    
    @staticmethod
    def from_source(source_id: str, source: str) -> None:
        algorithm = None
        algorithmRepository = None
        algorithmVersion = None
        datasetId = None

        try:
            yaml_source = yaml.safe_load(source)

            if 'algorithm' in yaml_source:
                algorithm = yaml_source['algorithm']['name']
                algorithmRepository = yaml_source['algorithm']['repository']
                algorithmVersion = yaml_source['algorithm']['version']

            if 'dataset' in yaml_source:
                datasetId = yaml_source['dataset']['id']

        except Exception as e:
            # no-op by intention
            pass

        return AlgorithmRunOrder(source_id, source, algorithm, algorithmRepository, algorithmVersion, datasetId)
