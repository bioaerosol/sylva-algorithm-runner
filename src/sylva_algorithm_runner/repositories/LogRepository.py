from pymongo import MongoClient
from datetime import datetime, timezone
from .. import AlgorithmRunOrder
from bson import ObjectId

class LogRepository:
    """ Class to handle logging of algorithm runs. """
    configuration = None
    mongo_client = None
    log_to_stdout = False


    def __init__(self, database_configuration: dict, log_to_stdout: bool = False) -> None:
        self.configuration = database_configuration
        self.mongo_client = MongoClient(self.configuration["host"], port=self.configuration["port"], username=self.configuration["user"], password=self.configuration["password"], authSource="admin", tz_aware=True)
        self.log_to_stdout = log_to_stdout


    def __get_algorithm_runs_collection(self):
        return self.mongo_client[self.configuration["database"]].algorithmRuns

    def get_waiting_for_data(self, algorithm_run_order: AlgorithmRunOrder):
        return self.__get_algorithm_runs_collection().find_one({"status": "WAITING_FOR_DATA", "runOrder": algorithm_run_order._id})

    def start_run(self, algorithm_run_order: AlgorithmRunOrder) -> str:
        """ Initializes a new run and returns the id of the run object."""
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        insert_result = algorithm_runs_collection.insert_one({"start": datetime.now(timezone.utc), "status": "RUNNING", "runOrder": algorithm_run_order._id})
        return str(insert_result.inserted_id)

    def end_run(self, pid: str, status: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$set": {"end": datetime.now(timezone.utc), "status": status.value}}
        )

    def set_status(self, pid: str, status: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$set": {"status": status.value}}
        )

    def log_output_files(self, pid: str, output_files: list):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$set": {"outputFiles": output_files}}
        )

    def append_log(self, pid: str, run_section: object, log_line: str):
        if (self.log_to_stdout):
            print(log_line)
        
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$push": {f"sections.{run_section.value}.log": {"timestamp": datetime.now(timezone.utc), "output": log_line}}}
        )

    def log_workspace_id(self, pid: str, workspace_id: str):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$set": {"workspace": workspace_id}}
        )

    def start_section(self, pid: str, run_section: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$set": {f"sections.{run_section.value}.start": datetime.now(timezone.utc)}},
            upsert=True
        )
    
    def end_section(self, pid: str, run_section: object, status: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"_id": ObjectId(pid)},
            {"$set": { f"sections.{run_section.value}.end": datetime.now(timezone.utc), f"sections.{run_section.value}.status": status.value }}
        )