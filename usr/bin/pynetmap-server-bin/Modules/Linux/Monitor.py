#!/usr/bin/python
from datetime import timedelta


class Monitor:

    def __init__(self, store, utils):
        self.utils = utils
        self.store = store

    def dependencies(self, ssh):
        self.utils.ssh_exec_read(ssh,
                                 """(command -v arp-scan && command -v route && command -v sockstat && command -v vmstat) || ( apt-get update ; apt-get install arp-scan coreutils sockstat procps net-tools -y )""")

    def process(self, id):
        ssh = self.utils.open_ssh(id)
        if ssh == None:
            return self.utils.STOPPED_STATUS
        failed = False
        self.dependencies(ssh)
        try:
            mem = self.utils.ssh_exec_read(
                ssh, """vmstat -s | awk  '$0 ~ /total memory/ {total=$1 } $0 ~/free memory/ {free=$1} $0 ~/buffer memory/ {buffer=$1} $0 ~/cache/ {cache=$1} END{print (total-free-buffer-cache)/total*100}'""", self.store.get_attr(
                    "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.history.memory",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.memory"), mem))
        except:
            failed = True

        try:
            nbcpus = int(self.utils.ssh_exec_read(
                ssh, """cat /proc/cpuinfo | grep processor | wc -l""", self.store.get_attr(
                    "base", id, "base.name")))
            self.store.set_attr(
                "module", id, "module.state.nbcpu", nbcpus)
        except:
            failed = True

        try:

            cpuusage = self.utils.ssh_exec_read(
                ssh, """grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$4+$5)} END {print usage}' """, self.store.get_attr(
                    "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.history.cpuusage",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.cpuusage"), cpuusage))
        except:
            failed = True

        try:
            uptime = self.utils.ssh_exec_read(ssh, "awk '{print $1}' /proc/uptime", self.store.get_attr(
                "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.uptime", str(
                timedelta(seconds=(int(float(uptime))))))
        except:
            failed = True

        try:
            disk = self.utils.ssh_exec_read(
                ssh, """df -h |  grep -v "tmpfs\|udev\|rootfs\|none" | awk '$NF=="/"{printf "%d\\n",$5}' """, self.store.get_attr(
                    "base", id, "base.name"))
            self.store.set_attr("module", id, "module.state.history.disk",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.disk"), disk))
        except:
            failed = True

        try:
            openports = self.utils.ssh_exec_read(
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

        except:
            failed = True
        try:
            mounts = self.utils.ssh_exec_read(
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
        except:
            failed = True
        ssh.close()
        if not failed:
            return self.utils.RUNNING_STATUS
        else:
            return self.utils.UNKNOWN_STATUS
