#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'


from datetime import timedelta
from proxmoxer import ProxmoxAPI


class Monitor:

    def __init__(self, store, utils):
        self.utils = utils
        self.store = store

    def process(self, id):
        proxmoxid = self.store.find_parent(id)
        localport = self.utils.open_port(proxmoxid, "8006")
        status = self.utils.UNKNOWN_STATUS
        try:
            if localport != None:
                ip = "localhost"
                port = str(localport)
            else:
                ip = str(self.store.get_attr(
                    "base", proxmoxid, "base.net.ip")).rstrip()
                port = "8006"

            proxmox = ProxmoxAPI(ip, port=port,
                                 user=str(self.store.get_attr(
                                     "base", proxmoxid, "base.ssh.user")).strip()+'@pam',
                                 password=str(self.store.get_attr(
                                     "base", proxmoxid, "base.ssh.password")).strip(),
                                 verify_ssl=False)
            source = proxmox.nodes(self.store.get_attr(
                "base", proxmoxid, "base.name")).qemu(self.store.get_attr(
                    "base", id, "base.proxmox.id")).get("status/current")

            try:
                mem = float(float(source["mem"]) /
                            float(source["maxmem"])) * 100
                self.store.set_attr("module", id, "module.state.history.memory",
                                    self.utils.history_append(self.store.get_attr(
                                        "module", id, "module.state.history.memory"), mem))

            except:
                pass

            nbcpus = None
            try:
                nbcpus = source["cpus"]
                self.store.set_attr(
                    "module", id, "module.state.nbcpu", nbcpus)
            except:
                pass

            try:
                nbcpus = source["maxcpu"]
                self.store.set_attr(
                    "module", id, "module.state.nbcpu", nbcpus)
            except:
                pass

            try:
                cpuusage = float(source["cpu"]) * 100
                self.store.set_attr("module", id, "module.state.history.cpuusage",
                                    self.utils.history_append(self.store.get_attr(
                                        "module", id, "module.state.history.cpuusage"), cpuusage))
            except:
                pass

            try:
                uptime = str(timedelta(seconds=(source["uptime"])))
                self.store.set_attr(
                    "module", id, "module.state.uptime", uptime)
            except:
                pass

            try:
                disk = float(float(source["disk"]) /
                             float(source["maxdisk"])) * 100
                self.store.set_attr("module", id, "module.state.history.disk",
                                    self.utils.history_append(self.store.get_attr(
                                        "module", id, "module.state.history.disk"), disk))
            except:
                pass

            if source["status"] == "running":
                status = self.utils.RUNNING_STATUS
            elif source["status"] == "stopped":
                status = self.utils.STOPPED_STATUS

        except:
            pass
        if localport != None:
            self.utils.close_port(localport)
        return status
