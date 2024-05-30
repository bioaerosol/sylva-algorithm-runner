
from sylva_algorithm_runner import AlgorithmRunOrder, AlgorithmRunOrderStatus
from bson import ObjectId
from pymongo import MongoClient

class DatabaseRepository:
    """ Class to handle database operations. """
    configuration = None
    mongo_client = None

    def __init__(self, database_configuration: dict) -> None:
        self.configuration = database_configuration
        self.mongo_client = MongoClient(self.configuration["host"], port=self.configuration["port"], username=self.configuration["user"], password=self.configuration["password"], authSource="admin", tz_aware=True)


    def add_if_missing(self, algorithm_run_order: AlgorithmRunOrder) -> bool:
        """ Adds the given algorithm run order to the database if it is not already present (identified by sourceId). """
        existing_order = self.__get_algorithm_run_order_collection().find_one({"sourceId": algorithm_run_order.sourceId})
        added = False

        if existing_order is None:
            self.__get_algorithm_run_order_collection().insert_one(algorithm_run_order.to_dict())
            added = True

        return added

    def get_algorithm_run_orders_raw(self, projection = None) -> list:
        """ Returns all algorithm run orders as noted in database. It's up to caller to do right projection. """
        return list(self.__get_algorithm_run_order_collection().find({}, projection=projection))
    
    def get_algorithm_runs_raw(self, run_order_id: str, projection = None) -> list:
        """ Returns all algorithm runs for the given algorithm run order as noted in database. It's up to caller to do right projection. """
        return list(self.__get_algorithm_run_collection().find({ "runOrder": ObjectId(run_order_id) }, projection=projection))
    
    def get_algorithm_run_raw(self, run_order_id: str, run_id: str, projection = None) -> list:
        """ Returns the requested algorithm run for the given algorithm run order as noted in database. It's up to caller to do right projection. """
        return self.__get_algorithm_run_collection().find_one({ "runOrder": ObjectId(run_order_id), "_id": ObjectId(run_id) }, projection=projection)

    def get_algorithm_run_order_in_status_created(self, id: str) -> AlgorithmRunOrder:
        """ Returns the algorithm run order with the given id if it is in status CREATED. """
        try: 
            object = self.__get_algorithm_run_order_collection().find_one({"_id": ObjectId(id), "status": AlgorithmRunOrderStatus.CREATED.value})
        except Exception as e:
            object = None

        return AlgorithmRunOrder.from_dict(object) if object is not None else None
    

    def update_algorithm_run_order_status(self, id: str, status: AlgorithmRunOrderStatus):
        """ Updates the status of the algorithm run order with the given id. """
        self.__get_algorithm_run_order_collection().update_one({"_id": ObjectId(id)}, {"$set": {"status": status.value}})


    def __get_algorithm_run_order_collection(self):
        return self.mongo_client.sylva.algorithmRunOrders
    
    def __get_algorithm_run_collection(self):
        return self.mongo_client.sylva.algorithmRuns
