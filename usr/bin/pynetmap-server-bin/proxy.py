#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'


import sys
import os
from database import Database
from utils import Utils
print """
  _____       _   _      _   __  __          _____
 |  __ \     | \ | |    | | |  \/  |   /\   |  __ \\
 | |__) |   _|  \| | ___| |_| \  / |  /  \  | |__) |
 |  ___/ | | | . ` |/ _ \ __| |\/| | / /\ \ |  ___/
 | |   | |_| | |\  |  __/ |_| |  | |/ ____ \| |
 |_|    \__, |_| \_|\___|\__|_|  |_/_/    \_\_|
         __/ |
        |___/
"""


class Proxy:
    def __init__(self):
        self.utils = Utils(Database())

    def build_ssh_command(self, id):
        cmds = []
        try:
            tunnel = self.utils.find_tunnel(id)

            if tunnel != None:
                print " -- tunnel found"
                tip = self.utils.store.get_attr(
                    "base", tunnel, "base.tunnel.ip")
                tport = self.utils.store.get_attr(
                    "base", tunnel, "base.tunnel.port")
                tuser = self.utils.store.get_attr(
                    "base", tunnel, "base.tunnel.user")
                tpass = self.utils.store.get_attr(
                    "base", tunnel, "base.tunnel.password")
                source = "sshpass -p"
                source += tpass.replace("!", "\\!")
                source += " ssh -tt -p "
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

            ip = self.utils.store.get_attr("base", id, "base.net.ip")
            password = self.utils.store.get_attr(
                "base", id, "base.ssh.password")
            username = self.utils.store.get_attr("base", id, "base.ssh.user")
            port = self.utils.store.get_attr("base", id, "base.ssh.port")
            target = "sshpass -p"
            target += password.replace("!", "\\!")
            target += " ssh -tt -p "
            target += "22" if port == None or port == "" else port
            target += " -o StrictHostKeyChecking=no "
            target += username
            target += "@"
            target += ip
            if source != "":
                cmd = source + ' " ' + target + ' " '
            else:
                cmd = target
            return cmd
        except:
            return None


if __name__ == '__main__':
    proxy = Proxy()
    if len(sys.argv) > 1:
        sshcmd = proxy.build_ssh_command(sys.argv[1])
        if sshcmd != None:
            os.system(sshcmd)
            exit(0)

    print """
    __________________________________________________
            This is not an ssh accessible node
    """
