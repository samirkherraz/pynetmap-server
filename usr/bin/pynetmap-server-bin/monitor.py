#!/usr/bin/python
from proxmoxer import ProxmoxAPI
from threading import Thread, Lock
from nmap import NMap
import threading
import os
from datetime import datetime, timedelta
import re
from const import UPDATE_INTERVAL, HISTORY, Debug
import paramiko
import select
import datetime
import time


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
            Debug("System", "Starting monitor thread")
            threads = []
            arp = NMap(self.store).get()
            all = self.store.find_by_schema("Noeud")
            i = 0
            for el in all:
                i = i+1
                thread = None
                if str(all[el]["base.type"]).rstrip() == "Proxmox":
                    thread = Thread(
                        target=self.proxmox, args=(el, all, arp))
                    thread.start()
                elif str(all[el]["base.type"]) == "Physical":
                    thread = Thread(
                        target=self.physical, args=(el, all, arp))
                    thread.start()
                threads.append(thread)
            for t in threads:
                try:
                    t.join(timeout=UPDATE_INTERVAL)
                except:
                    pass
            self.parent.update()
            self._stop.wait(UPDATE_INTERVAL)

    def stop(self):
        self._stop.set()
        self.join()



    def physical(self, id, lst, arp):
        el = lst[id]
        ssh = self.openssh(el)
        if ssh == None:
            Debug(el["base.core.name"], "no ssh access", 2)
            self.history_append(el, "module.history.status", 0)
            el["module.state.status"] = 'stopped'
            el["module.discover.ssh"] = "No"
        else:
            ssh.close()
            el["module.discover.ssh"] = "Yes"
            el["module.state.status"] = 'running'
            self.history_append(el, "module.history.status", 100)
            Debug(el["base.core.name"], "status is up")
            self.services(el, None)

        el["module.state.update"] = time.time()

    def history_append(self, el, key, value):
        if key not in el.keys() or type(el[key]) is not list:
            el[key] = []
        summ = 0
        i = 0
        if len(el[key]) > HISTORY:
            while len(el[key]) > HISTORY/2:
                i += 1
                summ += el[key].pop()
            if i > 0:
                el[key][0] = (el[key][0] + summ) / (i+1)
        el[key].append(value)

    def linux(self, el):
        ssh = self.openssh(el)
        if ssh == None:
            return True

        failed = False
        try:
            cmd = self.ssh_exec_read(
                ssh, """command -v sockstat""")
            if cmd == "":
                cmd = self.ssh_exec_read(
                    ssh, """apt-get update ; apt-get install coreutils sockstat procps -y""")
        except Exception as e:
            failed = True
        try:
            mem = self.ssh_exec_read(
                ssh, """vmstat -s | awk  '$0 ~ /total memory/ {total=$1 } $0 ~/free memory/ {free=$1} $0 ~/buffer memory/ {buffer=$1} $0 ~/cache/ {cache=$1} END{print (total-free-buffer-cache)/total*100}'""")
            self.history_append(el, "module.history.memory", mem)
        except Exception as e:
            failed = True

        try:
            nbcpus = int(self.ssh_exec_read(
                ssh, """cat /proc/cpuinfo | grep processor | wc -l"""))
            el["module.state.nbcpu"] = nbcpus
        except Exception as e:
            failed = True

        try:

            cpuusage = self.ssh_exec_read(
                ssh, """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}' """)
            self.history_append(
                el, "module.history.cpuusage", cpuusage)
        except Exception as e:
            failed = True

        try:
            uptime = self.ssh_exec_read(ssh, "awk '{print $1}' /proc/uptime")
            el["module.state.uptime"] = str(
                timedelta(seconds=(int(float(uptime)))))
        except Exception as e:
            failed = True

        try:
            disk = self.ssh_exec_read(
                ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '$NF=="/"{printf "%d\\n",$5}' """)
            self.history_append(el, "module.history.disk", disk)
        except Exception as e:
            failed = True

        try:
            openports = self.ssh_exec_read(
                ssh, """sockstat -l | awk 'split($5,port,":"){if( port[1] ~ "127.0.0.1") { targ="Local Only" } else { targ="WAN Interface" }} NR > 1 && NR < 15 && !seen[$2port[2]]++ {printf "%s|%s|%s\\n",toupper($2),port[2],targ } ' """)
            el["module.state.services"] = openports
        except Exception as e:
            failed = True
        try:
            mounts = self.ssh_exec_read(
                ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '(NR > 1 && $6 != "/"){printf "%s|%s / %s|%s\\n",$6,$3,$2,$5}'""")
            el["module.state.mounts"] = mounts
        except Exception as e:
            failed = True

        return failed

    def openssh(self, el):
        try:
            os.system("rm ~/.ssh/known_hosts > /dev/null 2>&1")
        except:
            pass
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            try:
                if "base.ssh.port" in el:
                    sport = int(str(el["base.ssh.port"]).strip())
                else:
                    sport = 22
            except:
                sport = 22

            ssh.connect(str(el["base.net.ip"]).strip(),
                        username=str(el["base.ssh.user"]).strip(), port=sport, password=str(el["base.ssh.password"]).strip(), timeout=5)
            return ssh
        except:
            return None

    def getos(self, el):
        ssh = self.openssh(el)
        try:
            os = self.ssh_exec_read(
                ssh, """uname""")
            el["module.discover.os"] = os
            ssh.close()
        except Exception as e:
            el["module.discover.os"] = "Unknown"

    def services(self, el, source):
        self.getos(el)

        if el["module.discover.os"] == "Linux":
            failed = self.linux(el)
        elif source != None:
            failed = self.proxmox_import(el, source)

        if failed:
            Debug(el["base.core.name"],
                  "monitoring data recived but with errors", 1)
        else:
            Debug(el["base.core.name"], "monitoring data recived", 0)

    def ssh_exec_read(self, ssh, cmd):
        out = ""
        _, stdout, _ = ssh.exec_command(cmd, get_pty=True)
        output = stdout.read()
        for line in output.splitlines():
            if line.strip() != "":
                out += line.strip() + "\n"
        return str(out).strip()

    def proxmox_import(self, el, source):
        failed = False
        try:
            mem = float(float(source["mem"]) / float(source["maxmem"])) * 100
            self.history_append(el, "module.history.memory", mem)

        except Exception as e:
            failed = True

        nbcpus = None
        try:
            nbcpus = source["cpus"]
            el["module.state.nbcpu"] = nbcpus
        except Exception as e:
            pass

        try:
            nbcpus = source["maxcpu"]
            el["module.state.nbcpu"] = nbcpus
        except Exception as e:
            pass

        failed = (nbcpus == None)

        try:
            cpuusage = float(source["cpu"]) * 100
            self.history_append(el, "module.history.cpuusage", cpuusage)
        except Exception as e:
            failed = True

        try:
            uptime = str(timedelta(seconds=(source["uptime"])))
            el["module.state.uptime"] = uptime
        except Exception as e:
            failed = True

        try:
            disk = float(float(source["disk"]) /
                         float(source["maxdisk"])) * 100
            self.history_append(el, "module.history.disk", disk)
        except Exception as e:
            failed = True

        return failed

    def proxmox(self, id, lst, arp):
        el = lst[id]
        try:
            proxmox = ProxmoxAPI(str(el["base.net.ip"]).strip(), user=str(el["base.ssh.user"]).strip()+'@pam', password=str(el["base.ssh.password"]).strip(),
                                 verify_ssl=False)
            el["module.state.status"] = 'running'
            self.history_append(el, "module.history.status", 100)
            Debug(el["base.core.name"], "proxmox api is up", 0)

        except:
            Debug(el["base.core.name"], "proxmox api is unreachable", 2)
            el["module.state.status"] = 'stopped'
            self.history_append(el, "module.history.status", 0)
            for k in el["base.core.children"]:
                el["base.core.children"][k]["module.state.status"] = "unknown"
                self.history_append(
                    el["base.core.children"][k], "module.history.status", 0)
            return
        el["module.state.update"] = time.time()
        for node in proxmox.nodes.get():
            el["base.core.name"] = node['node']
            self.services(el, node)
            try:
                for vm in proxmox.nodes(node['node']).qemu.get():
                    k = dict()
                    k["module.state.update"] = time.time()
                    k["module.state.status"] = vm["status"]
                    k["base.core.name"] = vm["name"]
                    for i in proxmox.nodes(node['node']).qemu(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                k["base.net.ip"] = arp[proxmox.nodes(node['node']).qemu(
                                    vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]]
                                k["base.net.eth"] = i
                            except:
                                pass

                    old = self.store.find_by_name(
                        vm["name"], el["base.core.children"])
                    if old != None:
                        (key, value) = old.items()[0]
                        value.update(k)
                        self.history_append(
                            value, "module.history.status", (100 if vm["status"] == "running" else 0))
                        self.services(value, vm)
                        self.store.edit(id, key, value,
                                        el["base.core.children"])
                    else:
                        k["base.core.children"] = dict()
                        k["base.core.schema"] = "VM"
                        self.store.add(id, k)
            except:
                pass

            try:
                for vm in proxmox.nodes(node['node']).lxc.get():
                    k = dict()
                    k["module.state.update"] = time.time()
                    k["module.state.status"] = vm["status"]
                    k["base.core.name"] = vm["name"]
                    for i in proxmox.nodes(node['node']).lxc(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                k["base.net.ip"] = arp[proxmox.nodes(node['node']).lxc(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]]
                                k["base.net.eth"] = i
                            except:
                                pass

                    old = self.store.find_by_name(
                        vm["name"], el["base.core.children"])
                    if old != None:
                        (key, value) = old.items()[0]
                        value.update(k)
                        self.history_append(
                            value, "module.history.status", (100 if vm["status"] == "running" else 0))
                        self.services(value, vm)
                        self.store.edit(id, key, value,
                                        el["base.core.children"])
                    else:
                        k["base.core.children"] = dict()
                        k["base.core.schema"] = "Container"
                        self.store.add(id, k)
            except:
                pass
            try:
                for vm in proxmox.nodes(node['node']).openvz.get():
                    k = dict()
                    k["module.state.update"] = time.time()
                    k["module.state.status"] = vm["status"]
                    k["base.core.name"] = vm["name"]
                    for i in proxmox.nodes(node['node']).openvz(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                k["base.net.ip"] = arp[proxmox.nodes(node['node']).openvz(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]]
                                k["base.net.eth"] = i
                            except:
                                pass

                    old = self.store.find_by_name(
                        vm["name"], el["base.core.children"])
                    if old != None:
                        (key, value) = old.items()[0]
                        value.update(k)
                        self.history_append(
                            value, "module.history.status", (100 if vm["status"] == "running" else 0))
                        self.services(value, vm)
                        self.store.edit(id, key, value,
                                        el["base.core.children"])
                    else:
                        k["base.core.children"] = dict()
                        k["base.core.schema"] = "Container"
                        self.store.add(id, k)

            except:
                pass
