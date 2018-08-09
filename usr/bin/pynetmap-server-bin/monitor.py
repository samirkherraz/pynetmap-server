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
                    if "Memory" not in el.keys() or type(el["Memory"]) is not list:
                        el["Memory"] = []
                    while len(el["Memory"]) > 100:
                        el["Memory"].pop()
                    mem = self.ssh_exec_read(
                        ssh, """free -m | awk 'NR==2{printf "%.2f\\n", $3*100/$2 }'""")
                    el["Memory"].append(mem)
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR MEMORY   ]"

                try:
                    nbcpus = int(self.ssh_exec_read(
                        ssh, """cat /proc/cpuinfo | grep processor | wc -l"""))
                    el["NB CPU"] = nbcpus
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR NG CPU  ]"

                try:
                    if "CPU Usage" not in el.keys() or type(el["CPU Usage"]) is not list:
                        el["CPU Usage"] = []
                    while len(el["CPU Usage"]) > 100:
                        el["CPU Usage"].pop()
                    cpuusage = self.ssh_exec_read(
                        ssh, """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}' """)
                    el["CPU Usage"].append(cpuusage)
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + \
                        " :: ERROR CPU USAGE   ]"

                try:
                    uptime = self.ssh_exec_read(ssh, "uptime | cut -d',' -f1")
                    el["Uptime"] = uptime
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR UPTIME   ]"

                try:
                    if "Disk" not in el.keys() or type(el["Disk"]) is not list:
                        el["Disk"] = []
                    while len(el["Disk"]) > 100:
                        el["Disk"].pop()
                    disk = self.ssh_exec_read(
                        ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '$NF=="/"{printf "%d\\n",$5}' """)
                    el["Disk"].append(disk)
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + " :: ERROR DISK  ]"

                try:
                    openports = self.ssh_exec_read(
                        ssh, """sockstat -l | awk 'split($5,port,":"){if( port[1] ~ "127.0.0.1") { targ="Local Only" } else { targ="WAN Interface" }} NR > 1 && !seen[$2port[2]]++ {printf "%s|%s|%s\\n",toupper($2),port[2],targ } ' """)
                    el["Services"] = openports
                except Exception as e:
                    print "> [ " + str(el["__ID__"]) + \
                        " :: ERROR OPEN PORTS   ]"
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
            if "Memory" not in el.keys() or type(el["Memory"]) is not list:
                el["Memory"] = []
            while len(el["Memory"]) > 100:
                el["Memory"].pop()
            mem = float(float(source["mem"]) / float(source["maxmem"])) * 100
            el["Memory"].append(mem)
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
            if "CPU Usage" not in el.keys() or type(el["CPU Usage"]) is not list:
                el["CPU Usage"] = []
            while len(el["CPU Usage"]) > 100:
                el["CPU Usage"].pop()
            cpuusage = float(source["cpu"]) * 100
            el["CPU Usage"].append(cpuusage)
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR CPU USAGE   ]"

        try:
            uptime = str(timedelta(seconds=(source["uptime"])))
            el["Uptime"] = uptime
        except Exception as e:
            print "> [ " + str(el["__ID__"]) + " :: ERROR UPTIME   ]"

        try:
            if "Disk" not in el.keys() or type(el["Disk"]) is not list:
                el["Disk"] = []
            while len(el["Disk"]) > 100:
                el["Disk"].pop()
            disk = float(float(source["disk"]) /
                         float(source["maxdisk"])) * 100
            el["Disk"].append(disk)
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
