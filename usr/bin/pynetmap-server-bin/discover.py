#!/usr/bin/python
from proxmoxer import ProxmoxAPI
from utils import Utils
from threading import Thread, Event
import time
from datetime import timedelta
import paramiko
from const import UPDATE_INTERVAL


class Discover(Thread):
    FROM_PVE = 1
    FROM_SSH = 0
    FROM_SSH_THEN_PVE = 2
    ALERT_ERROR = 1
    ALERT_INFO = 0

    def __init__(self, parent):
        Thread.__init__(self)
        self.store = parent.store
        self.parent = parent
        self.arp = dict()
        self._stop = Event()

    def arp_table(self, id):
        ssh = Utils.open_ssh(self.store.get("base", id))
        if ssh != None:
            table = Utils.ssh_exec_read(ssh,
                                        """for i in $(route -n | awk 'NR > 2 && !seen[$1$2]++  {print $8}');do arp-scan -I $i -l --quiet | head -n -3 | tail -n +3 ; done | awk '!seen[$1$2]++ { print $1"="$2;}'""")
            try:
                for line in table.split("\n"):
                    try:
                        self.arp[line.split("=")[1].upper()] = line.split("=")[
                            0].upper()
                    except:
                        pass
            except:
                pass

    def dependencies(self, id):
        ssh = Utils.open_ssh(self.store.get("base", id))
        if ssh != None:
            Utils.ssh_exec_read(ssh,
                                """(command -v arp-scan && command -v route && command -v sockstat && command -v vmstat) || ( apt-get update ; apt-get install arp-scan coreutils sockstat procps net-tools -y )""")

    def run(self):
        while not self._stop.isSet():
            self._stop.wait(UPDATE_INTERVAL)
            Utils.debug("System", "Discovery started")
            threads = []
            all = self.store.find_by_schema("Noeud")
            for id in all:
                thread = None
                print self.store.get_attr("base", id, "base.type")
                if str(self.store.get_attr("base", id, "base.type")).rstrip() == "Proxmox":
                    thread = Thread(
                        target=self.proxmox, args=(id,))
                    thread.start()
                elif str(self.store.get_attr("base", id, "base.type")) == "Physical":
                    thread = Thread(
                        target=self.physical, args=(id,))
                    thread.start()
                threads.append(thread)
            for t in threads:
                try:
                    t.joint(timeout=UPDATE_INTERVAL)
                    print "END"
                except:
                    pass

    def physical(self, id):
        self.discover(id)

    def set_status(self, id, bln, status=None):
        el = self.store.get("base", id)
        if bln or status == "running":
            Utils.debug(el["base.name"], "Host is up")
            self.store.set_attr("module", id, "module.state.history.status",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.status"), 100))
            self.store.set_attr("module", id, "module.state.status", 'running')
        else:
            Utils.debug(el["base.name"], "Host is down", 1)
            self.store.set_attr("module", id, "module.state.history.status",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.status"), 0))
            self.store.set_attr("module", id, "module.state.status",
                                ('stopped' if status == None else status))

    def discover(self, id, source=None):
        el_base = self.store.get("base", id)
        ssh = Utils.open_ssh(el_base)
        if ssh != None:
            self.dependencies(id)
            self.store.set_attr("module", id, "module.discover.ssh", "Yes")
            os = Utils.ssh_exec_read(
                ssh, """uname""", el_base["base.name"])
            self.store.set_attr("module", id, "module.discover.os", os)
            if source != None:
                self.monitor(id, ssh, Discover.FROM_SSH_THEN_PVE, source)
                self.set_status(id, True)
            else:
                self.monitor(id, ssh, Discover.FROM_SSH)
                self.set_status(id, True)
            ssh.close()
        else:
            self.store.set_attr("module", id, "module.discover.os", "Unknown")
            self.store.set_attr("module", id, "module.discover.ssh", "No")
            if source != None:
                self.monitor(id, source, Discover.FROM_PVE)
                self.set_status(id, False, source["status"])
            else:
                self.set_status(id, False)

        self.parent.alerts.check(id)

    def monitor(self, id, source, method, extra=None):
        if method == Discover.FROM_SSH:
            if self.store.get_attr("module", id, "module.discover.os") == "Linux":
                failed = self.monitor_linux(id, source)
            else:
                failed = True
        elif method == Discover.FROM_SSH_THEN_PVE:
            if self.store.get_attr("module", id, "module.discover.os") == "Linux":
                failed = self.monitor_linux(id, source)
                if failed:
                    failed = self.monitor_proxmox(id, extra)
            else:
                failed = self.monitor_proxmox(id, extra)
        elif method == Discover.FROM_PVE:
            failed = self.monitor_proxmox(id, source)

        self.store.set_attr(
            "module", id, "module.state.lastupdate", time.time())

        if failed:
            Utils.debug(self.store.get_attr("base", id, "base.name"),
                        "monitoring data partialy or could not be retrived", 1)
        else:
            Utils.debug(self.store.get_attr("base", id, "base.name"),
                        "monitoring data recived", 0)

    def monitor_proxmox(self, id, source):

        failed = False
        try:
            mem = float(float(source["mem"]) / float(source["maxmem"])) * 100
            self.store.set_attr("module", id, "module.state.history.memory",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.memory"), mem))

        except Exception as e:
            failed = True

        nbcpus = None
        try:
            nbcpus = source["cpus"]
            self.store.set_attr("module", id, "module.state.nbcpu", nbcpus)
        except Exception as e:
            pass

        try:
            nbcpus = source["maxcpu"]
            self.store.set_attr("module", id, "module.state.nbcpu", nbcpus)
        except Exception as e:
            pass

        failed = (nbcpus == None)

        try:
            cpuusage = float(source["cpu"]) * 100
            self.store.set_attr("module", id, "module.state.history.cpuusage",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.cpuusage"), cpuusage))
        except Exception as e:
            failed = True

        try:
            uptime = str(timedelta(seconds=(source["uptime"])))
            self.store.set_attr("module", id, "module.state.uptime", uptime)
        except Exception as e:
            failed = True

        try:
            disk = float(float(source["disk"]) /
                         float(source["maxdisk"])) * 100
            self.store.set_attr("module", id, "module.state.history.disk",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.disk"), disk))
        except Exception as e:
            failed = True

        return failed

    def monitor_linux(self, id, ssh):
        failed = False
        try:
            mem = Utils.ssh_exec_read(
                ssh, """vmstat -s | awk  '$0 ~ /total memory/ {total=$1 } $0 ~/free memory/ {free=$1} $0 ~/buffer memory/ {buffer=$1} $0 ~/cache/ {cache=$1} END{print (total-free-buffer-cache)/total*100}'""", self.store.get_attr(
                    "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.history.memory",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.memory"), mem))
        except Exception as e:
            failed = True

        try:
            nbcpus = int(Utils.ssh_exec_read(
                ssh, """cat /proc/cpuinfo | grep processor | wc -l""", self.store.get_attr(
                    "base", id, "base.name")))
            self.store.set_attr("module", id, "module.state.nbcpu", nbcpus)
        except Exception as e:
            failed = True

        try:

            cpuusage = Utils.ssh_exec_read(
                ssh, """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}' """, self.store.get_attr(
                    "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.history.cpuusage",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.cpuusage"), cpuusage))
        except Exception as e:
            failed = True

        try:
            uptime = Utils.ssh_exec_read(ssh, "awk '{print $1}' /proc/uptime", self.store.get_attr(
                "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.uptime", str(
                timedelta(seconds=(int(float(uptime))))))
        except Exception as e:
            failed = True

        try:
            disk = Utils.ssh_exec_read(
                ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '$NF=="/"{printf "%d\\n",$5}' """, self.store.get_attr(
                    "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.history.disk",
                                Utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.disk"), disk))
        except Exception as e:
            failed = True

        try:
            openports = Utils.ssh_exec_read(
                ssh, """sockstat -l | awk 'split($5,port,":"){if( port[1] ~ "127.0.0.1") { targ="Local" } else { targ="WAN" }} NR > 1 && NR < 15 && !seen[$2port[2]]++ {printf "%s|%s|%s\\n",toupper($2),port[2],targ } ' """, self.store.get_attr(
                    "base", id, "base.name"))
            lst = []
            for line in openports.split("\n"):
                if line.rstrip() != "":
                    k = dict()
                    arr = line.split("|")
                    k["service"] = arr[0]
                    k["port"] = arr[1]
                    k["listen"] = arr[2]
                    lst.append(k)
            self.store.set_attr(
                "module", id, "module.state.list.services", lst)

        except Exception as e:
            failed = True
        try:
            mounts = Utils.ssh_exec_read(
                ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '(NR > 1 && $6 != "/"){printf "%s|%s / %s|%d\\n",$6,$3,$2,$5}'""", self.store.get_attr(
                    "base", id, "base.name"))
            lst = []
            for line in mounts.split("\n"):
                if line.rstrip() != "":
                    k = dict()
                    arr = line.split("|")
                    k["point"] = arr[0]
                    k["capacity"] = arr[1]
                    k["usage"] = arr[2]
                    lst.append(k)
            self.store.set_attr(
                "module", id, "module.state.list.mounts", lst)
        except Exception as e:
            failed = True

        return failed

    def proxmox_find(self, name, id):
        for k in self.store.get_children(id):
            if self.store.get_attr("base", k, "base.name") == name:
                return k
        newid = self.store.create(id)
        return newid

    def proxmox(self, id):
        try:
            proxmox = ProxmoxAPI(str(self.store.get_attr(
                "base", id, "base.net.ip")).strip(),
                user=str(self.store.get_attr(
                    "base", id, "base.ssh.user")).strip()+'@pam',
                password=str(self.store.get_attr(
                    "base", id, "base.ssh.password")).strip(),
                verify_ssl=False)

            self.store.set_attr(
                "module", id, "module.discover.proxmox", "Yes")
            Utils.debug(self.store.get_attr(
                "base", id, "base.name"), "proxmox api is up", 0)
        except:
            Utils.debug(self.store.get_attr(
                "base", id, "base.name"), "proxmox api is unreachable", 2)
            self.store.set_attr(
                "module", id, "module.discover.proxmox", "No")
            return
        for node in proxmox.nodes.get():
            self.store.set_attr(
                "base", id, "base.name", node['node'])
            self.discover(id)
            self.arp_table(id)
            try:
                for vm in proxmox.nodes(node['node']).qemu.get():
                    k = self.proxmox_find(vm["name"], id)
                    self.store.set_attr("base", k, "base.name", vm["name"])
                    self.store.set_attr(
                        "base", k, "base.proxmox.id", vm["vmid"])
                    self.store.set_attr(
                        "base", k, "base.core.schema", "VM")
                    for i in proxmox.nodes(node['node']).qemu(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                ip = self.arp[proxmox.nodes(node['node']).qemu(
                                    vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]]
                                eth = i
                                mac = proxmox.nodes(node['node']).qemu(
                                    vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]
                                self.store.set_attr(
                                    "base", k, "base.net.ip", ip)
                                self.store.set_attr(
                                    "base", k, "base.net.eth", eth)
                                self.store.set_attr(
                                    "base", k, "base.net.mac", mac)

                            except:
                                pass
                    self.discover(k, vm)

            except ValueError as e:
                print e

            try:
                for vm in proxmox.nodes(node['node']).lxc.get():
                    k = self.proxmox_find(vm["name"], id)
                    self.store.set_attr("base", k, "base.name", vm["name"])
                    self.store.set_attr(
                        "base", k, "base.proxmox.id", vm["vmid"])
                    self.store.set_attr(
                        "base", k, "base.core.schema", "Container")

                    for i in proxmox.nodes(node['node']).lxc(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                ip = self.arp[proxmox.nodes(node['node']).lxc(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]]
                                eth = i
                                mac = proxmox.nodes(node['node']).lxc(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                self.store.set_attr(
                                    "base", k, "base.net.ip", ip)
                                self.store.set_attr(
                                    "base", k, "base.net.eth", eth)
                                self.store.set_attr(
                                    "base", k, "base.net.mac", mac)

                            except:
                                pass

                    self.discover(k, vm)

            except:
                pass
            try:
                for vm in proxmox.nodes(node['node']).openvz.get():
                    k = self.proxmox_find(vm["name"], id)
                    self.store.set_attr("base", k, "base.name", vm["name"])
                    self.store.set_attr(
                        "base", k, "base.proxmox.id", vm["vmid"])
                    self.store.set_attr(
                        "base", k, "base.core.schema", "Container")
                    for i in proxmox.nodes(node['node']).openvz(vm["vmid"]).config.get():
                        if 'net' in i:
                            try:
                                ip = self.arp[proxmox.nodes(node['node']).openvz(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]]
                                eth = i
                                mac = proxmox.nodes(node['node']).openvz(
                                    vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                self.store.set_attr(
                                    "base", k, "base.net.ip", ip)
                                self.store.set_attr(
                                    "base", k, "base.net.eth", eth)
                                self.store.set_attr(
                                    "base", k, "base.net.mac", mac)

                            except:
                                pass
                    self.discover(k, vm)

            except:
                pass

    def stop(self):
        self._stop.set()
