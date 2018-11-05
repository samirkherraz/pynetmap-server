#!/usr/bin/python
from datetime import timedelta
from .zabbix_api import ZabbixAPI


class Monitor:

    def login(self):
        if self.zabbix == None or not self.zabbix.test_login():
            try:
                self.zabbix = ZabbixAPI(server=self.store.get_attr(
                    "server", "zabbix", "url"))
                self.zabbix.login(self.store.get_attr(
                    "server", "zabbix", "username"), self.store.get_attr(
                    "server", "zabbix", "password"))
            except ValueError as e:
                return False
        return self.zabbix != None and self.zabbix.test_login()

    def update_schemat(self):
        hostlist = self.getHostList()
        fields = self.store.get_attr("schema", "Noeud", "Fields")
        fields["base.monitor.zabbix.id"] = hostlist
        self.store.set_attr("schema", "Noeud", "Fields", fields)

        fields = self.store.get_attr("schema", "VM", "Fields")
        fields["base.monitor.zabbix.id"] = hostlist
        self.store.set_attr("schema", "VM", "Fields", fields)

        fields = self.store.get_attr("schema", "Container", "Fields")
        fields["base.monitor.zabbix.id"] = hostlist
        self.store.set_attr("schema", "Container", "Fields", fields)

    def __init__(self, model):
        self.utils = model.utils
        self.store = model.store
        self.zabbix = None
        self.login()
        self.update_schemat()
        self.data = None

    def getHostList(self):
        return [e["hostid"]+"::"+e["name"]
                for e in self.zabbix.host.get({"output": ["hostid", "name", "ip"], "selectInterfaces": ["ip"], })]

    def getHostInfo(self, id):
        return {e["key_"]: e["lastvalue"]
                for e in self.zabbix.item.get({
                    "output": ["key_", "lastvalue"],
                    "filter": {
                        "hostid": id,
                    }
                })}

    def isHostUP(self, id):
        status = self.zabbix.host.get({
            "output": ["status"],
            "filter": {
                "hostid": id,
            }
        })
        if len(status) > 0:
            return str(status[0]["status"]) == "0"
        else:
            return False

    def getHostByIP(self, ip):
        return [e["hostid"]+"::"+e["name"]
                for e in self.zabbix.host.get({"output": ["hostid", "name", "ip"], "selectInterfaces": ["ip"], "filter": {"ip": ip}})]

    def populateData(self, id):

        if not self.login():
            return False
        zabbixid = self.store.get_attr(
            "base", id, "base.monitor.zabbix.id")
        if zabbixid == None:
            ip = self.store.get_attr("base", id, "base.net.ip")
            inf = self.getHostByIP(ip)
            zabbixid = inf[0] if len(inf) > 0 else None
            if zabbixid == None:
                return False
            self.store.set_attr("base", id, "base.monitor.zabbix.id", zabbixid)

        zabbixid = zabbixid.split("::")[0]

        if not self.isHostUP(zabbixid):
            return False

        self.data = self.getHostInfo(zabbixid)
        if self.data == None:
            return False
        return True

    def getItem(self, key):
        for el in self.data.keys():
            if el == key:
                return self.data[el]

    def getItemList(self, key):
        d = dict()
        for el in self.data.keys():
            if str(el).startswith(key):
                d[el] = self.data[el]
        return d

    def process(self, id):
        if not self.populateData(id):
            return self.utils.STOPPED_STATUS
        failed = False

        try:
            nbcpus = 0
            self.store.set_attr(
                "module", id, "module.state.nbcpu", nbcpus)
        except ValueError as e:
            print(e)
            failed = True

        try:

            memtotal = float(self.getItem("vm.memory.size[total]"))
            memavail = float(self.getItem("vm.memory.size[available]"))

            mem = "{0:.2f}".format(100*((memtotal-memavail)/memtotal))
            self.store.set_attr("module", id, "module.state.history.memory",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.memory"), str(mem)))
        except ValueError as e:
            print(e)
            failed = True

        try:
            nbcpus = 0
            self.store.set_attr(
                "module", id, "module.state.nbcpu", nbcpus)
        except ValueError as e:
            print(e)
            failed = True

        try:

            cpuusage = "{0:.2f}".format(
                float(self.getItem("system.cpu.load[percpu,avg5]")))
            self.store.set_attr("module", id, "module.state.history.cpuusage",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.cpuusage"), str(cpuusage)))
        except ValueError as e:
            print(e)

            failed = True

        try:
            uptime = self.getItem("system.uptime")
            self.store.set_attr("module", id, "module.state.uptime", str(
                timedelta(seconds=(int(float(uptime))))))
        except ValueError as e:
            print(e)

            failed = True

        try:

            disktotal = float(self.getItem("vfs.fs.size[/,total]"))
            diskused = float(self.getItem("vfs.fs.size[/,used]"))

            disk = "{0:.2f}".format(100*(diskused/disktotal))
            self.store.set_attr("module", id, "module.state.history.disk",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.disk"),  str(disk)))
        except ValueError as e:
            print(e)

            failed = True

        try:
            dataset = self.getItemList("vfs.fs.size")
            mounts = dict()
            for e in dataset.keys():
                volume = e.replace("vfs.fs.size[", "").split(",")[0]
                data = e.replace("]", "").split(",")[1]
                if volume not in mounts.keys():
                    mounts[volume] = dict()
                mounts[volume][data] = dataset[e]

            lst = []
            for line in mounts.keys():
                k = dict()
                k["point"] = str(line)
                k["usage"] = str("{0:.2f}".format(
                    100-(float(mounts[line]["pfree"]))))+" %"
                lst.append(k)
            self.store.set_attr(
                "module", id, "module.state.list.mounts", lst)
        except ValueError as e:
            print(e)

            failed = True
        if not failed:
            return self.utils.RUNNING_STATUS
        else:
            return self.utils.UNKNOWN_STATUS
