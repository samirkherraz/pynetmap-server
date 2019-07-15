import http.cookies
import json

from http.server import BaseHTTPRequestHandler
from Core.RestServer.Actions import Actions
from Constants import *
import logging

class HttpHandler(BaseHTTPRequestHandler):

    ACTIONS = Actions()
    URLS = {
        "/data/get": (True,None, ACTIONS.get_data),
        "/data/set": (True,"edit", ACTIONS.set_data),
        "/data/create": (True,"edit",ACTIONS.create_data),
        "/data/delete": (True,"edit",ACTIONS.delete_data),
        "/data/move": (True,"edit",ACTIONS.move_data),
        "/data/cleanup": (True,"edit",ACTIONS.cleanup_data),
        "/data/find/path": (True, None,ACTIONS.find_path),
        "/data/find/attr": (True,None,ACTIONS.find),
        "/data/find/parent": (True,None,ACTIONS.find_parent),
        "/data/find/children": (True,None,ACTIONS.find_children),
        #"/auth/create": (True,"manage",ACTIONS.user_create),
        "/auth/login": (False,None,ACTIONS.user_auth),
        "/auth/access": (True,None,ACTIONS.user_access),
        "/auth/check": (True,None,ACTIONS.user_auth_check),
        "/ping": (False,None,ACTIONS.ping),
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
                (login, privilege, fn) = HttpHandler.URLS[k]
                if login and not HttpHandler.ACTIONS.user_check(cookies):
                    self.fail({"AUTHORIZATION": False})
                    return
                if privilege is not None and HttpHandler.ACTIONS.user_privilege(cookies,privilege):
                    self.fail({"AUTHORIZATION": False})
                    return  
                self.success(fn(npaths, data, cookies))
                return

        self.fail("operation not supported")
        return
