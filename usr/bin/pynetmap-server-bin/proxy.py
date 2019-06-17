#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'


import os
import sys
import logging
logging.basicConfig(filename="test.log", level=logging.DEBUG)

#from model import Model
from Core.Database.DbUtils import DbUtils
from Constants import *
print(""" 
  _____       _   _      _   __  __          _____
 |  __ \     | \ | |    | | |  \/  |   /\   |  __ \\
 | |__) |   _|  \| | ___| |_| \  / |  /  \  | |__) |
 |  ___/ | | | . ` |/ _ \ __| |\/| | / /\ \ |  ___/
 | |   | |_| | |\  |  __/ |_| |  | |/ ____ \| |
 |_|    \__, |_| \_|\___|\__|_|  |_/_/    \_\_|
         __/ |
        |___/

""")

class Proxy:

    def ip_net_in_network(self,ip, net):
        ipaddr = int(''.join(['%02x' % int(x) for x in ip.split('.')]), 16)
        netstr, bits = net.split('/')
        netaddr = int(''.join(['%02x' % int(x)
                               for x in netstr.split('.')]), 16)
        mask = (0xffffffff << (32 - int(bits))) & 0xffffffff
        return (ipaddr & mask) == (netaddr & mask)


    def find_tunnel(self, id):
        ip = str(self.db[[DbUtils.BASE, id,KEY_NET_IP]]).strip()

        path = self.db.find_path(id)
        if len(path) <= 2:
            return None

        pnetwork = self.db[[DbUtils.BASE, path[1], KEY_TUNNEL_NETWORK]]

        if pnetwork != None and pnetwork != "" and self.ip_net_in_network(ip, str(pnetwork).strip()):
            return path[1]

        for key in self.db.find_children(path[0]):
            try:
                network = str(self.db[[DbUtils.BASE, key, KEY_TUNNEL_NETWORK]]).strip()
                if self.ip_net_in_network(ip, network):
                    return key

            except:
                pass
        return None

    def __init__(self):
        self.db = DbUtils.getInstance()

    def build_ssh_command(self, id):
        cmds = []
        try:
            tunnel = self.find_tunnel(id)

            if tunnel != None:
                tip = self.db[[DbUtils.BASE, tunnel, KEY_TUNNEL_IP]]
                tport = self.db[[DbUtils.BASE, tunnel, KEY_TUNNEL_PORT]]
                tuser = self.db[[DbUtils.BASE, tunnel, KEY_TUNNEL_USER]]
                tpass = self.db[[DbUtils.BASE, tunnel, KEY_TUNNEL_PASSWORD]]
                source = "sshpass -p"
                source += tpass.replace("!", "\\!")
                source += " ssh -q -tt -p "
                source += "22" if tport == None or tport == "" else tport
                source += " -o StrictHostKeyChecking=no "
                source += tuser
                source += "@"
                source += tip
                cmds.append(source)
                dependencies = "command -v sshpass | apt-get install sshpass -y"
                os.system(source + " '"+dependencies+"' > /dev/null 2>&1 ")
            else:
                source = ""

            ip = self.db[[DbUtils.BASE, id, KEY_NET_IP]]
            password = self.db[[DbUtils.BASE, id, KEY_SSH_PASSWORD]]
            username = self.db[[DbUtils.BASE, id, KEY_SSH_USER]]
            port = self.db[[DbUtils.BASE,  id, KEY_SSH_PORT]]
            target = "sshpass -p"
            target += password.replace("!", "\\!")
            target += " ssh -q -tt -p "
            target += "22" if port == None or port == "" else port
            target += " -o StrictHostKeyChecking=no "
            target += username
            target += "@"
            target += ip
            shell = "export TERM=xterm ; exec /bin/bash  || exec /bin/sh || echo No Shell Found"
            if source != "":
                cmd = source + ' " ' + target + ' \\"'+shell+'\\" " '
            else:
                cmd = target + ' "'+shell+'" '
            return cmd

        except ValueError as e:
            return None


if __name__ == '__main__':
    proxy = Proxy()
    if len(sys.argv) > 1:
        sshcmd = proxy.build_ssh_command(sys.argv[1])
        if sshcmd != None:
            os.system(sshcmd)
            exit(0)

    print("""
    ___________________________________________________

            This is not an ssh accessible node
    ___________________________________________________
    """)
