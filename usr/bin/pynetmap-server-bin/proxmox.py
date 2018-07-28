#!/usr/bin/python
from proxmoxer import ProxmoxAPI
from threading import Thread, Lock
from nmap import NMap
import threading
import os
from datetime import datetime, timedelta
import re
from const import PROXMOX_UPDATE_INTERVAL
import paramiko
import select


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
                if str(all[el]["System"]) == "Proxmox":
                    thread = Thread(
                        target=self.proxmox, args=(el, all, arp))
                    thread.setDaemon(True)
                    thread.start()
                elif str(all[el]["System"]) == "Physical":
                    thread = Thread(
                        target=self.physical, args=(el, all, arp))
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

    def physical(self, id, lst, arp):
        el = lst[id]
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:

            ssh.connect(str(el["IP"]).strip(),
                        username=str(el["User"]).strip(), password=str(el["Password"]).strip())
            el["Status"] = 'running'

            nbcpus = int(self.ssh_exec_read(
                ssh, "cat /proc/cpuinfo | grep processor | wc -l"))
            totalmem = int(self.ssh_exec_read(
                ssh, "cat /proc/meminfo | grep 'MemTotal:' | cut -d' ' -f9")) * 1024
            freemem = int(self.ssh_exec_read(
                ssh, "cat /proc/meminfo | grep 'MemFree:' | cut -d' ' -f11")) * 1024
            uptime = self.ssh_exec_read(ssh, "uptime -p")

            el["Memory"] = self.format_bytes(
                totalmem-freemem) + str(" / ") + self.format_bytes(totalmem)
            el["NB CPU"] = nbcpus
            el["Uptime"] = uptime
            ssh.close()
            print " > UPDATE [ " + str(el["__ID__"]) + " :: SUCCESS ]"

        except:
            el["Status"] = 'stopped'
            print " > UPDATE [ " + str(el["__ID__"]) + " :: FAILD ]"

    def ssh_exec_read(self, ssh, cmd):
        out = ""
        ssh_stdin, stdout, ssh_stderr = ssh.exec_command(cmd, get_pty=True)
        for line in stdout.read().splitlines():
            if line != "":
                out += line

        print out
        return str(out).strip()

    def proxmox(self, id, lst, arp):
        el = lst[id]
        for k in el["__CHILDREN__"]:
            el["__CHILDREN__"][k]["Status"] = "unknown"
            el["__CHILDREN__"][k]["Uptime"] = "unknown"
            el["__CHILDREN__"][k]["CPU Usage"] = "unknown"
            el["__CHILDREN__"][k]["NB CPU"] = "unknown"
            el["__CHILDREN__"][k]["Memory"] = "unknown"
        try:
            if str(el["IP"]).strip() == "" or str(el["Password"]).strip() == "" or str(el["User"]).strip() == "":
                return
            proxmox = ProxmoxAPI(str(el["IP"]).strip(), user=str(el["User"]).strip()+'@pam', password=str(el["Password"]).strip(),
                                 verify_ssl=False)
            el["Status"] = 'running'
            print " > UPDATE [ " + str(el["__ID__"]) + " :: SUCCESS ]"
        except:
            el["Status"] = 'stopped'
            print " > UPDATE [ " + str(el["__ID__"]) + " :: FAILD ]"
            return
        for node in proxmox.nodes.get():
            el["__ID__"] = node['node']
            try:
                for vm in proxmox.nodes(node['node']).qemu.get():
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
            except:
                print "WARNING : This node is not supporting QEMU"
            try:
                for vm in proxmox.nodes(node['node']).lxc.get():
                    k = dict()
                    k["Status"] = vm["status"]
                    k["__ID__"] = vm["name"]
                    k["Uptime"] = str(self.format_secs(vm["uptime"]))
                    k["CPU Usage"] = str(self.format_pourcentage(vm["cpu"]))
                    k["NB CPU"] = vm["cpus"]
                    k["Memory"] = self.format_bytes(
                        vm["mem"]) + " / " + self.format_bytes(vm["maxmem"])

                    for i in proxmox.nodes(node['node']).lxc(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                k["IP"] = arp[proxmox.nodes(node['node']).lxc(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]]
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
                        k["__SCHEMA__"] = "Container"
                        self.store.add(id, k)
            except:
                print "WARNING : This node is not supporting LXC"
            try:
                for vm in proxmox.nodes(node['node']).openvz.get():
                    k = dict()
                    k["Status"] = vm["status"]
                    k["__ID__"] = vm["name"]
                    k["Uptime"] = str(self.format_secs(vm["uptime"]))
                    k["CPU Usage"] = str(self.format_pourcentage(vm["cpu"]))
                    k["NB CPU"] = vm["cpus"]
                    k["Memory"] = self.format_bytes(
                        vm["mem"]) + " / " + self.format_bytes(vm["maxmem"])

                    for i in proxmox.nodes(node['node']).openvz(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                k["IP"] = arp[proxmox.nodes(node['node']).openvz(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]]
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
                        k["__SCHEMA__"] = "Container"
                        self.store.add(id, k)
            except:
                print "WARNING : This node is not supporting OpenVZ"
