#!/usr/bin/python
from proxmoxer import ProxmoxAPI
from threading import Thread, Lock
from nmap import NMap
import threading
import os
from datetime import datetime, timedelta
import re
from const import PROXMOX_UPDATE_INTERVAL


class ProxmoxDaemon(Thread):
    def __init__(self, database):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.store = database
        self.setDaemon(True)
        self.lock = Lock()

    def run(self):
        while not self._stop.isSet():
            arp = NMap(self.store).get()
            all = self.store.find_by_schema("Noeud")
            i = 0
            for el in all:
                i = i+1
                thread = Thread(
                    target=self.process, args=(el, all, arp))
                thread.setDaemon(True)
                thread.start()

            self._stop.wait(PROXMOX_UPDATE_INTERVAL)

    def stop(self):
        self._stop.set()
        self.join()

    def format_bytes(self, bytes_num):
        sizes = ["B", "KB", "MB", "GB", "TB"]

        i = 0
        dblbyte = bytes_num

        while (i < len(sizes) and bytes_num >= 1024):
            dblbyte = bytes_num / 1024.0
            i = i + 1
            bytes_num = bytes_num / 1024

        return str(round(dblbyte, 2)) + " " + sizes[i]

    def format_secs(self, uptime):
        return timedelta(seconds=uptime)

    def format_pourcentage(self, number):
        return "{0:.2f}".format(number * 100) + " %"

    def process(self, id, lst, arp):
        el = lst[id]
        for k in el["__CHILDREN__"]:
            el["__CHILDREN__"][k]["Status"] = "unknown"
            el["__CHILDREN__"][k]["Uptime"] = "unknown"
            el["__CHILDREN__"][k]["CPU Usage"] = "unknown"
            el["__CHILDREN__"][k]["NB CPU"] = "unknown"
            el["__CHILDREN__"][k]["Memory"] = "unknown"
            el["__CHILDREN__"][k]["IP"] = "unknown"
        try:
            if str(el["IP"]).strip() == "" or str(el["Password"]).strip() == "" or str(el["User"]).strip() == "":
                return
            proxmox = ProxmoxAPI(str(el["IP"]).strip(), user=str(el["User"]).strip()+'@pam', password=str(el["Password"]).strip(),
                                 verify_ssl=False)
            el["Status"] = 'running'
        except:
            el["Status"] = 'stopped'
            return

        for node in proxmox.nodes.get():
            for vm in proxmox.nodes(node['node']).qemu.get():
                el["__ID__"] = node['node']
                k = dict()
                k["Status"] = vm["status"]
                k["__ID__"] = vm["name"]
                k["Uptime"] = str(self.format_secs(vm["uptime"]))
                k["CPU Usage"] = str(self.format_pourcentage(vm["cpu"]))
                k["NB CPU"] = vm["cpus"]
                k["Memory"] = self.format_bytes(
                    vm["mem"]) + " / " + self.format_bytes(vm["maxmem"])

                for i in proxmox.nodes(node['node']).qemu(vm["vmid"]).config.get():
                    if 'net' in i:
                        try:
                            k["IP"] = arp[proxmox.nodes(node['node']).qemu(
                                vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]]
                            k["Ethernet"] = i
                        except:
                            pass

                old = self.store.find_by_name(
                    vm["name"], el["__CHILDREN__"])
                if old != None:
                    (key, value) = old.items()[0]
                    value.update(k)
                    self.store.edit(id, key, value,
                                    el["__CHILDREN__"])
                else:
                    k["__CHILDREN__"] = dict()
                    k["__SCHEMA__"] = "VM"
                    self.store.add(id, k)
