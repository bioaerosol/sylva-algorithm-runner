from bottle import request, response
from sylva_algorithm_runner_frontend.Server import Server

def after_request_callback():
    response.headers['Access-Control-Allow-Origin'] = '*'

server = Server()
app = server.create_application(after_request_hook=after_request_callback)
app.run(host='localhost', port=8080, reloader=True)
