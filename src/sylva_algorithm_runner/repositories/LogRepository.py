from pymongo import MongoClient
from datetime import datetime, timezone

class LogRepository:
    """ Class to handle logging of algorithm runs. """
    configuration = None
    mongo_client = None

    def __init__(self, database_configuration: dict) -> None:
        self.configuration = database_configuration
        self.mongo_client = MongoClient(self.configuration["host"], port=self.configuration["port"], username=self.configuration["user"], password=self.configuration["password"], authSource="admin", tz_aware=True)

    def __get_algorithm_runs_collection(self):
        return self.mongo_client.sylva.algorithmRuns

    def start_run(self, pid):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.insert_one({"pid": pid, "start": datetime.now(timezone.utc)})

    def end_run(self, pid, status: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"pid": pid},
            {"$set": {"end": datetime.now(timezone.utc), "status": status.value}}
        )

    def append_log(self, pid: str, run_section: object, log_line: str):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"pid": pid },
            {"$push": {f"sections.{run_section.value}.log": {"timestamp": datetime.now(timezone.utc), "output": log_line}}}
        )

    def start_section(self, pid: str, run_section: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"pid": pid},
            {"$set": {f"sections.{run_section.value}.start": datetime.now(timezone.utc)}},
            upsert=True
        )
    
    def end_section(self, pid: str, run_section: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"pid": pid},
            {"$set": {f"sections.{run_section.value}.end": datetime.now(timezone.utc)}}
        )

    def set_section_status(self, pid: str, run_section: object, status: object):
        algorithm_runs_collection = self.__get_algorithm_runs_collection()
        algorithm_runs_collection.update_one(
            {"pid": pid},
            {"$set": {f"sections.{run_section.value}.status": status.value}}
        )