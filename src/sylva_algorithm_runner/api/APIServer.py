from . import JSONEncoder
from bottle import Bottle

from sylva_algorithm_runner import YamlConfiguration
from sylva_algorithm_runner.repositories import DatabaseRepository

def dummyCallback():
    return { "response": "Hello World" }

class APIServer:
    database_repository = None

    def __init__(self):
        configuration = YamlConfiguration("/etc/sylva-algorithm-runner/config.yaml")
        self.database_repository = DatabaseRepository(configuration.get("database"))

    def __list_algorithm_run_orders(self):
        return JSONEncoder().encode(self.database_repository.get_algorithm_run_orders_raw({ "_id": 1, "status": 1, "algorithm": 1, "algorithmRepository": 1, "algorithmVersion": 1, "dataset": 1 }))
    
    def create_application(self, before_request_hook=None, after_request_hook=None):
        app = Bottle()

        if before_request_hook is not None:
            app.add_hook("before_request", before_request_hook)

        if after_request_hook is not None:
            app.add_hook("after_request", after_request_hook)

        app.route("/runOrders", method="GET", callback=self.__list_algorithm_run_orders)

        return app