from enum import Enum
from collections import MutableMapping

class AlgorithmRunOrderStatus(Enum):
    CREATED = "CREATED"

class AlgorithmRunOrder():
    status = AlgorithmRunOrderStatus.CREATED

    sourceId: str
    source: dict

    algorithm: str = None
    algorithmRepository: str = None
    algorithmVersion: str = None

    datasetId: str = None

    def __init__(self, source_id: str, source: dict) -> None:
        super().__init__()
        self.sourceId = source_id
        self.source = source

        try:
            if 'algorithm' in source:
                self.algorithm = source['algorithm']['name']
                self.algorithmRepository = source['algorithm']['repository']
                self.algorithmVersion = source['algorithm']['version']

            if 'dataset' in source:
                self.datasetId = source['dataset']['id']

        except Exception as e:
            # no-op by intention
            pass

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