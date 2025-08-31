
from sylva_algorithm_runner import AlgorithmRunOrder, AlgorithmRunOrderStatus
from bson import ObjectId
from pymongo import MongoClient
import typing
import subprocess

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

    def has_file(self, run_order_id: str, run_id: str, file_path: str) -> bool:
        """ Checks if the given file is present in the database. """
        return self.__get_algorithm_run_collection().find_one({ "runOrder": ObjectId(run_order_id), "_id": ObjectId(run_id), "outputFiles": {"$elemMatch": {"filePath": file_path}} }) is not None

    def find_next_to_run_id(self, count) -> typing.List[str]:
        """ Returns the id of the next algorithm run order to run. This is either a run order with no algorithm runs or an algorithm run in status WAITING_FOR_DATA."""
        
        def count_local_sylva_algorithm_run_processes():
            """Counts the number of local Unix processes running 'sylva-algorithm-run'."""
            try:
                output = subprocess.check_output(
                    ["ps", "aux"], universal_newlines=True
                )
                lines = [line for line in output.splitlines() if "sylva-algorithm-run " in line]
                for line in lines:
                    print(line)
                return len(lines)
            except Exception:
                return 0

        currently_running_count = count_local_sylva_algorithm_run_processes() # currently running count is for local machine
        count_left = count - currently_running_count

        print(f"Currently running processes on local machine: {currently_running_count}, new possible processes: {count_left}.")

        if count_left > 0:
            results = self.__get_algorithm_run_order_collection().aggregate([
                {
                    "$lookup": {
                    "from": "algorithmRuns",
                    "localField": "_id",
                    "foreignField": "runOrder",
                    "as": "algorithmRuns"
                    }
                },
                {
                    "$sort": { 'algorithmRuns.status' : -1 }
                },
                {
                    "$sort": { "_id": -1 }
                },
                {
                    "$match": {
                        "$and": [
                            { "status": "CREATED" },
                            { "$or": [
                                {
                                    'algorithmRuns.status': 'WAITING_FOR_DATA'
                                },
                                {
                                    "algorithmRuns": {
                                        "$size": 0
                                    }
                                }
                                ]}
                        ]
                    }
                },
                {
                    "$project": {
                    "_id": 1
                    }
                },
                {
                    "$limit": count_left
                }
            ])

            found = [str(result['_id']) for result in results]
            
            print(f"Found {len(found)} algorithm run orders to start.")

            return found
        else:
            return []

    def __get_algorithm_run_order_collection(self):
        return self.mongo_client[self.configuration["database"]].algorithmRunOrders
    
    def __get_algorithm_run_collection(self):
        return self.mongo_client[self.configuration["database"]].algorithmRuns
