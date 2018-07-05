#!/usr/bin/python
import os
from const import TUNNEL_CORE, TUNNEL_HEADER
import subprocess
import time
import socket
import struct


class Tunnel:
    def __init__(self, l):
        self.passed = []
        self.get_my_id()
        self.process(l)

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

    def start(self):
        os.system(TUNNEL_HEADER)
        for cmd in self.passed:
            print cmd
            os.system(cmd)

    def stop(self):
        os.system(TUNNEL_HEADER)
