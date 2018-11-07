#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

from .proxmoxer import ProxmoxAPI


class Discover:

    def arp_table(self, id):
        arp = dict()
        ssh = self.utils.open_ssh(id)
        if ssh != None:
            table = self.utils.ssh_exec_read(ssh,
                                                """for i in $(route -n | awk 'NR > 2 && !seen[$1$2]++  {print $8}');do arp-scan -I $i -l --quiet | head -n -3 | tail -n +3 ; done | awk '!seen[$1$2]++ { print $1"="$2;}'""")
            ssh.close()
            try:
                for line in table.split("\n"):
                    try:
                        arp[line.split("=")[1].upper()] = line.split("=")[
                            0].upper()
                    except:
                        pass
            except:
                pass
        return arp

    def find(self, vmid, id):
        for k in self.store.get_children(id):
            if self.store.get_attr("base", k, "base.proxmox.id") == vmid:
                return k
        newid = self.store.create(id)
        self.utils.debug('System::Discovery',
                         self.store.get_attr("base", id, "base.name")+"::"+str(vmid))
        return newid

    def __init__(self, model):
        self.utils = model.utils
        self.store = model.store

    def process(self, id):
        localport = self.utils.open_port(id, "8006")
        try:
            if localport != None:
                ip = "localhost"
                port = str(localport)
            else:
                ip = str(self.store.get_attr(
                    "base", id, "base.net.ip")).strip()
                port = "8006"

            proxmox = ProxmoxAPI(ip, port=port,
                                 user=str(self.store.get_attr(
                                     "base", id, "base.ssh.user")).strip()+'@pam',
                                 password=str(self.store.get_attr(
                                     "base", id, "base.ssh.password")).strip(),
                                 verify_ssl=False)

            self.store.set_attr(
                "module", id, "module.discover.proxmox", "Yes")

            for node in proxmox.nodes.get():
                self.store.set_attr(
                    "base", id, "base.name", node['node'])
                arp = self.arp_table(id)
                try:
                    for vm in proxmox.nodes(node['node']).qemu.get():
                        k = self.find(vm["vmid"], id)
                        self.store.set_attr(
                            "base", k, "base.name", vm["name"])

                        self.store.set_attr(
                            "base", k, "base.proxmox.id", vm["vmid"])
                        self.store.set_attr(
                            "base", k, "base.core.schema", "VM")
                        for i in proxmox.nodes(node['node']).qemu(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:
                                    eth = i
                                    self.store.set_attr(
                                        "base", k, "base.net.eth", eth)
                                    mac = proxmox.nodes(node['node']).qemu(
                                        vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]
                                    self.store.set_attr(
                                        "base", k, "base.net.mac", mac)
                                    ip = arp[mac]

                                    self.store.set_attr(
                                        "base", k, "base.net.ip", ip)

                                except:
                                    pass

                except:
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).lxc.get():
                        k = self.find(vm["vmid"], id)
                        self.store.set_attr(
                            "base", k, "base.name", vm["name"])
                        self.store.set_attr(
                            "base", k, "base.proxmox.id", vm["vmid"])
                        self.store.set_attr(
                            "base", k, "base.core.schema", "Container")

                        for i in proxmox.nodes(node['node']).lxc(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:

                                    eth = i
                                    self.store.set_attr(
                                        "base", k, "base.net.eth", eth)
                                    mac = proxmox.nodes(node['node']).lxc(
                                        vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                    self.store.set_attr(
                                        "base", k, "base.net.mac", mac)
                                    ip = arp[mac]
                                    self.store.set_attr(
                                        "base", k, "base.net.ip", ip)

                                except:
                                    pass

                except:
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).openvz.get():
                        k = self.find(vm["vmid"], id)
                        self.store.set_attr(
                            "base", k, "base.name", vm["name"])
                        self.store.set_attr(
                            "base", k, "base.proxmox.id", vm["vmid"])
                        self.store.set_attr(
                            "base", k, "base.core.schema", "Container")
                        for i in proxmox.nodes(node['node']).openvz(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:
                                    eth = i
                                    self.store.set_attr(
                                        "base", k, "base.net.eth", eth)
                                    mac = proxmox.nodes(node['node']).openvz(
                                        vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                    self.store.set_attr(
                                        "base", k, "base.net.mac", mac)
                                    ip = arp[mac]
                                    self.store.set_attr(
                                        "base", k, "base.net.ip", ip)

                                except:
                                    pass

                except:
                    pass
        except:
            self.store.set_attr(
                "module", id, "module.discover.proxmox", "No")

        if localport != None:
            self.utils.close_port(localport)
