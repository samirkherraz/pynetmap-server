#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
from database import Database
from monitor import MonitorDaemon
from tunnel import Tunnel
from const import Debug, ADMIN_PASSWORD, ADMIN_USERNAME, LISTENING_PORT, EXIT_ERROR_CORRUPT_DB, EXIT_ERROR_LOCK, EXIT_SUCCESS
import signal
import Cookie
import string
import random
import time
import json
import sys

import ssl


class Boot:
    def __init__(self):
        self.last_data_timestamp = time.time()
        self.last_schema_timestamp = time.time()
        self.tokens = []
        self.api = dict()
        try:
            self.store = Database()
            self.store.read()
        except:
            Debug("System", "Unable to access Database", 2)
            exit(EXIT_ERROR_CORRUPT_DB)
        self.tunnel = Tunnel(self.store)
        self.tunnel.start()
        self.proxmox = MonitorDaemon(self)
        self.proxmox.start()
        self.register_action("/core/data/base/get", self.get_base)
        self.register_action("/core/data/base/set", self.set_base)
        self.register_action("/core/data/state/get", self.get_history)
        self.register_action("/core/data/alert/get", self.get_history)
        self.register_action("/core/schema/get", self.get_schema)
        self.register_action("/core/schema/set", self.set_schema)
        self.register_action("/core/auth", self.auth)

    def register_action(self, path, callback):
        self.api[path] = callback

    def auth(self, username, password):

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            token = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(16))
            self.tokens.append(token)
            return token
        else:
            return None

    def update(self):
        self.last_data_timestamp = time.time()

    def stop(self):
        self.tunnel.stop()
        self.proxmox.stop()

    def get_schema(self, path, data):
        return self.store._schema

    def set_schema(self, path, data):
        self.store.replace_schema(data)
        self.store.write()
        self.last_schema_timestamp = time.time()

    def get_base(self, path, data):
        if len(path) > 1 and path[1] == "get":
            (k, value) = self.store.get_persistant(
                self.store.find_by_id(path[0])).items()[0]
            value = value.copy()
            del value["base.core.children"]
            return value
        else:
            return self.store.get_persistant()

    def set_base(self, path, data):
        if len(path) > 1 and path[1] == "set":
            (key, value) = self.store.find_by_id(path[0]).items()[0]
            value.update(data)
            self.store.edit(self.store.find_parent(key), key, value)
        else:
            self.store.replace_data(data)
        self.store.write()
        self.last_data_timestamp = time.time()
        # self.tunnel.notify()

    def get_history(self, path, data):
        if len(path) > 1 and path[1] == "get":
            (k, value) = self.store.get_volatile(
                self.store.find_by_id(path[0])).items()[0]
            value = value.copy()
            del value["base.core.children"]
            return value
        else:
            return self.store.get_volatile()

    def last_data_update(self):
        return self.last_data_timestamp

    def last_schema_update(self):
        return self.last_schema_timestamp


class KodeFunHTTPRequestHandler(BaseHTTPRequestHandler):

    def read_data(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        return json.loads(post_data)

    def verify_con(self):
        return True
        if "Cookie" in self.headers:
            c = Cookie.SimpleCookie(self.headers["Cookie"])
            if c['TOKEN'].value in Server.tokens:
                return True
        return False

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
        self.send_headers()
        npaths = [x for x in self.path.split("/")[::-1] if x]
        try:
            data = self.read_data()
        except:
            data = None
        for k in Server.api.keys():
            if self.path.startswith(k):
                self.replay(Server.api[k](npaths, data))

        if npaths[0] == ("auth"):
            data = self.read_data()
            token = Server.auth(data["username"], data["password"])
            if token == None:
                self.replay({"TOKEN": None})
            else:
                self.replay({"TOKEN": token})

        elif npaths[0] == ("auth_check"):
            if self.verify_con():
                self.replay({"AUTHORIZATION": True})
            else:
                self.replay({"AUTHORIZATION": False})

        elif npaths[0] == ("state_check"):
            out = dict()
            out["TIMESTAMP"] = time.time()
            out["ACTIONS"] = []
            timestamp = self.read_data()["TIMESTAMP"]
            if not self.verify_con():
                out["ACTIONS"].append("AUTH")
            if Server.last_data_update() > timestamp:
                out["ACTIONS"].append("DATA")
            if Server.last_schema_update() > timestamp:
                out["ACTIONS"].append("SCHEMA")

            self.replay(out)
        elif self.path.endswith("reload"):
            if self.verify_con():
                Server.tunnel.notify()
                self.replay({"STATUS": "OK"})
            else:
                self.replay({"AUTHORIZATION": False})

        return


def run():
    Debug("System", "HTTP Server Starting")
    server_address = ('0.0.0.0', LISTENING_PORT)
    httpd = HTTPServer(server_address, KodeFunHTTPRequestHandler)
    httpd.socket = ssl.wrap_socket(httpd.socket,
                                   keyfile="/etc/pynetmap-server/server.key",
                                   certfile="/etc/pynetmap-server/server.crt", server_side=True)

    Debug("System", "HTTP Server Running")
    httpd.serve_forever()


def signal_handler(signal, frame):
    Server.stop()
    exit(EXIT_SUCCESS)


if __name__ == '__main__':
    Server = Boot()
    signal.signal(signal.SIGINT, signal_handler)
    run()
