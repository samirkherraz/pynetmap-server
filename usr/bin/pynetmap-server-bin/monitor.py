#!/usr/bin/python
from proxmoxer import ProxmoxAPI
from threading import Thread, Lock
from nmap import NMap
import threading
import os
from datetime import datetime, timedelta
import re
from const import UPDATE_INTERVAL, HISTORY
import paramiko
import select
import datetime


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
                    thread.start()
                elif str(all[el]["System"]) == "Physical":
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
        try:
            os.system("rm ~/.ssh/known_hosts")
        except:
            pass
        el = lst[id]
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            try:
                if "PORT" in el:
                    sport = int(str(el["PORT"]).strip())
                else:
                    sport = 22
            except:
                sport = 22

            ssh.connect(str(el["IP"]).strip(),
                        username=str(el["User"]).strip(), port=sport, password=str(el["Password"]).strip(), timeout=5)
            el["__SSH__"] = "Yes"
            el["Status"] = 'running'

            ssh.close()
            self.services(el, None)
        except:
            el["Status"] = 'stopped'
            el["__SSH__"] = "No"

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

    def services(self, el, source):

        try:
            os.system("rm ~/.ssh/known_hosts")
        except:
            pass
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            try:
                if "PORT" in el:
                    sport = int(str(el["PORT"]).strip())
                else:
                    sport = 22
            except:
                sport = 22

            ssh.connect(str(el["IP"]).strip(),
                        username=str(el["User"]).strip(), port=sport, password=str(el["Password"]).strip(), timeout=5)

            el["Status"] = 'running'
            el["__SSH__"] = "Yes"

            try:
                os = self.ssh_exec_read(
                    ssh, """uname""")
                el["OS Type"] = os
            except Exception as e:
                el["OS Type"] = "Unknown"

            if el["OS Type"] == "Linux":
                try:
                    cmd = self.ssh_exec_read(
                        ssh, """command -v sockstat""")
                    if cmd == "":
                        cmd = self.ssh_exec_read(
                            ssh, """apt-get update ; apt-get install coreutils sockstat procps -y""")
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + \
                        " :: ERROR OPEN PORTS   ]"
                try:
                    mem = self.ssh_exec_read(
                        ssh, """vmstat -s | awk  '$0 ~ /total memory/ {total=$1 } $0 ~/free memory/ {free=$1} $0 ~/buffer memory/ {buffer=$1} $0 ~/cache/ {cache=$1} END{print (total-free-buffer-cache)/total*100}'""")
                    self.history_append(el, "Memory", mem)
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR MEMORY   ]"

                try:
                    nbcpus = int(self.ssh_exec_read(
                        ssh, """cat /proc/cpuinfo | grep processor | wc -l"""))
                    el["NB CPU"] = nbcpus
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR NG CPU  ]"

                try:

                    cpuusage = self.ssh_exec_read(
                        ssh, """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}' """)
                    self.history_append(el, "CPU Usage", cpuusage)
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR CPU USAGE ]"

                try:
                    uptime = self.ssh_exec_read(ssh, "uptime | cut -d',' -f1")
                    el["Uptime"] = uptime
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR UPTIME   ]"

                try:
                    disk = self.ssh_exec_read(
                        ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '$NF=="/"{printf "%d\\n",$5}' """)
                    self.history_append(el, "Disk", disk)
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR DISK  ]"

                try:
                    openports = self.ssh_exec_read(
                        ssh, """sockstat -l | awk 'split($5,port,":"){if( port[1] ~ "127.0.0.1") { targ="Local Only" } else { targ="WAN Interface" }} NR > 1 && NR < 15 && !seen[$2port[2]]++ {printf "%s|%s|%s\\n",toupper($2),port[2],targ } ' """)
                    el["Services"] = openports
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR OPEN PORTS ]"
                try:
                    mounts = self.ssh_exec_read(
                        ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '(NR > 1 && $6 != "/"){printf "%s|%s / %s|%s\\n",$6,$3,$2,$5}'""")
                    el["Mounts"] = mounts
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR MOUNTS   ]"


            elif source != None:
                self.proxmox_import(el, source)

            ssh.close()

        except Exception as e:
            el["__SSH__"] = "No"

        if el["Status"] != "running":
            status = 0
        else:
            status = 100
        self.history_append(el, "Status History", status)

    def ssh_exec_read(self, ssh, cmd):
        out = ""
        ssh_stdin, stdout, ssh_stderr = ssh.exec_command(cmd, get_pty=True)
        output = stdout.read()
        for line in output.splitlines():
            if line.strip() != "":
                out += line.strip() + "\n"
        return str(out).strip()

    def proxmox_import(self, el, source):
        try:
            mem = float(float(source["mem"]) / float(source["maxmem"])) * 100
            self.history_append(el, "Memory", mem)

        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR MEMORY   ]"

        try:
            nbcpus = source["cpus"]
            el["NB CPU"] = nbcpus
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR NG CPU  ]"

        try:
            nbcpus = source["maxcpu"]
            el["NB CPU"] = nbcpus
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR NG CPU  ]"

        try:
            cpuusage = float(source["cpu"]) * 100
            self.history_append(el, "CPU Usage", cpuusage)
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR CPU USAGE   ]"

        try:
            uptime = str(timedelta(seconds=(source["uptime"])))
            el["Uptime"] = uptime
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR UPTIME   ]"

        try:
            disk = float(float(source["disk"]) /
                         float(source["maxdisk"])) * 100
            self.history_append(el, "Disk", disk)
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR DISK  ]"

    def proxmox(self, id, lst, arp):
        el = lst[id]
        try:
            proxmox = ProxmoxAPI(str(el["IP"]).strip(), user=str(el["User"]).strip()+'@pam', password=str(el["Password"]).strip(),
                                 verify_ssl=False)
            el["Status"] = 'running'

        except:
            el["Status"] = 'stopped'
            for k in el["__CHILDREN__"]:
                el["__CHILDREN__"][k]["Status"] = "unknown"
            print "> [ " + str(el["__ID__"]) + " :: FAILED  ]"
            return
        for node in proxmox.nodes.get():
            el["__ID__"] = node['node']
            self.services(el, node)

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
                        self.services(value, vm)
                        self.store.edit(id, key, value,
                                        el["__CHILDREN__"])
                    else:
                        k["__CHILDREN__"] = dict()
                        k["__SCHEMA__"] = "VM"
                        self.store.add(id, k)
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
                        self.services(value, vm)
                        self.store.edit(id, key, value,
                                        el["__CHILDREN__"])
                    else:
                        k["__CHILDREN__"] = dict()
                        k["__SCHEMA__"] = "Container"
                        self.store.add(id, k)
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
                        self.services(value, vm)
                        self.store.edit(id, key, value,
                                        el["__CHILDREN__"])
                    else:
                        k["__CHILDREN__"] = dict()
                        k["__SCHEMA__"] = "Container"
                        self.store.add(id, k)

            except:
                pass

