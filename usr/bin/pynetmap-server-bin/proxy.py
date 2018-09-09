#!/usr/bin/python2.7

import pty
import sys
import os
from subprocess import Popen
import struct
from database import Database
import socket
from contextlib import closing
# print """

#   _____       _   _      _   __  __          _____
#  |  __ \     | \ | |    | | |  \/  |   /\   |  __ \\
#  | |__) |   _|  \| | ___| |_| \  / |  /  \  | |__) |
#  |  ___/ | | | . ` |/ _ \ __| |\/| | / /\ \ |  ___/
#  | |   | |_| | |\  |  __/ |_| |  | |/ ____ \| |
#  |_|    \__, |_| \_|\___|\__|_|  |_/_/    \_\_|
#          __/ |
#         |___/
# """


# print """
#   __________________________________________________
#         This is not an ssh accessible node
# """

class Proxy:
    def __init__(self):
        self.store = Database()

    def find_free_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('', 0))
        port = s.getsockname()[1]
        return port

    def map_port(self, id, port):
        try:
            tunnel = self.find_tunnel(id)
            ip = self.store.get_attr("base", id, "base.net.ip")
            localport = self.find_free_port()
            if tunnel != None:
                tip = self.store.get_attr("base", tunnel, "base.tunnel.ip")
                tport = self.store.get_attr(
                    "base", tunnel, "base.tunnel.port")
                tuser = self.store.get_attr(
                    "base", tunnel, "base.tunnel.user")
                tpass = self.store.get_attr(
                    "base", tunnel, "base.tunnel.password")
                source = "sshpass -p"
                source += tpass.replace("!", "\\!")
                source += " ssh -p "
                source += "22" if tport == None or tport == "" else tport
                source += " -o StrictHostKeyChecking=no "
                source += " -L "
                source += str(localport)
                source += ":"
                source += ip
                source += ":"
                source += port
                source += " "
                source += tuser
                source += "@"
                source += tip

            else:
                source = ""
        except ValueError as e:
            print e
            return None

    def ip_net_in_network(self, ip, net):
        ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
        netstr, bits = net.split('/')
        netaddr = int(''.join(['%02x' % int(x)
                               for x in netstr.split('.')]), 16)
        mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
        return (ipaddr & mask) == (netaddr & mask)

    def find_tunnel(self, id):
        ip = self.store.get_attr(
            "base", id, "base.net.ip")

        for key in self.store.find_by_schema("Serveur"):
            try:
                network = self.store.get_attr(
                    "base", key, "base.tunnel.network")
                if self.ip_net_in_network(ip, network):
                    return key

            except:
                pass
        return None

    def build_ssh_command(self, id):
        try:
            tunnel = self.find_tunnel(id)

            if tunnel != None:
                tip = self.store.get_attr("base", tunnel, "base.tunnel.ip")
                tport = self.store.get_attr(
                    "base", tunnel, "base.tunnel.port")
                tuser = self.store.get_attr(
                    "base", tunnel, "base.tunnel.user")
                tpass = self.store.get_attr(
                    "base", tunnel, "base.tunnel.password")
                source = "sshpass -p"
                source += tpass.replace("!", "\\!")
                source += " ssh -tt -p "
                source += "22" if tport == None or tport == "" else tport
                source += " -o StrictHostKeyChecking=no "
                source += tuser
                source += "@"
                source += tip
                dependencies = "command -v sshpass | apt-get install sshpass -y"
                os.system(source + " '"+dependencies+"' > /dev/null 2>&1 ")
            else:
                source = ""

            ip = self.store.get_attr("base", id, "base.net.ip")
            password = self.store.get_attr(
                "base", id, "base.ssh.password")
            username = self.store.get_attr("base", id, "base.ssh.user")
            port = self.store.get_attr("base", id, "base.ssh.port")
            target = "sshpass -p"
            target += password.replace("!", "\\!")
            target += " ssh -tt -p "
            target += "22" if port == None or port == "" else port
            target += " -o StrictHostKeyChecking=no "
            target += username
            target += "@"
            target += ip

            if source != "":
                cmd = source + " '" + target.replace("'", "\\'") + "'"
            else:
                cmd = target
            return cmd
        except:
            return None


if __name__ == '__main__':
    proxy = Proxy()
    if len(sys.argv) > 1:
        proxy.map_port(sys.argv[1], "80")
        cmd = proxy.build_ssh_command(sys.argv[1])
        if cmd != None:
            #pty.spawn(["/bin/bash", "-c", cmd])
            os.system("/bin/bash -c \""+cmd+"\"")
