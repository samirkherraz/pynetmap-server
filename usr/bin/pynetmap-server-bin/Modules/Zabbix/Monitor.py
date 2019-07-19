#!/usr/bin/python
from datetime import timedelta
from threading import Semaphore

from zabbix_api import ZabbixAPI

from Constants import *
from Core.Database.DbUtils import DbUtils
from Core.Utils import Fn
from Core.Utils.Logging import getLogger


class Monitor:
    def connect(self):
        logging = getLogger(__package__)
        try:
            zabbix = ZabbixAPI(server=DbUtils.getInstance()
                               [DB_SERVER, "zabbix", "url"])
            zabbix.login(DbUtils.getInstance()[DB_SERVER, "zabbix", "username"],
                         DbUtils.getInstance()[DB_SERVER, "zabbix", "password"])
            return zabbix
        except Exception as e:
            logging.error(e)
            logging.error("UNABLE TO ACCESS ZABBIX API")
            return None

    def __init__(self):
        logging = getLogger(__package__)
        zabbix = self.connect()
        if zabbix is not None:
            try:
                host_list = self.get_host_list(zabbix)
                host_list.sort()
                for e in ["Noeud", "VM", "Container"]:
                    DbUtils.getInstance()[DB_SCHEMA, e, "Fields",
                                          KEY_MONITOR_ZABBIX_ID] = host_list
                logging.info("POPULATE SCHEMA FIELDS")
            except Exception as e:
                logging.debug(e)

    def get_host_list(self, zabbix):
        logging = getLogger(__package__)
        try:
            return [e["name"]+"::"+e["hostid"] for e in zabbix.host.get({"output": ["hostid", "name", "ip"], "selectInterfaces": ["ip"], })]
        except Exception as e:
            logging.debug(e)
            return []

    def get_host_info(self, zabbix, id):
        logging = getLogger(__package__)
        try:

            return {e["key_"]: e["lastvalue"]
                    for e in zabbix.item.get({
                        "output": ["key_", "lastvalue"],
                        "filter": {
                            "hostid": id,
                        }
                    })}
        except Exception as e:
            logging.debug(e)
            return {}

    def is_host_up(self, zabbix, id):
        logging = getLogger(__package__)
        try:
            status = zabbix.host.get({
                "output": ["status"],
                "filter": {
                    "hostid": id,
                }
            })
            if len(status) > 0:
                return str(status[0]["status"]) == "0"
        except Exception as e:
            logging.debug(e)
        return False

    def get_host_by_ip(self, zabbix, ip):
        return [e["name"]+"::"+e["hostid"]
                for e in zabbix.host.get({"output": ["hostid", "name", "ip"], "selectInterfaces": ["ip"], "filter": {"ip": ip}})]

    def populate(self, id):
        zabbix = self.connect()
        if zabbix is not None:
            zabbixid = DbUtils.getInstance(
            )[DB_BASE, id, KEY_MONITOR_ZABBIX_ID]
            if zabbixid == None:
                ip = DbUtils.getInstance()[DB_BASE, id, KEY_NET_IP]
                inf = self.get_host_by_ip(zabbix, ip)
                zabbixid = inf[0] if len(inf) > 0 else None
                if zabbixid == None:
                    return None
                DbUtils.getInstance()[DB_BASE, id,
                                      KEY_MONITOR_ZABBIX_ID] = zabbixid
                DbUtils.getInstance().persist()

            else:
                zabbixid = zabbixid.split("::")[1]

            if not self.is_host_up(zabbix, zabbixid):
                return None

            data = self.get_host_info(zabbix, zabbixid)
            return data
        return None

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
        if data is None:
            return STOPPED_STATUS
        else:
            logging = getLogger(__package__, DbUtils.getInstance()[
                                DB_BASE, id, KEY_NAME])
            failed = False

            try:
                nbcpus = 0
                DbUtils.getInstance()[DB_MODULE, id,
                                      KEY_MONITOR_NB_CPU] = nbcpus
                logging.info(f'NB CPU SET TO {nbcpus}')
            except Exception as e:
                logging.warning(e)
                failed = True

            try:

                memtotal = float(self.get_item(data, "vm.memory.size[total]"))
                memavail = float(self.get_item(
                    data, "vm.memory.size[available]"))

                mem = "{0:.2f}".format(100*((memtotal-memavail)/memtotal))
                if DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_MEMORY] is None:
                    DbUtils.getInstance()[
                        DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_MEMORY] = list()
                Fn.history(
                    DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_MEMORY], str(mem))
                logging.info(f'MEMORY SET TO {mem}')
            except Exception as e:
                logging.warning(e)
                failed = True

            try:

                cpuusage = "{0:.2f}".format(
                    float(self.get_item(data, "system.cpu.load[percpu,avg5]")))
                if DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_CPU_USAGE] is None:
                    DbUtils.getInstance()[
                        DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_CPU_USAGE] = list()
                Fn.history(
                    DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_CPU_USAGE], str(cpuusage))
                logging.info(f'CPU USAGE SET TO {cpuusage}')
            except Exception as e:
                logging.warning(e)
                failed = True

            try:
                uptime = self.get_item(data, "system.uptime")
                DbUtils.getInstance()[DB_MODULE, id, "uptime"] = str(
                    timedelta(seconds=(int(float(uptime)))))
                logging.info(f'UPTIME SET TO {uptime}')
            except Exception as e:
                logging.warning(e)
                failed = True

            try:

                disktotal = float(self.get_item(data, "vfs.fs.size[/,total]"))
                diskused = float(self.get_item(data, "vfs.fs.size[/,used]"))

                disk = "{0:.2f}".format(100*(diskused/disktotal))
                if DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_DISK] is None:
                    DbUtils.getInstance()[
                        DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_DISK] = list()
                Fn.history(
                    DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_MONITOR_DISK],  str(disk))
                logging.info(f'DISK USAGE SET TO {disk}')

            except Exception as e:
                logging.warning(e)

                failed = True

            try:
                dataset = self.get_item_list(data, "vfs.fs.size")
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
                    logging.info(
                        f'MOUNT POINT { k["point"] } USAGE SET TO {k["usage"]}')
                if DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_LISTS, KEY_MONITOR_MOUNTS] is None:
                    DbUtils.getInstance()[
                        DB_MODULE, id, KEY_MONITOR_LISTS, KEY_MONITOR_MOUNTS] = list()
                DbUtils.getInstance()[DB_MODULE, id,
                                      KEY_MONITOR_LISTS, KEY_MONITOR_MOUNTS] = lst
            except Exception as e:
                logging.warning(e)
                failed = True

            if not failed:
                return RUNNING_STATUS
            else:
                return UNKNOWN_STATUS
