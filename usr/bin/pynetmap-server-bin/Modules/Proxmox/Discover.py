#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

from proxmoxer import ProxmoxAPI

from Constants import *
from Core.Database.DbUtils import DbUtils, call_persist_after
from Core.Utils import Fn
from Core.Utils.Logging import getLogger
from Core.Utils.SSHLib import SSHLib


class Discover:

    def arp_table(self, id):
        logging = getLogger(__package__, DbUtils.getInstance()[
                            DB_BASE, id, KEY_NAME])
        arp = dict()
        ssh = self.sshlib.open_ssh(id)
        if ssh != None:
            table = self.sshlib.ssh_exec_read(ssh,
                                              """for i in $(route -n | awk 'NR > 2 && !seen[$1$2]++  {print $8}');do arp-scan -I $i -l --quiet | head -n -3 | tail -n +3 ; done | awk '!seen[$1$2]++ { print $1"="$2;}'""")
            ssh.close()
            try:
                for line in table.split("\n"):
                    try:
                        arp[line.split("=")[1].upper()] = str(line.split("=")[
                            0].upper())
                        arp[line.split("=")[0].upper()] = str(line.split("=")[
                            1].upper())
                    except:
                        pass
            except:
                pass
        else:
            logging.error("UNABLE TO OPEN PORT FOR SSH")
        return arp

    def find(self, vmid, id):
        for k in DbUtils.getInstance().find_children(id):
            if DbUtils.getInstance()[DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] == vmid:
                return k
        newid = DbUtils.getInstance().create(id)
        return newid

    def __init__(self):
        self.sshlib = SSHLib()

    @call_persist_after
    def process(self, id):
        logging = getLogger(__package__, DbUtils.getInstance()[
                            DB_BASE, id, KEY_NAME])
        logging.info(f'START PROCESSING')
        localport = self.sshlib.open_port(id, "8006")
        try:
            if localport != None:
                ip = "localhost"
                port = str(localport)
            else:
                ip = str(DbUtils.getInstance()[
                         DB_BASE, id, KEY_NET_IP]).strip()
                port = "8006"

            proxmox = ProxmoxAPI(ip, port=port,
                                 user=str(DbUtils.getInstance()[
                                          DB_BASE, id, KEY_SSH_USER]).strip()+'@pam',
                                 password=str(DbUtils.getInstance()[
                                              DB_BASE, id, KEY_SSH_PASSWORD]).strip(),
                                 verify_ssl=False)

            DbUtils.getInstance()[DB_MODULE, id,
                                  KEY_DISCOVER_PROXMOX_STATUS] = "Yes"
            logging.info("PVE API ACCES OK")
            FOUND = list()
            for node in proxmox.nodes.get():
                DbUtils.getInstance()[DB_BASE, id, KEY_NAME] = node['node']
                arp = self.arp_table(id)
                try:
                    for vm in proxmox.nodes(node['node']).qemu.get():
                        k = self.find(vm["vmid"], id)
                        FOUND.append(k)
                        logging.info("DISCOVERED QEMU VM : " + vm["name"])
                        DbUtils.getInstance()[DB_BASE, k,
                                              KEY_NAME] = vm["name"]
                        DbUtils.getInstance()[
                            DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] = vm["vmid"]
                        DbUtils.getInstance()[DB_BASE, k, KEY_TYPE] = "VM"

                        for i in proxmox.nodes(node['node']).qemu(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:
                                    eth = i
                                    mac = proxmox.nodes(node['node']).qemu(
                                        vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]
                                    ip = arp[mac]

                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_ETH] = eth
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_MAC] = mac
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_IP] = ip
                                except:
                                    pass

                except:
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).lxc.get():
                        k = self.find(vm["vmid"], id)
                        FOUND.append(k)
                        logging.info(
                            "DISCOVERED LXC CONTAINER : " + vm["name"])
                        DbUtils.getInstance()[DB_BASE, k,
                                              KEY_NAME] = vm["name"]
                        DbUtils.getInstance()[
                            DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] = vm["vmid"]
                        DbUtils.getInstance()[DB_BASE, k,
                                              KEY_TYPE] = "Container"

                        for i in proxmox.nodes(node['node']).lxc(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:

                                    eth = i
                                    mac = proxmox.nodes(node['node']).lxc(
                                        vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                    ip = arp[mac]

                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_ETH] = eth
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_MAC] = mac
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_IP] = ip
                                except:
                                    pass

                except:
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).openvz.get():
                        k = self.find(vm["vmid"], id)
                        FOUND.append(k)
                        logging.info(
                            "DISCOVERED OPENVZ CONTAINER : " + vm["name"])
                        DbUtils.getInstance()[DB_BASE, k,
                                              KEY_NAME] = vm["name"]
                        DbUtils.getInstance()[
                            DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] = vm["vmid"]
                        DbUtils.getInstance()[DB_BASE, k,
                                              KEY_TYPE] = "Container"
                        for i in proxmox.nodes(node['node']).openvz(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:
                                    eth = i
                                    mac = proxmox.nodes(node['node']).openvz(
                                        vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                    ip = arp[mac]
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_ETH] = eth
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_MAC] = mac
                                    DbUtils.getInstance()[
                                        DB_BASE, k, KEY_NET_IP] = ip
                                except:
                                    pass

                except:
                    pass

            for elm in DbUtils.getInstance().find_children(id):
                if elm not in FOUND:
                    DbUtils.getInstance().delete(id, elm)
        except:
            pass
            logging.warning(f'UNABLE TO ACCESS PVE')
            DbUtils.getInstance()[DB_MODULE, id,
                                  KEY_DISCOVER_PROXMOX_STATUS] = "No"

        if localport != None:
            self.sshlib.close_port(localport)
