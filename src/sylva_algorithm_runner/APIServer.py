from bottle import Bottle

def dummyCallback():
    return { "response": "Hello World" }

class APIServer:
    def create_application(self, before_request_hook=None, after_request_hook=None):
        app = Bottle()

        if before_request_hook is not None:
            app.add_hook("before_request", before_request_hook)

        if after_request_hook is not None:
            app.add_hook("after_request", after_request_hook)

        app.route("/runOrders", method="GET", callback=dummyCallback)

        return app