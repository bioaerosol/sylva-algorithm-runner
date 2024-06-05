import os

from . import JSONEncoder
from bottle import Bottle, response, static_file, HTTPError

from sylva_algorithm_runner import YamlConfiguration
from sylva_algorithm_runner.repositories import DatabaseRepository

def dummyCallback():
    return { "response": "Hello World" }

class APIServer:
    database_repository = None
    configuration = None

    def __init__(self):
        self.configuration = YamlConfiguration("/etc/sylva-algorithm-runner/config.yaml")
        self.database_repository = DatabaseRepository(self.configuration.get("database"))

    def __list_algorithm_run_orders(self):
        return JSONEncoder().encode(self.database_repository.get_algorithm_run_orders_raw({ "_id": 1, "status": 1, "algorithm": 1, "algorithmRepository": 1, "algorithmVersion": 1, "dataset": 1 }))
    
    def __list_algorithm_runs(self, run_order_id: str):
        return JSONEncoder().encode(self.database_repository.get_algorithm_runs_raw(run_order_id, { "_id": 1, "start": 1, "status": 1, "end": 1 }))
    
    def __get_algorithm_run(self, run_order_id: str, run_id: str):
        return JSONEncoder().encode(self.database_repository.get_algorithm_run_raw(run_order_id, run_id, { "_id": 1, "start": 1, "status": 1, "end": 1, "sections": 1, "outputFiles": 1 }))

    def __get_file(self, run_order_id: str, run_id: str, file_path: str):
        has_file = self.database_repository.has_file(run_order_id, run_id, file_path)
        if (has_file):
            output_root = os.path.join(self.configuration.get("runner")["output"], run_id)
            return static_file(file_path, root=output_root)
        else:
            return HTTPError(404)

    def create_application(self, before_request_hook=None, after_request_hook=None):
        app = Bottle()

        if before_request_hook is not None:
            app.add_hook("before_request", before_request_hook)

        if after_request_hook is not None:
            app.add_hook("after_request", after_request_hook)

        app.add_hook("after_request", lambda: response.set_header("Content-Type", "application/json"))

        app.route("/runOrders", method="GET", callback=self.__list_algorithm_run_orders)
        app.route("/runOrders/<run_order_id>/runs", method="GET", callback=self.__list_algorithm_runs)
        app.route("/runOrders/<run_order_id>/runs/<run_id>", method="GET", callback=self.__get_algorithm_run)
        app.route("/runOrders/<run_order_id>/runs/<run_id>/files/<file_path:path>", method="GET", callback=self.__get_file)

        return app