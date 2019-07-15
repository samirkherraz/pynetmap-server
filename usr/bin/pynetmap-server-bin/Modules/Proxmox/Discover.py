#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

from proxmoxer import ProxmoxAPI
from Core.Database.DbUtils import DbUtils
from Core.Utils import Fn
from Core.Utils.SSHLib import SSHLib
from Constants import *

import logging
class Discover:

    def arp_table(self, id):
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
                    except Exception as e:
                        logging.error(e)
                        pass
            except Exception as e:
                logging.error(e)
                pass
        else:
            logging.error("NO SSH COOO")
        return arp

    def find(self, vmid, id):
        for k in self.db.find_children(id):
            if self.db[DB_BASE, k,KEY_DISCOVER_PROXMOX_ID] == vmid:
                return k
        newid = self.db.create(id)
        return newid

    def __init__(self):
        self.db = DbUtils.getInstance()
        self.sshlib = SSHLib()

    def process(self, id):
        logging.info("process "+str(id))
        localport = self.sshlib.open_port(id, "8006")
        try:
            if localport != None:
                ip = "localhost"
                port = str(localport)
            else:
                ip = str(self.db[DB_BASE, id,KEY_NET_IP]).strip()
                port = "8006"

            proxmox = ProxmoxAPI(ip, port=port,
                                 user=str(self.db[DB_BASE, id,KEY_SSH_USER]).strip()+'@pam',
                                 password=str(self.db[DB_BASE, id,KEY_SSH_PASSWORD]).strip(),
                                 verify_ssl=False)

            self.db[DB_MODULE, id,KEY_DISCOVER_PROXMOX_STATUS] =  "Yes"
            logging.info("PVE API ACCES OK")
            FOUND = list()
            for node in proxmox.nodes.get():
                self.db[DB_BASE, id, KEY_NAME] = node['node']
                arp = self.arp_table(id)
                try:
                    for vm in proxmox.nodes(node['node']).qemu.get():
                        k = self.find(vm["vmid"], id)
                        FOUND.append(k)
                        logging.info("DISCOVER :: "+ vm["name"])
                        self.db[DB_BASE, k, KEY_NAME] =  vm["name"]
                        self.db[DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] =  vm["vmid"]
                        self.db[DB_BASE, k, KEY_TYPE] =  "VM"
                        
                        for i in proxmox.nodes(node['node']).qemu(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:
                                    eth = i
                                    mac = proxmox.nodes(node['node']).qemu(
                                        vm["vmid"]).config.get()[i].split("=")[1].split(",")[0]
                                    ip = arp[mac]

                                    self.db[DB_BASE, k, KEY_NET_ETH] =  eth
                                    self.db[DB_BASE, k, KEY_NET_MAC] =  mac
                                    self.db[DB_BASE, k, KEY_NET_IP] =  ip
                                except Exception as e:
                                    logging.error(e)
                                    pass

                except Exception as e:
                    logging.error(e)
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).lxc.get():
                        k = self.find(vm["vmid"], id)
                        FOUND.append(k)

                        self.db[DB_BASE, k, KEY_NAME] =  vm["name"]
                        self.db[DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] =  vm["vmid"]
                        self.db[DB_BASE, k, KEY_TYPE] =  "Container"

                        for i in proxmox.nodes(node['node']).lxc(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:

                                    eth = i
                                    mac = proxmox.nodes(node['node']).lxc(
                                        vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                    ip = arp[mac]
   
                                    self.db[DB_BASE, k, KEY_NET_ETH] =  eth
                                    self.db[DB_BASE, k, KEY_NET_MAC] =  mac
                                    self.db[DB_BASE, k, KEY_NET_IP] =  ip
                                except Exception as e:
                                    logging.error(e)
                                    pass

                except Exception as e :
                    logging.error(e)
                    pass
                try:
                    for vm in proxmox.nodes(node['node']).openvz.get():
                        k = self.find(vm["vmid"], id)
                        FOUND.append(k)
                        self.db[DB_BASE, k, KEY_NAME] =  vm["name"]
                        self.db[DB_BASE, k, KEY_DISCOVER_PROXMOX_ID] =  vm["vmid"]
                        self.db[DB_BASE, k, KEY_TYPE] =  "Container"
                        for i in proxmox.nodes(node['node']).openvz(vm["vmid"]).config.get():
                            if 'net' in i:
                                try:
                                    eth = i
                                    mac = proxmox.nodes(node['node']).openvz(
                                        vm["vmid"]).config.get()[i].split(",")[3].split("=")[1]
                                    ip = arp[mac]
                                    self.db[DB_BASE, k, KEY_NET_ETH] =  eth
                                    self.db[DB_BASE, k, KEY_NET_MAC] =  mac
                                    self.db[DB_BASE, k, KEY_NET_IP] =  ip
                                except Exception as e:
                                    logging.error(e)
                                    pass

                except Exception as e:
                    logging.error(e)
                    pass

            for elm in self.db.find_children(id):
                if elm not in FOUND:
                    self.db.delete(id, elm)
        except Exception as e:
            logging.error(e)
            logging.info("Unable to access proxmox api")
            self.db[DB_MODULE, id,KEY_DISCOVER_PROXMOX_STATUS] =  "No"


        if localport != None:
            self.sshlib.close_port(localport)
