#!/usr/bin/env python

from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
import os
from database import Database
from proxmox import ProxmoxDaemon
from tunnel import Tunnel
from const import ADMIN_PASSWORD, ADMIN_USERNAME, LISTENING_PORT, EXIT_ERROR_CORRUPT_DB, EXIT_ERROR_LOCK, EXIT_SUCCESS
import signal
import Cookie
import string
import random
import time
import json
import sys


class Boot:
    def __init__(self):
        self.tokens = []
        try:
            self.store = Database()
            self.store.read()
        except:
            print "ERROR: Unable to access to database, wrong GPG key"
            exit(EXIT_ERROR_CORRUPT_DB)
        self.tunnel = Tunnel(self.store)
        self.tunnel.start()
        self.proxmox = ProxmoxDaemon(self.store)
        self.proxmox.start()

    def auth(self, username, password):

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            token = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(16))
            self.tokens.append(token)
            return token
        else:
            return None

    def stop(self):
        self.tunnel.stop()
        self.proxmox.stop()

    def pull_data(self):
        return self.store._head

    def pull_schema(self):
        return self.store._schema

    def push_data(self, data):
        self.store.replace_data(data)
        self.store.write()

    def push_schema(self, data):
        self.store.replace_schema(data)
        self.store.write()

    def last_data_update(self):
        return self.store.last_data_timestamp()

    def last_schema_update(self):
        return self.store.last_schema_timestamp()


class KodeFunHTTPRequestHandler(BaseHTTPRequestHandler):

    def read_data(self):
        content_length = int(self.headers['Content-Length'])
        post_data = json.loads(self.rfile.read(content_length))
        return json.loads(post_data)

    def verify_con(self):
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

    def do_POST(self):
        self.send_headers()
        if self.path.endswith("push_data"):
            if self.verify_con():
                data = self.read_data()
                Server.push_data(data)
                self.replay({"STATUS": "OK"})
            else:
                self.replay({"AUTHORIZATION": False})
        elif self.path.endswith("push_schema"):
            if self.verify_con():
                data = self.read_data()
                Server.push_schema(data)
                self.replay({"STATUS": "OK"})
            else:
                self.replay({"AUTHORIZATION": False})

        elif self.path.endswith("auth"):
            data = self.read_data()
            token = Server.auth(data["username"], data["password"])
            if token == None:
                self.replay({"TOKEN": None})
            else:
                self.replay({"TOKEN": token})

        elif self.path.endswith("auth_check"):
            if self.verify_con():
                self.replay({"AUTHORIZATION": True})
            else:
                self.replay({"AUTHORIZATION": False})
        elif self.path.endswith("state_check"):
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
        elif self.path.endswith("pull_data"):
            if self.verify_con():
                self.replay(Server.pull_data())
            else:
                self.replay({"AUTHORIZATION": False})
        elif self.path.endswith("pull_schema"):
            if self.verify_con():
                self.replay(Server.pull_schema())
            else:
                self.replay({"AUTHORIZATION": False})

        return


def run():
    print('http server is starting...')
    server_address = ('0.0.0.0', LISTENING_PORT)
    httpd = HTTPServer(server_address, KodeFunHTTPRequestHandler)
    print('http server is running...')
    httpd.serve_forever()


def signal_handler(signal, frame):
    Server.stop()
    exit(EXIT_SUCCESS)


if __name__ == '__main__':
    Server = Boot()
    signal.signal(signal.SIGINT, signal_handler)
    run()
