import http.cookies
import json

from http.server import BaseHTTPRequestHandler
from Core.RestServer.Actions import Actions
from Settings import DEBUG
import logging

class HttpHandler(BaseHTTPRequestHandler):

    ACTIONS = Actions()
    URLS = {
        "/core/data/get": ACTIONS.get_data,
        "/core/data/set": ACTIONS.set_data,
        "/core/data/create": ACTIONS.create_data,
        "/core/data/delete": ACTIONS.delete_data,
        "/core/data/move": ACTIONS.move_data,
        "/core/data/cleanup": ACTIONS.cleanup_data,
        "/core/data/find/path": ACTIONS.find_path,
        "/core/data/find/attr": ACTIONS.find,
        "/core/data/find/parent": ACTIONS.find_parent,
        "/core/data/find/children": ACTIONS.find_children,
        "/core/auth/login": ACTIONS.user_auth,
        "/core/auth/access": ACTIONS.user_access,
        "/core/auth/check": ACTIONS.user_check,
    }

    def read_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length).decode())
            return json.loads(post_data)
        except Exception as e:
            logging.error(e)
            return dict()

    def read_cookies(self):
        if "Cookie" in self.headers:
            c = http.cookies.SimpleCookie(self.headers["Cookie"])
            return c
        else:
            return dict()

    def send_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def success(self, data=None):
        response = dict()
        response["status"] = "OK"
        if data != None:
            response["content"] = data
        self.wfile.write(json.dumps(response).encode())

    def fail(self, data=None):
        response = dict()
        response["status"] = "NOTOK"
        if data != None:
            response["content"] = data
        self.wfile.write(json.dumps(response).encode())

    def do_GET(self):
        if DEBUG:
            self.do_POST()
        else:
            self.send_headers()
            self.fail("GET is not supported")
        return

    def do_POST(self):
        self.send_headers()

        data = self.read_data()
        cookies = self.read_cookies()

        for k in list(HttpHandler.URLS.keys()):
            if self.path.startswith(k):
                args = [x for x in k.split("/") if x]
                npaths = [x for x in self.path.split(
                    "/")[::-1] if x and x not in args]
                self.success(HttpHandler.URLS[k](npaths, data, cookies))
                return

        self.fail("operation not supported")
        return
