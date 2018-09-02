#!/usr/bin/python
import os
from const import TUNNEL_CORE, TUNNEL_HEADER, Debug
import subprocess
import time
import socket
import struct
from threading import Thread, Event, Lock


class Tunnel(Thread):
    def __init__(self, l):
        Thread.__init__(self)
        self.passed = dict()
        self.ips = []
        self.get_my_id()
        self.store = l
        self._stop = Event()
        self._lock = Lock()
        self.processes = dict()

    def core_writter(self, elm):
        try:
            if str(elm["base.tunnel.ip"]).strip() == "" or str(elm["base.tunnel.password"]).strip() == "" or str(
                    elm["base.tunnel.user"]).strip() == "":
                return
            for ip in self.ips:
                if ip in elm["base.tunnel.network"]:
                    return
            cmd = TUNNEL_CORE
            cmd = cmd.replace("[ID]", str(
                str(elm["base.core.name"])+"-"+str(elm["base.tunnel.network"])).replace("/", "-").strip())
            cmd = cmd.replace("[IP]", str(elm["base.tunnel.ip"]).strip())
            cmd = cmd.replace("[USER]", str(elm["base.tunnel.user"]).strip())
            cmd = cmd.replace("[PORT]", str(elm["base.tunnel.port"]).strip())
            cmd = cmd.replace("[PASS]", str(
                elm["base.tunnel.password"]).replace("'", "\\'").strip())
            cmd = cmd.replace("[NET]", str(elm["base.tunnel.network"]).strip())

        except Exception as e:

            return
        if cmd not in self.passed.keys():
            self.passed[cmd] = elm

    def get_my_id(self):
        popen = os.popen(
            " route | cut -d ' ' -f1 | grep '\\.'")
        lstr = popen.read().split("\n")
        popen.close()
        self.ips = ' '.join(lstr).split()

    def process(self, lst):
        for elm in lst.find_by_schema("Serveur"):
            (_, v) = lst.find_by_id(elm).items()[0]
            self.core_writter(v)

    def rundaemon(self, cmd):
        while not self._stop.isSet():
            Debug(self.passed[cmd]["base.core.name"], "Starting Tunnel")
            self.passed[cmd]["module.tunnel.state"] = "OK"
            os.system(cmd)
            Debug(self.passed[cmd]["base.core.name"],
                  "Failed Tunnel, retry in 30s", 2)
            self.passed[cmd]["module.tunnel.state"] = "Lost"
            self._stop.wait(30)

    def run(self):
        os.system(TUNNEL_HEADER)
        self.process(self.store)
        for cmd in self.passed.keys():
            self.processes[cmd] = Thread(
                target=self.rundaemon, args=(cmd, ))
            self.processes[cmd].start()

    def stop(self):
        with self._lock:
            self._stop.set()
            self._notify.set()
            os.system(TUNNEL_HEADER)
