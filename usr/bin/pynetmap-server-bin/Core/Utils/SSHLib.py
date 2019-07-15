#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import os
import random
import socket
import string
import time
from threading import Lock, Thread
from Core.Database.DbUtils import DbUtils
import logging
import paramiko
from Constants import *

from .forward import forward_tunnel

paramiko.util.log_to_file("/dev/null")


class SSHLib:

    def __init__(self):
        self.db = DbUtils.getInstance()
        self.ports = dict()
        self._portsl = Lock()

    def ssh_exec_read(ssh, cmd, name="System"):
        out = ""
        try:
            _, stdout, _ = ssh.exec_command(
                cmd, get_pty=True, timeout=15)
            output = stdout.readlines()
            for line in output:
                if line.strip() != "":
                    out += str(line.strip()) + str("\n")
            return str(out).strip()
        except ValueError as e:
            logging.error(e)

    def ip_net_in_network(ip, net):
        ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
        netstr, bits = net.split('/')
        netaddr = int(''.join(['%02x' % int(x)
                               for x in netstr.split('.')]), 16)
        mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
        return (ipaddr & mask) == (netaddr & mask)

    def find_tunnel(self, id):
        ip = str(self.db[DB_BASE, id, KEY_NET_IP]).strip()

        path = self.db.find_path(id)
        if len(path) <= 2:
            return None

        pnetwork = self.db[DB_BASE, path[1], KEY_TUNNEL_NETWORK]

        if pnetwork != None and pnetwork != "" and self.ip_net_in_network(ip, str(pnetwork).strip()):
            return path[1]

        for key in self.db.get_children(path[0]):
            try:
                network = str(self.db[DB_BASE, key, KEY_TUNNEL_NETWORK]).strip()
                if self.ip_net_in_network(ip, network):
                    return key

            except Exception as e:
                logging.error(e)
                pass
        return None

    def open_ssh(self, id):
        try:
            os.system("rm ~/.ssh/known_hosts > /dev/null 2>&1")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ip = str(self.db[DB_BASE, id, KEY_NET_IP]).strip()
            password = str(self.db[DB_BASE, id, KEY_SSH_PASSWORD]).strip()
            username = str(self.db[DB_BASE, id, KEY_SSH_USER]).strip()
            port = self.db[DB_BASE, id, KEY_SSH_PORT]
            tunnel = self.find_tunnel(id)
            if tunnel != None:
                tip = str(self.db[DB_BASE, tunnel, KEY_TUNNEL_IP]).strip()
                tport = self.db[DB_BASE, tunnel, KEY_TUNNEL_PORT]
                tuser = str(self.db[DB_BASE, tunnel, KEY_TUNNEL_USER]).strip()
                tpass = str(self.db[DB_BASE, tunnel, KEY_TUNNEL_PASSWORD]).strip()
                source = "sshpass -p"
                source += tpass.replace("!", "\\!")
                source += " ssh -p "
                source += ("22" if tport == None or tport ==
                           "" else str(tport))
                source += " -o StrictHostKeyChecking=no "
                source += tuser
                source += "@"
                source += tip
                source += " nc -w 15 "+ip+" " + \
                    ("22" if port == None or port == "" else str(port))
                proxy = paramiko.ProxyCommand(source)
                ssh.connect(ip, username=username,
                            password=password, sock=proxy, timeout=5)
            else:
                ssh.connect(ip, username=username,
                            password=password, timeout=5)

            return ssh
        except Exception as e:
            logging.error(e)
            return None

    def history_append(lst, value):
        if lst == None:
            lst = []
        HISTORY = self.db[DB_SERVER, "trigger", "history_keep"]
        if len(lst) > HISTORY:
            while len(lst) > HISTORY/2:
                lst.pop()

        val = dict()
        val["date"] = time.time()
        val["value"] = float(value) if value != None else 0
        lst.append(val)
        return lst

    def find_free_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        return port

    def open_port(self, id, port):
        try:
            tunnel = self.find_tunnel(id)
            localport = str(self.find_free_port()).strip()
            if tunnel != None:
                ip = str(self.db[DB_BASE, id, KEY_NET_IP]).strip()
                tip = str(self.db[DB_BASE, tunnel, KEY_TUNNEL_IP]).strip()
                tport = self.db[DB_BASE, tunnel, KEY_TUNNEL_PORT]
                tuser = str(self.db[DB_BASE, tunnel, KEY_TUNNEL_USER]).strip()
                tpass = str(self.db[DB_BASE, tunnel, KEY_TUNNEL_PASSWORD]).strip()
                try:

                    self.ports[localport +
                               "TR"] = paramiko.Transport((tip, int(tport)))

                    self.ports[localport +
                               "TR"].connect(username=tuser, password=tpass)

                    self.ports[localport] = forward_tunnel(
                        int(localport), ip, int(port), self.ports[localport+"TR"])
                    self.ports[localport+"TH"] = Thread(
                        target=self.ports[localport].serve_forever)
                    self.ports[localport+"TH"].daemon = True
                    self.ports[localport+"TH"].start()

                    
                    return localport
                except Exception as e:
                    logging.error(e)

                   
                    return None
            else:
              
                return None
        except Exception as e:
            logging.error(e)
            return None

    def close_port(self, port):
        with self._portsl:
            self.ports[str(port)].shutdown()
            self.ports[str(port)+"TR"].close()
            del self.ports[str(port)]
            del self.ports[str(port)+"TH"]
            del self.ports[str(port)+"TR"]
      

    ip_net_in_network = staticmethod(ip_net_in_network)
    ssh_exec_read = staticmethod(ssh_exec_read)
  