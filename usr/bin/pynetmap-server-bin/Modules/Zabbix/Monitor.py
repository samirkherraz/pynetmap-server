#!/usr/bin/python
from datetime import timedelta
from zabbix_api import ZabbixAPI
from threading import Semaphore
from Core.Database.DbUtils import DbUtils
from Core.Utils import Fn
from Constants import *
from Core.Utils.Logging import getLogger
logging = getLogger(__package__)





class Monitor:
    def connect(self):
        try:
            zabbix = ZabbixAPI(
                server=self.db[DB_SERVER, "zabbix", "url"])
            zabbix.login(self.db[DB_SERVER, "zabbix", "username"],
                         self.db[DB_SERVER, "zabbix", "password"])
            return zabbix
        except:
            logging.error("UNABLE TO ACCESS ZABBIX API")
            return None

    def __init__(self):
        self.db = DbUtils.getInstance()
        zabbix = self.connect()
        if zabbix is not None:
            host_list = self.get_host_list(zabbix)
            host_list.sort()
            for e in ["Noeud","VM","Container"]:
                self.db[DB_SCHEMA, e, "Fields", KEY_MONITOR_ZABBIX_ID] = host_list

    def get_host_list(self, zabbix):
        return [e["name"]+"::"+e["hostid"] for e in zabbix.host.get({"output": ["hostid", "name", "ip"], "selectInterfaces": ["ip"], })]

    def get_host_info(self, zabbix, id):
        return {e["key_"]: e["lastvalue"]
                for e in zabbix.item.get({
                    "output": ["key_", "lastvalue"],
                    "filter": {
                        "hostid": id,
                    }
                })}

    def is_host_up(self, zabbix, id):
        status = zabbix.host.get({
            "output": ["status"],
            "filter": {
                "hostid": id,
            }
        })
        if len(status) > 0:
            return str(status[0]["status"]) == "0"
        else:
            return False

    def get_host_by_ip(self, zabbix, ip):
        return [e["name"]+"::"+e["hostid"]
                for e in zabbix.host.get({"output": ["hostid", "name", "ip"], "selectInterfaces": ["ip"], "filter": {"ip": ip}})]

    def populate(self, id):
        zabbix = self.connect()
        if zabbix == None:
            return None
        zabbixid = self.db[DB_BASE, id, KEY_MONITOR_ZABBIX_ID]
        if zabbixid == None:
            ip = self.db[DB_BASE, id, KEY_NET_IP]
            inf = self.get_host_by_ip(zabbix, ip)
            zabbixid = inf[0] if len(inf) > 0 else None
            if zabbixid == None:
                return None
            self.db[DB_BASE, id, KEY_MONITOR_ZABBIX_ID] = zabbixid
        else:
            zabbixid = zabbixid.split("::")[1]

        if not self.is_host_up(zabbix, zabbixid):
            return None

        data = self.get_host_info(zabbix, zabbixid)
        return data

    def get_item(self, data, key):
        for el in data.keys():
            if el == key:
                return data[el]
        return None

    def get_item_list(self, data, key):
        d = dict()
        for el in data.keys():
            if str(el).startswith(key):
                d[el] = data[el]
        return d

    def process(self, id):
        data = self.populate(id)
        if data == None:
            return STOPPED_STATUS
        failed = False

        try:
            nbcpus = 0
            self.db[DB_MODULE, id, KEY_MONITOR_NB_CPU] = nbcpus
        except:
            pass
            failed = True

        try:

            memtotal = float(self.get_item(data,"vm.memory.size[total]"))
            memavail = float(self.get_item(data,"vm.memory.size[available]"))

            mem = "{0:.2f}".format(100*((memtotal-memavail)/memtotal))
            if self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_MEMORY] is None:
                self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_MEMORY] = list()
            Fn.history(
                self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_MEMORY], str(mem))

        except:
            pass
            failed = True

        try:

            cpuusage = "{0:.2f}".format(
                float(self.get_item(data,"system.cpu.load[percpu,avg5]")))
            if self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_CPU_USAGE] is None:
                self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_CPU_USAGE] = list()
            Fn.history(
                self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_CPU_USAGE], str(cpuusage))
        except:
            pass
            failed = True

        try:
            uptime = self.get_item(data,"system.uptime")
            self.db[DB_MODULE, id, "uptime"] = str(
                timedelta(seconds=(int(float(uptime)))))
        except:
            pass

            failed = True

        try:

            disktotal = float(self.get_item(data,"vfs.fs.size[/,total]"))
            diskused = float(self.get_item(data,"vfs.fs.size[/,used]"))

            disk = "{0:.2f}".format(100*(diskused/disktotal))
            if self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_DISK] is None:
                self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_DISK] = list()
            Fn.history(
                self.db[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_DISK],  str(disk))
        except:
            pass

            failed = True

        try:
            dataset = self.get_item_list(data,"vfs.fs.size")
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
            if self.db[DB_MODULE, id, KEY_MONITOR_LISTS, KEY_MONITOR_MOUNTS] is None:
                self.db[DB_MODULE, id, KEY_MONITOR_LISTS, KEY_MONITOR_MOUNTS] = list()
            self.db[DB_MODULE, id, KEY_MONITOR_LISTS, KEY_MONITOR_MOUNTS] = lst
        except:
            pass
            failed = True

        if not failed:
            return RUNNING_STATUS
        else:
            return UNKNOWN_STATUS
