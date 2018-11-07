#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import http.cookies
import json
import os
import random
import signal
import string
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from threading import Thread

from const import (ADMIN_PASSWORD, ADMIN_USERNAME, LISTENING_PORT)
from Core import Core
from utils import Utils
from error import EXIT_SUCCESS


class RequestManager():
    def __init__(self):
        self.terminal_fields = []
        self.terminal_fields.append("base.ssh.password")
        self.terminal_fields.append("base.ssh.user")
        self.terminal_fields.append("base.ssh.port")
        self.terminal_fields.append("base.tunnel.port")
        self.terminal_fields.append("base.tunnel.user")
        self.terminal_fields.append("base.tunnel.network")
        self.terminal_fields.append("base.tunnel.password")
        self.terminal_fields.append("server.ssh.password")
        self.terminal_fields.append("server.ssh.user")
        self.terminal_fields.append("server.ssh.port")
        self.edit_fields = []
        self.edit_fields.append("base.ssh.password")
        self.edit_fields.append("base.ssh.user")
        self.edit_fields.append("base.ssh.port")
        self.edit_fields.append("base.tunnel.port")
        self.edit_fields.append("base.tunnel.user")
        self.edit_fields.append("base.tunnel.network")
        self.edit_fields.append("base.tunnel.password")
        self.edit_fields.append("alert.required_fields")

        self.api = dict()
        self.core = Core()
        self.core.model.utils.change_ssh_password()
        self.engine = Thread(target=self.core.run)
        self.engine.daemon = True
        self.engine.start()
        self.register_action("/core/data/get", self.get_data)
        self.register_action("/core/data/set", self.set_data)
        self.register_action("/core/data/create", self.create_data)
        self.register_action("/core/data/delete", self.delete_data)
        self.register_action("/core/data/move", self.move_data)
        self.register_action("/core/data/cleanup", self.cleanup_data)
        self.register_action("/core/data/find/path", self.find_path)
        self.register_action("/core/data/find/attr", self.find_attr)
        self.register_action("/core/data/find/schema", self.find_schema)
        self.register_action("/core/data/find/parent", self.find_parent)
        self.register_action("/core/data/find/children", self.find_children)
        self.register_action("/core/auth/login", self.user_auth)
        self.register_action("/core/auth/access", self.user_access)
        self.register_action("/core/auth/check", self.user_check)
        self.register_action("/core/tunnel/reload", self.tunnel_reload)

    def register_action(self, path, callback):
        self.api[path] = callback

    def stop(self):
        pass

    def change_file_permission(self):
        os.system("chmod 700 /var/lib/pynetmap -R")

    def user_auth(self, path, data, cookies):
        k = dict()
        access = False
        try:
            if data["username"] == ADMIN_USERNAME and data["password"] == ADMIN_PASSWORD:
                access = True

            elif data["username"] in self.core.model.store.get_table("users") and self.core.model.store.get_attr("users", data["username"], "users.password") == data["password"]:
                access = True
            else:
                access = False
        except ValueError as e:
            access = False

        if access == True:
            token = ''.join(random.choice(
                    string.ascii_uppercase + string.digits) for _ in range(16))
            self.core.model.store.set_attr(
                "users", data["username"], "users.token", token)
            k["TOKEN"] = token
        else:
            k["TOKEN"] = None

        return k

    def user_check(self, path, data, cookies):

        token = cookies["TOKEN"].value if "TOKEN" in list(
            cookies.keys()) else None
        username = cookies["USERNAME"].value if "USERNAME" in list(cookies.keys(
        )) else None

        if username != None and token != None:
            if self.core.model.store.get_attr("users", username, "users.token") == token:
                return {"AUTHORIZATION": True}

        return {"AUTHORIZATION": False}

    def user_create(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
            return {"AUTHORIZATION": False}
        k = dict()
        try:
            if data["username"] not in list(self.core.model.store.get_table("users").keys()):
                k = dict()
                k["users.password"] = data["password"]
                k["users.privilege.edit"] = data["privilege.edit"]
                k["users.privilege.terminal"] = data["privilege.terminal"]
                k["users.token"] = None
                k["users.lastname"] = data["lastname"]
                k["users.firstname"] = data["firstname"]
                k["users.privilege.manage"] = data["privilege.manage"]
                self.core.model.store.tables["users"].set(data["username"], k)
                self.core.model.store.tables["users"].write()

        except:
            pass

    def user_delete(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
            return {"AUTHORIZATION": False}
        self.core.model.store.tables["users"].delete(path[0])
        self.core.model.store.tables["users"].write()

    def tunnel_reload(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
            return {"AUTHORIZATION": False}

    def get_data(self, path, data, cookies):
        terminal = self.core.model.store.get_attr(
            "users", cookies["USERNAME"].value, "users.privilege.terminal")

        edit = self.core.model.store.get_attr(
            "users", cookies["USERNAME"].value, "users.privilege.edit")

        if len(path) == 3:
            data = self.core.model.store.get_attr(path[2], path[1], path[0])
        elif len(path) == 2:
            data = self.core.model.store.get(path[1], path[0])
        elif len(path) == 1:
            data = self.core.model.store.get_table(path[0])

        else:
            data = dict()

        return self.filter(data, terminal, edit, path)

    def filter(self, data, terminal, edit, path=None):
        if path != None:
            for key in path:
                if not terminal and key in self.terminal_fields:
                    return None
                elif not edit and key in self.edit_fields:
                    return None
            if type(data) is dict:
                data = data.copy()
        if type(data) is dict:
            for key in list(data.keys()):
                if not terminal and key in self.terminal_fields:
                    del data[key]
                elif not edit and key in self.edit_fields:
                    del data[key]
                else:
                    data[key] = self.filter(data[key], terminal, edit)

        return data

    def user_access(self, path, data, cookies):
        try:
            return {"AUTHORIZATION": self.core.model.store.get_attr("users", cookies["USERNAME"].value, path[0])}
        except:
            return {"AUTHORIZATION": False}

    def set_data(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 3:
            self.core.model.store.set_attr(path[2], path[1], path[0], data)
        elif len(path) == 2:
            self.core.model.store.set(path[1], path[0], data)
        elif len(path) == 1:
            self.core.model.store.set_table(path[0], data)
        self.core.model.store.cleanup()
        self.core.model.store.write()

    def create_data(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 2:
            return {"ID": self.core.model.store.create(path[1], path[0])}
        elif len(path) == 1:
            return {"ID": self.core.model.store.create(path[0])}
        else:
            return {"ID": self.core.model.store.create()}

        self.core.model.store.cleanup()
        self.core.model.store.write()

    def delete_data(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 2:
            self.core.model.store.delete(path[1], path[0])
        elif len(path) == 1:
            self.core.model.store.delete(None, path[0])

        self.core.model.store.cleanup()
        self.core.model.store.write()

    def cleanup_data(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        self.core.model.store.cleanup()
        self.core.model.store.write()

    def move_data(self, path, data, cookies):
        if not self.core.model.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 2:
            self.core.model.store.move(path[1], path[0])
            return ["success"]

    def find_attr(self, path, data, cookies):
        if len(path) == 2:
            return self.core.model.store.find_by_attr(path[0], path[1])
        elif len(path) == 1:
            return self.core.model.store.find_by_attr(path[0])
        else:
            return []

    def find_schema(self, path, data, cookies):
        if len(path) == 1:
            return self.core.model.store.find_by_schema(path[0])
        else:
            return []

    def find_path(self, path, data, cookies):
        if len(path) == 1:
            return self.core.model.store.find_path(path[0])
        else:
            return []

    def find_parent(self, path, data, cookies):
        if len(path) == 1:
            return {"Parent": self.core.model.store.find_parent(path[0])}
        else:
            return {"Parent": None}

    def find_children(self, path, data, cookies):
        if len(path) == 1:
            return self.core.model.store.get_children(path[0])
        else:
            return []


class RequestHandler(BaseHTTPRequestHandler):

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

    def send_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def replay(self, data):
        self.wfile.write(json.dumps(data).encode())

    def replay_default(self):
        s = dict()
        s["STATUS"] = "OK"
        self.wfile.write(json.dumps(s).encode())

    def do_GET(self):
        self.send_headers()
        self.replay_default()
        return 
    def do_POST(self):
        self.send_headers()

        data = self.read_data()
        cookies = self.read_cookies()

        for k in list(Server.api.keys()):
            if self.path.startswith(k):
                args = [x for x in k.split("/") if x]
                npaths = [x for x in self.path.split(
                    "/")[::-1] if x and x not in args]
                self.replay(Server.api[k](npaths, data, cookies))
                return

        self.replay_default()
        return


Server = RequestManager()


def signal_handler(signal, frame):
    Server.stop()
    exit(EXIT_SUCCESS)


def run():
    Utils.debug("System::API", "HTTP Server Starting")
    server_address = ('0.0.0.0', LISTENING_PORT)
    httpd = HTTPServer(server_address, RequestHandler)
    Utils.debug("System::API", "HTTP Server Running")
    signal.signal(signal.SIGINT, signal_handler)
    httpd.serve_forever()
