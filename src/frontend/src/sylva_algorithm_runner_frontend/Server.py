from bottle import Bottle
from . import DatabaseResource

class Server:
    def create_application(self, before_request_hook=None, after_request_hook=None):
        app = Bottle()

        if before_request_hook is not None:
            app.add_hook("before_request", before_request_hook)

        if after_request_hook is not None:
            app.add_hook("after_request", after_request_hook)

        database_resource = DatabaseResource()
        app.route("/runOrders", method="GET", callback=database_resource.get_run_orders)

        return app