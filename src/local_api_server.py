from bottle import response
from sylva_algorithm_runner.api.APIServer import APIServer

def after_request_callback():
    response.headers['Access-Control-Allow-Origin'] = '*'

server = APIServer()
app = server.create_application(after_request_hook=after_request_callback)
app.run(host='localhost', port=8080, reloader=True)
