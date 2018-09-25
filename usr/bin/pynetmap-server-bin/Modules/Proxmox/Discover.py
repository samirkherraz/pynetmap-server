#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

from proxmoxer import ProxmoxAPI


class Discover:

    def arp_table(self, id):
        ssh = self.utils.open_ssh(self.store.get("base", id))
        if ssh != None:
            table = self.utils.ssh_exec_read(ssh,
                                             """for i in $(route -n | awk 'NR > 2 && !seen[$1$2]++  {print $8}');do arp-scan -I $i -l --quiet | head -n -3 | tail -n +3 ; done | awk '!seen[$1$2]++ { print $1"="$2;}'""")
            ssh.close()
            try:
                for line in table.split("\n"):
                    try:
                        self.arp[line.split("=")[1].upper()] = line.split("=")[
                            0].upper()
                    except:
                        pass
            except:
                pass

    def find(self, name, id):
        for k in self.store.get_children(id):
            if self.store.get_attr("base", k, "base.name") == name:
                return k
        newid = self.store.create(id)
        return newid

    def __init__(self, store, utils):
        self.utils = utils
        self.store = store

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
                self.arp_table(id)
                try:
                    for vm in proxmox.nodes(node['node']).qemu.get():
                        k = self.proxmox_find(vm["name"], id)
                        self.store.set_attr(
                            "base", k, "base.name", vm["name"])
                        self.store.set_attr(
                            "base", k, "base.vmid", vm["vmid"])
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

                except:
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).lxc.get():
                        k = self.proxmox_find(vm["name"], id)
                        self.store.set_attr(
                            "base", k, "base.name", vm["name"])
                        self.store.set_attr(
                            "base", k, "base.vmid", vm["vmid"])
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

                except:
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).openvz.get():
                        k = self.proxmox_find(vm["name"], id)
                        self.store.set_attr(
                            "base", k, "base.name", vm["name"])
                        self.store.set_attr(
                            "base", k, "base.vmid", vm["vmid"])
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

                except:
                    pass
        except:
            self.store.set_attr(
                "module", id, "module.discover.proxmox", "No")

        if localport != None:
            self.utils.close_port(localport)
