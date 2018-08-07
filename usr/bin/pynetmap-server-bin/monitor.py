#!/usr/bin/python
from proxmoxer import ProxmoxAPI
from threading import Thread, Lock
from nmap import NMap
import threading
import os
from datetime import datetime, timedelta
import re
from const import UPDATE_INTERVAL
import paramiko
import select


class MonitorDaemon(Thread):
    def __init__(self, parent):
        Thread.__init__(self)
        self._stop = threading.Event()
        self.store = parent.store
        self.parent = parent
        self.setDaemon(True)
        self.lock = Lock()

    def run(self):
        while not self._stop.isSet():
            threads = []
            arp = NMap(self.store).get()
            all = self.store.find_by_schema("Noeud")
            i = 0
            for el in all:
                i = i+1
                thread = None
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

                threads.append(thread)

            for t in threads:
                try:
                    t.join()
                except:
                    pass

            self.parent.update()
            self._stop.wait(UPDATE_INTERVAL)

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
            ssh.close()
            self.services(el)
            print "> [ " + str(el["__ID__"]) + " :: SUCCESS ]"

        except:
            el["Status"] = 'stopped'
            print "> [ " + str(el["__ID__"]) + " :: FAILD   ]"

    def services(self, el):
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:

            ssh.connect(str(el["IP"]).strip(),
                        username=str(el["User"]).strip(), password=str(el["Password"]).strip())

            el["Status"] = 'running'

            cpuusage = self.ssh_exec_read(
                ssh, "grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}' ")

            openports = self.ssh_exec_read(
                ssh, 'netstat -lt4p | grep -oh "0.0.0.0:\w\w*" ').replace("0.0.0.0:", "")

            mounts = self.ssh_exec_read(
                ssh, 'df -h |  grep -v "tmpfs" | grep -v "rootfs" |  grep -v "/$" | grep -oh "[0-9][0-9]*% .*" | grep -v "/dev"  | sed -e "s/ /\t/g"')

            disk = self.ssh_exec_read(
                ssh, 'df -h | grep -v "tmpfs" | grep -v "rootfs" |  grep "/$" | grep -oh "[0-9][0-9]*%" | grep -v "/dev" ')

            nbcpus = int(self.ssh_exec_read(
                ssh, "cat /proc/cpuinfo | grep processor | wc -l"))
            mem = self.ssh_exec_read(
                ssh, "free | grep Mem | awk '{print ($2-$7)/$2 * 100.0}'")
            uptime = self.ssh_exec_read(ssh, "uptime | cut -d',' -f1")
            ssh.close()

            if "CPU Usage" not in el.keys() or type(el["CPU Usage"]) is not list:
                el["CPU Usage"] = []

            if "Disk" not in el.keys() or type(el["Disk"]) is not list:
                el["Disk"] = []

            if "Memory" not in el.keys() or type(el["Memory"]) is not list:
                el["Memory"] = []

            while len(el["CPU Usage"]) > 100:
                el["CPU Usage"].pop()

            while len(el["Memory"]) > 100:
                el["Memory"].pop()

            while len(el["Disk"]) > 100:
                el["Disk"].pop()

            el["Memory"].append(mem)

            el["CPU Usage"].append(cpuusage)
            el["Disk"].append(disk)

            el["NB CPU"] = nbcpus
            el["Uptime"] = uptime
            el["Listning Ports"] = openports
            el["Mounts"] = mounts

        except:
            print "> [ " + str(el["__ID__"]) + " :: NO SSH ACCESS   ]"

    def ssh_exec_read(self, ssh, cmd):
        out = ""
        ssh_stdin, stdout, ssh_stderr = ssh.exec_command(cmd, get_pty=True)
        output = stdout.read()
        if "command not found" in output:
            ssh_stdin, stdout, ssh_stderr = ssh.exec_command(
                'apt-get update && apt-get install net-tools -y ', get_pty=True)
            for line in stdout.read().splitlines():
                print line
            return self.ssh_exec_read(ssh, cmd)
        for line in output.splitlines():
            if line.strip() != "":
                out += line.strip() + "\n"

        return str(out).strip()

    def proxmox(self, id, lst, arp):
        el = lst[id]
        for k in el["__CHILDREN__"]:
            el["__CHILDREN__"][k]["Status"] = "unknown"
        try:
            if str(el["IP"]).strip() == "" or str(el["Password"]).strip() == "" or str(el["User"]).strip() == "":
                return
            proxmox = ProxmoxAPI(str(el["IP"]).strip(), user=str(el["User"]).strip()+'@pam', password=str(el["Password"]).strip(),
                                 verify_ssl=False)
            el["Status"] = 'running'
            self.services(el)
            print "> [ " + str(el["__ID__"]) + " :: SUCCESS ]"
        except:
            el["Status"] = 'stopped'
            print "> [ " + str(el["__ID__"]) + " :: FAILED  ]"
            return
        for node in proxmox.nodes.get():
            el["__ID__"] = node['node']
            try:
                for vm in proxmox.nodes(node['node']).qemu.get():
                    k = dict()
                    k["Status"] = vm["status"]
                    k["__ID__"] = vm["name"]

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
                        self.services(value)
                        self.store.edit(id, key, value,
                                        el["__CHILDREN__"])
                    else:
                        k["__CHILDREN__"] = dict()
                        k["__SCHEMA__"] = "VM"
                        self.store.add(id, k)
                    print ">    [ " + str(k["__ID__"]) + " :: SUCCESS ]"
            except:
                pass
            try:
                for vm in proxmox.nodes(node['node']).lxc.get():
                    k = dict()
                    k["Status"] = vm["status"]
                    k["__ID__"] = vm["name"]

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
                        self.services(value)
                        self.store.edit(id, key, value,
                                        el["__CHILDREN__"])
                    else:
                        k["__CHILDREN__"] = dict()
                        k["__SCHEMA__"] = "Container"
                        self.store.add(id, k)
                    print ">    [ " + str(k["__ID__"]) + " :: SUCCESS ]"
            except:
                pass
            try:
                for vm in proxmox.nodes(node['node']).openvz.get():
                    k = dict()
                    k["Status"] = vm["status"]
                    k["__ID__"] = vm["name"]

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
                        self.services(value)
                        self.store.edit(id, key, value,
                                        el["__CHILDREN__"])
                    else:
                        k["__CHILDREN__"] = dict()
                        k["__SCHEMA__"] = "Container"
                        self.store.add(id, k)

                    print ">    [ " + str(k["__ID__"]) + " :: SUCCESS ]"
            except:
                pass
