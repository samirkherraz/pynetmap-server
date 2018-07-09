#!/usr/bin/python
import os
from const import TUNNEL_CORE, TUNNEL_HEADER
import subprocess
import time
import socket
import struct
from threading import Thread, Event


class Tunnel(Thread):
    def __init__(self, l):
        Thread.__init__(self)
        self.passed = []
        self.ips = []
        self.get_my_id()
        self.store = l
        self._stop = Event()
        self._notify = Event()

    def core_writter(self, elm):
        try:
            if str(elm["Tunnel IP"]).strip() == "" or str(elm["Tunnel Password"]).strip() == "" or str(
                    elm["Tunnel User"]).strip() == "":
                return
            for ip in self.ips:
                if ip in elm["Tunnel Network"]:
                    return
            cmd = TUNNEL_CORE
            cmd = cmd.replace("[ID]", str(
                elm["Tunnel Network"]).replace("/", "-").strip())
            cmd = cmd.replace("[IP]", str(elm["Tunnel IP"]).strip())
            cmd = cmd.replace("[USER]", str(elm["Tunnel User"]).strip())
            cmd = cmd.replace("[PORT]", str(elm["Tunnel SSH Port"]).strip())
            cmd = cmd.replace("[PASS]", str(
                elm["Tunnel Password"]).replace("'", "\\'").strip())
            inet = []
            try:
                for ielm in elm["__CHILDREN__"]:
                    inet.append(elm["__CHILDREN__"][ielm]["IP"])
            except:
                print "OIPS"
                return
            cmd = cmd.replace("[NET]", str(elm["Tunnel Network"]).strip())

        except:
            return
        if cmd not in self.passed:
            self.passed.append(cmd)

    def get_my_id(self):
        lstr = os.popen(
            " route | cut -d ' ' -f1 | grep '\\.'").read().split("\n")
        self.ips = ' '.join(lstr).split()

    def process(self, lst):
        for elm in lst.find_by_schema("Serveur"):
            self.core_writter(lst.find_by_id(elm))

    def run(self):
        while not self._stop.isSet():
            self.process(self.store)
            os.system(TUNNEL_HEADER)
            for cmd in self.passed:
                print cmd
                os.system(cmd)
            self._notify.wait()
            self._notify.clear()

    def notify(self):
        self._notify.set()

    def stop(self):
        self._stop.set()
        self._notify.set()
        os.system(TUNNEL_HEADER)
