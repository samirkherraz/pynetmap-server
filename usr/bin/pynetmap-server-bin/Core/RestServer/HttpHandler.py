import http.cookies
import json
from http.server import BaseHTTPRequestHandler

from Constants import *
from Core.RestServer.Actions import Actions
from Core.Utils.Logging import getLogger

logging = getLogger(__package__)


class HttpHandler(BaseHTTPRequestHandler):

    URLS = {

        "/data/get/"+DB_SERVER: (True, "terminal", "get_data", 1),
        "/data/set/"+DB_SERVER: (True, "terminal", "set_data", 1),
        "/data/rm/"+DB_SERVER: (True, "terminal", "rm_data", 1),

        "/data/get/"+DB_USERS: (True, "manage", "get_data", 1),
        "/data/set/"+DB_USERS: (True, "manage", "set_data", 1),
        "/data/rm/"+DB_USERS: (True, "manage", "rm_data", 1),

        "/data/get": (True, None, "get_data", 0),
        "/data/set": (True, "edit", "set_data", 0),
        "/data/rm": (True, "edit", "rm_data", 0),

        "/data/create": (True, "edit", "create_data", 0),
        "/data/delete": (True, "edit", "delete_data", 0),
        "/data/move": (True, "edit", "move_data", 0),

        "/data/cleanup": (True, "edit", "cleanup_data", 0),

        "/data/find/path": (True, None, "find_path", 0),
        "/data/find/attr": (True, None, "find", 0),
        "/data/find/parent": (True, None, "find_parent", 0),
        "/data/find/children": (True, None, "find_children", 0),

        "/auth/access": (True, None, "user_access", 0),
        "/auth/check": (True, None, "user_auth_check", 0),
        "/auth/login": (False, None, "user_auth", 0),

        "/ping": (False, None, "ping", 0),
    }

    def read_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length).decode())
            return json.loads(post_data)
        except:
            return dict()

    def read_cookies(self):
        if "Cookie" in self.headers:
            c = http.cookies.SimpleCookie(self.headers["Cookie"])
            return c
        else:
            return dict()

    def send_headers(self, status=200):
        self.send_response(status)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def success(self, data=None):
        self.send_headers()
        response = dict()
        response["status"] = "OK"
        if data != None:
            response["content"] = data
        self.wfile.write(json.dumps(response).encode())

    def fail(self, data=None, status=403):
        self.send_headers(status)
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

        data = self.read_data()
        cookies = self.read_cookies()

        for k in list(HttpHandler.URLS.keys()):
            if self.path.startswith(k):
                (login, privilege, fn, revpath) = HttpHandler.URLS[k]
                args = [x for x in k.split("/") if x][::-1]
                npaths = []
                for i in range(revpath):
                    npaths.append(args[i])
                for x in self.path.split("/"):
                    if x and x not in args:
                        npaths.append(x)
                act = Actions(npaths, data, cookies)
                if not DEBUG:
                    if login and not act.user_check():
                        self.fail({"AUTHORIZATION": False})
                        return
                    if privilege is not None and not act.user_privilege(privilege):
                        self.fail({"AUTHORIZATION": False})
                        return
                try:
                    method = getattr(act, fn)
                    logging.info(f'CALL TO FUNCTION {fn}')
                    self.success(method())
                except Exception as e:
                    logging.error(e)
                    self.fail("Serveur Error")
                return

        self.fail("operation not supported")
        return
