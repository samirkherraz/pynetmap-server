

import os
import sys
import logging
logging.basicConfig(filename="/dev/null", level=logging.DEBUG)

#from model import Model
from Core.Database.DbUtils import DbUtils
from Constants import *
from Core.Utils.SSHLib import SSHLib
class Proxy:

    def __init__(self, id):
        db = DbUtils.getInstance()
        sshlib = SSHLib()
        localport = None
        try:
            port = db[DB_BASE,  id, KEY_SSH_PORT]
            localport = sshlib.open_port(id, "22" if port == None or port == "" else port)
            ip = "127.0.0.1" 
            password = db[DB_BASE, id, KEY_SSH_PASSWORD]
            username = db[DB_BASE, id, KEY_SSH_USER]
            target = "sshpass -p"
            target += password.replace("!", "\\!")
            target += " ssh -q -tt -p "
            target += localport 
            target += " -o StrictHostKeyChecking=no "
            target += username
            target += "@"
            target += ip
            shell = """ 
                export TERM=xterm ;
                NSHELL=$(cat /etc/passwd | grep $USER ; ) 
                [ -f /etc/rc.initial ] && /etc/rc.initial && exit 0 || [ -f /etc/rc.initial ] && exit 0 ;
                [ -f /bin/bash ] && /bin/bash && exit 0 || [ -f /bin/bash ] && exit 0 ;
                [ -f /bin/mksh ] && /bin/mksh && exit 0 || [ -f /bin/mksh ] && exit 0 ;
                [ -f /bin/sh ] && /bin/sh && exit 0 || [ -f /bin/sh ] && exit 0 ;
               

                echo "No Shell Found"
                """
            cmd = target + ' "'+shell+'" '
            os.system(cmd)
            sshlib.close_port(localport)

        except Exception as e:
            pass
