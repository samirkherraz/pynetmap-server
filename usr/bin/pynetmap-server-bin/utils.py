#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import os
import socket
import threading
from threading import Lock

import paramiko
from const import HISTORY, DEBUG
from forward import forward_tunnel
from threading import Thread

paramiko.util.log_to_file("/dev/null")


class Utils:

    def __init__(self, database):
        self.store = database
        self.ports = dict()
        self._portsl = Lock()

    def ssh_exec_read(ssh, cmd, name="System"):
        out = ""
        try:
            _, stdout, _ = ssh.exec_command(
                cmd, get_pty=True, timeout=15)
            output = stdout.read()
            for line in output.splitlines():
                if line.strip() != "":
                    out += line.strip() + "\n"
            return str(out).strip()
        except:
            Utils.debug(name, "SSH Timeout for command\n"+cmd, 1)

    def ip_net_in_network(ip, net):
        ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
        netstr, bits = net.split('/')
        netaddr = int(''.join(['%02x' % int(x)
                               for x in netstr.split('.')]), 16)
        mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
        return (ipaddr & mask) == (netaddr & mask)

    def find_tunnel(self, id):
        ip = str(self.store.get_attr(
            "base", id, "base.net.ip")).strip()

        path = self.store.find_path(id)
        pnetwork = self.store.get_attr(
            "base", path[1], "base.tunnel.network")

        if pnetwork != None and pnetwork != "" and self.ip_net_in_network(ip, str(pnetwork).strip()):
            return path[1]

        for key in self.store.get_children(path[0]):
            try:
                network = str(self.store.get_attr(
                    "base", key, "base.tunnel.network")).strip()
                if self.ip_net_in_network(ip, network):
                    return key

            except:
                pass
        return None

    def open_ssh(self, id):
        try:
            os.system("rm ~/.ssh/known_hosts > /dev/null 2>&1")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ip = str(self.store.get_attr("base", id, "base.net.ip")).strip()
            password = str(self.store.get_attr(
                "base", id, "base.ssh.password")).strip()
            username = str(self.store.get_attr(
                "base", id, "base.ssh.user")).strip()
            port = self.store.get_attr(
                "base", id, "base.ssh.port")
            tunnel = self.find_tunnel(id)
            if tunnel != None:
                tip = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.ip")).strip()
                tport = self.store.get_attr(
                    "base", tunnel, "base.tunnel.port")
                tuser = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.user")).strip()
                tpass = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.password")).strip()
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
        except:
            return None

    def debug(elm, msg, level=0):

        if level == Utils.DEBUG_NOTICE:
            lvl = "[  Notice  ]"
            if not DEBUG:
                return
        elif level == Utils.DEBUG_WARNING:
            lvl = "[  Warning ]"
            if not DEBUG:
                return
        elif level == Utils.DEBUG_ERROR:
            lvl = "[  Error   ]"
        else:
            return

        head = lvl + " [ " + str(elm)
        while len(head) < 35:
            head += " "
        head += " ] - "
        with Utils.STDOUT:
            print (head + msg)

    def history_append(lst, value):
        if lst == None:
            lst = []
        summ = 0
        i = 0
        if len(lst) > HISTORY:
            while len(lst) > HISTORY/2:
                i += 1
                summ += lst.pop()
            if i > 0:
                lst[0] = (lst[0] + summ) / (i+1)
        lst.append(float(value) if value != None else 0)
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
                ip = str(self.store.get_attr(
                    "base", id, "base.net.ip")).strip()
                tip = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.ip")).strip()
                tport = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.port")).strip()
                tuser = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.user")).strip()
                tpass = str(self.store.get_attr(
                    "base", tunnel, "base.tunnel.password")).strip()

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

                    self.debug("System::Forwarding",
                               "Port "+ip+":"+port+" Mapped to localhost:"+localport)
                    return localport
                except:

                    self.debug("System::Forwarding",
                               "Unable to map "+ip+":"+port+" to localhost:"+localport)
                    return None
            else:
                self.debug("System::Forwarding",
                           "Not required")
                return None
        except:
            self.debug("System::Forwarding",
                       "Not required")
            return None

    def close_port(self, port):
        with self._portsl:
            self.ports[str(port)].shutdown()
            self.ports[str(port)+"TR"].close()
            del self.ports[str(port)]
            del self.ports[str(port)+"TH"]
            del self.ports[str(port)+"TR"]
        self.debug("System",
                   "Port "+port+" Closed.")

    history_append = staticmethod(history_append)
    debug = staticmethod(debug)
    ip_net_in_network = staticmethod(ip_net_in_network)
    ssh_exec_read = staticmethod(ssh_exec_read)
    DEBUG_ERROR = 2
    DEBUG_NOTICE = 0
    DEBUG_NONE = -1
    DEBUG_WARNING = 1

    RUNNING_STATUS = "running"
    STOPPED_STATUS = "stopped"
    UNKNOWN_STATUS = "unknown"

    STDOUT = Lock()
