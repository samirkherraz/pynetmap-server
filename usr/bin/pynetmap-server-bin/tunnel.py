#!/usr/bin/python
import os
from const import TUNNEL_CORE, TUNNEL_HEADER
import subprocess
import time
import socket
import struct
from threading import Thread, Event, Lock
from utils import Utils


class Tunnel(Thread):
    def __init__(self, ui):
        Thread.__init__(self)
        self.passed = dict()
        self.ips = []
        self.get_my_id()
        self.ui = ui
        self._stop = Event()
        self._notify = Event()
        self._lock = Lock()

    def process(self, id):
        while not self._stop.isSet():
            try:
                elm = self.ui.store.get("base", id)
                if str(elm["base.tunnel.ip"]).strip() == "" or str(elm["base.tunnel.password"]).strip() == "" or str(
                        elm["base.tunnel.user"]).strip() == "":
                    Utils.debug(
                        elm["base.name"], "Some required fields for tunnel are missing", 2)
                    return
                for ip in self.ips:
                    if ip in elm["base.tunnel.network"]:
                        Utils.debug(
                            elm["base.name"], "Can't tunnel to LAN", 2)
                        return
                cmd = TUNNEL_CORE
                cmd = cmd.replace("[ID]", str(
                    str(elm["base.name"])+"-"+str(elm["base.tunnel.network"])).replace("/", "-").strip())
                cmd = cmd.replace("[IP]", str(elm["base.tunnel.ip"]).strip())
                cmd = cmd.replace("[USER]", str(
                    elm["base.tunnel.user"]).strip())
                cmd = cmd.replace("[PORT]", str(
                    elm["base.tunnel.port"]).strip())
                cmd = cmd.replace("[PASS]", str(
                    elm["base.tunnel.password"]).replace("'", "\\'").strip())
                cmd = cmd.replace("[NET]", str(
                    elm["base.tunnel.network"]).strip())

            except Exception as e:
                Utils.debug(
                    elm["base.name"], "Some required fields for tunnel are missing", 2)
                return
            with self._lock:
                if cmd in self.passed.keys():
                    Utils.debug(elm["base.name"], "Tunnel already started", 1)
                    return
                else:
                    self.passed[cmd] = id
            Utils.debug(elm["base.name"], "Starting Tunnel")
            self.ui.store.set_attr("base", id, "module.state.tunnel", "Yes")
            os.system(cmd)
            with self._lock:
                del self.passed[cmd]
            Utils.debug(elm["base.name"],
                        "Failed Tunnel, retry in 2 minutes", 2)
            self.ui.store.set_attr("base", id, "module.state.tunnel", "No")
            self._stop.wait(120)

    def get_my_id(self):
        popen = os.popen(
            " route | cut -d ' ' -f1 | grep '\\.'")
        lstr = popen.read().split("\n")
        popen.close()
        self.ips = ' '.join(lstr).split()

    def run(self):
        os.system(TUNNEL_HEADER)
        while not self._stop.isSet():
            Utils.debug("System",
                        "Tunnel notification received, restarting")
            for key in self.ui.store.find_by_schema("Serveur"):
                prc = Thread(
                    target=self.process, args=(key, ))
                prc.start()
            self._notify.wait()
            with self._lock:
                self._notify.clear()

    def notify(self, kill=False):
        with self._lock:
            if kill:
                os.system(TUNNEL_HEADER)
            self._notify.set()

    def stop(self):
        with self._lock:
            self._stop.set()
            os.system(TUNNEL_HEADER)
