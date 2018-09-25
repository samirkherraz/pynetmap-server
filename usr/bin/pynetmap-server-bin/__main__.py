#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import Cookie
import json
import os
import random
import signal
import string
import sys
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from multiprocessing.managers import BaseManager
from multiprocessing import Process
from alerts import Alerts
from const import (ADMIN_PASSWORD, ADMIN_USERNAME, EXIT_ERROR_CORRUPT_DB,
                   EXIT_SUCCESS, LISTENING_PORT)
from database import Database
from Core import Core
from utils import Utils


class MyManager(BaseManager):
    pass


class Boot():
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

        MyManager.register("Database", Database)
        MyManager.register("Utils", Utils)
        MyManager.register("Alerts", Alerts)
        MyManager.register("Core", Core)
        self.shared = MyManager()
        self.shared.start()

        self.api = dict()
        try:
            self.store = self.shared.Database()
            self.store.read()
        except ValueError as e:
            Utils.debug("System::Database", "Unable to access Database"+e, 2)
            exit(EXIT_ERROR_CORRUPT_DB)
        self.change_ssh_password()
        self.utils = self.shared.Utils(self.store)
        self.alerts = self.shared.Alerts(self.store, self.utils)
        self.core = self.shared.Core(self.store, self.utils, self.alerts)
        self.engine = Process(target=self.core.run)
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
        self.engine.terminate()

    def change_ssh_password(self):
        new = ''.join(random.choice(
            string.ascii_uppercase + string.digits) for _ in range(32))
        old = self.store.get("server", "server.ssh.password")

        os.system('/bin/bash -c \'echo -e "'+old +
                  '\\n'+new+'\\n'+new+'" | passwd \'')
        self.store.set("server", "server.ssh.password", new)
        self.store.write()

    def change_file_permission(self):
        os.system("chmod 700 /var/lib/pynetmap -R")

    def user_auth(self, path, data, cookies):
        k = dict()
        access = False
        try:
            if data["username"] == ADMIN_USERNAME and data["password"] == ADMIN_PASSWORD:
                access = True

            elif data["username"] in self.store.get_table("users") and self.store.get_attr("users", data["username"], "users.password") == data["password"]:
                access = True
            else:
                access = False
        except:
            access = False

        if access == True:
            token = ''.join(random.choice(
                    string.ascii_uppercase + string.digits) for _ in range(16))
            self.store.set_attr(
                "users", data["username"], "users.token", token)
            k["TOKEN"] = token
        else:
            k["TOKEN"] = None

        return k

    def user_check(self, path, data, cookies):

        token = cookies["TOKEN"].value if "TOKEN" in cookies.keys() else None
        username = cookies["USERNAME"].value if "USERNAME" in cookies.keys(
        ) else None

        if username != None and token != None:
            if self.store.get_attr("users", username, "users.token") == token:
                return {"AUTHORIZATION": True}

        return {"AUTHORIZATION": False}

    def user_create(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
            return {"AUTHORIZATION": False}
        k = dict()
        try:
            if data["username"] not in self.store.get_table("users").keys():
                k = dict()
                k["users.password"] = data["password"]
                k["users.privilege.edit"] = data["privilege.edit"]
                k["users.privilege.terminal"] = data["privilege.terminal"]
                k["users.token"] = None
                k["users.lastname"] = data["lastname"]
                k["users.firstname"] = data["firstname"]
                k["users.privilege.manage"] = data["privilege.manage"]
                self.store.tables["users"].set(data["username"], k)
                self.store.tables["users"].write()

        except:
            pass

    def user_delete(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
            return {"AUTHORIZATION": False}
        self.store.tables["users"].delete(path[0])
        self.store.tables["users"].write()

    def tunnel_reload(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
            return {"AUTHORIZATION": False}

    def get_data(self, path, data, cookies):
        terminal = self.store.get_attr(
            "users", cookies["USERNAME"].value, "users.privilege.terminal")

        edit = self.store.get_attr(
            "users", cookies["USERNAME"].value, "users.privilege.edit")

        if len(path) == 3:
            data = self.store.get_attr(path[2], path[1], path[0])
        elif len(path) == 2:
            data = self.store.get(path[1], path[0])
        elif len(path) == 1:
            data = self.store.get_table(path[0])

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
            for key in data.keys():
                if not terminal and key in self.terminal_fields:
                    del data[key]
                elif not edit and key in self.edit_fields:
                    del data[key]
                else:
                    data[key] = self.filter(data[key], terminal, edit)

        return data

    def user_access(self, path, data, cookies):
        try:
            return {"AUTHORIZATION": self.store.get_attr("users", cookies["USERNAME"].value, path[0])}
        except:
            return {"AUTHORIZATION": False}

    def set_data(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 3:
            self.store.set_attr(path[2], path[1], path[0], data)
        elif len(path) == 2:
            self.store.set(path[1], path[0], data)
        elif len(path) == 1:
            self.store.set_table(path[0], data)
        self.store.cleanup()
        self.store.write()

    def create_data(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 2:
            return {"ID": self.store.create(path[1], path[0])}
        elif len(path) == 1:
            return {"ID": self.store.create(path[0])}
        else:
            return {"ID": self.store.create()}

        self.store.cleanup()
        self.store.write()

    def delete_data(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 2:
            self.store.delete(path[1], path[0])
        elif len(path) == 1:
            self.store.delete(None, path[0])

        self.store.cleanup()
        self.store.write()

    def cleanup_data(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        self.store.cleanup()
        self.store.write()

    def move_data(self, path, data, cookies):
        if not self.store.get_attr("users", cookies["USERNAME"].value, "users.privilege.edit"):
            return {"AUTHORIZATION": False}
        if len(path) == 2:
            self.store.move(path[1], path[0])
            return ["success"]

    def find_attr(self, path, data, cookies):
        if len(path) == 2:
            return self.store.find_by_attr(path[0], path[1])
        elif len(path) == 1:
            return self.store.find_by_attr(path[0])
        else:
            return []

    def find_schema(self, path, data, cookies):
        if len(path) == 1:
            return self.store.find_by_schema(path[0])
        else:
            return []

    def find_path(self, path, data, cookies):
        if len(path) == 1:
            return self.store.find_path(path[0])
        else:
            return []

    def find_parent(self, path, data, cookies):
        if len(path) == 1:
            return {"Parent": self.store.find_parent(path[0])}
        else:
            return {"Parent": None}

    def find_children(self, path, data, cookies):
        if len(path) == 1:
            return self.store.get_children(path[0])
        else:
            return []


class KodeFunHTTPRequestHandler(BaseHTTPRequestHandler):

    def read_data(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = json.loads(self.rfile.read(content_length))
            return json.loads(post_data)
        except:
            return dict()

    def read_cookies(self):
        if "Cookie" in self.headers:
            c = Cookie.SimpleCookie(self.headers["Cookie"])
            return c
        else:
            return dict()

    def send_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def replay(self, data):
        self.wfile.write(json.dumps(data))

    def replay_default(self):
        s = dict()
        s["STATUS"] = "OK"
        self.wfile.write(json.dumps(s))

    def do_GET(self):
        self.do_POST()

    def do_POST(self):
        self.send_headers()

        data = self.read_data()
        cookies = self.read_cookies()

        for k in Server.api.keys():
            if self.path.startswith(k):
                args = [x for x in k.split("/") if x]
                npaths = [x for x in self.path.split(
                    "/")[::-1] if x and x not in args]
                self.replay(Server.api[k](npaths, data, cookies))
                return

        self.replay_default()
        return


def run():
    Utils.debug("System::API", "HTTP Server Starting")
    server_address = ('0.0.0.0', LISTENING_PORT)
    httpd = HTTPServer(server_address, KodeFunHTTPRequestHandler)
    Utils.debug("System::API", "HTTP Server Running")
    httpd.serve_forever()


def signal_handler(signal, frame):
    Server.stop()
    exit(EXIT_SUCCESS)


if __name__ == '__main__':
    Server = Boot()
    signal.signal(signal.SIGINT, signal_handler)
    run()
