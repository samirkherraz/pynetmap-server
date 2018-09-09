import paramiko
import os
from threading import Lock
from const import HISTORY
import random
import string


class Utils:

    def ssh_exec_read(ssh, cmd, name="System"):
        out = ""
        try:
            _, stdout, _ = ssh.exec_command(cmd, get_pty=True, timeout=15)
            output = stdout.read()
            for line in output.splitlines():
                if line.strip() != "":
                    out += line.strip() + "\n"
            return str(out).strip()
        except:
            Utils.debug(name, "Timeout for command\n"+cmd, 1)

    # def open_ssh(el):
    #     try:
    #         os.system("rm ~/.ssh/known_hosts > /dev/null 2>&1")
    #     except:
    #         pass
    #     ssh = paramiko.SSHClient()
    #     ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    #     try:
    #         try:
    #             if "base.ssh.port" in el:
    #                 sport = int(str(el["base.ssh.port"]).strip())
    #             else:
    #                 sport = 22
    #         except:
    #             sport = 22

    #         ssh.connect(str(el["base.net.ip"]).strip(),
    #                     username=str(el["base.ssh.user"]).strip(), port=sport, password=str(el["base.ssh.password"]).strip(), timeout=1)
    #         return ssh
    #     except:
    #         return None

    def open_ssh(id):
        try:
            os.system("rm ~/.ssh/known_hosts > /dev/null 2>&1")
        except:
            pass
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        ssh.connect("localhost", username="pynetmap",
                    password="Shinu3G!", timeout=1)
        return ssh

    def debug(elm, msg, level=0):
        if level == Utils.DEBUG_NONE:
            return
        elif level == Utils.DEBUG_NOTICE:
            lvl = "[  Notice  ]"
        elif level == Utils.DEBUG_WARNING:
            lvl = "[  Warning ]"
        elif level == Utils.DEBUG_ERROR:
            lvl = "[  Error   ]"

        head = lvl + " [ " + elm
        while len(head) < 35:
            head += " "
        head += " ] - "
        with Utils.STDOUT:
            print head + msg

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

    history_append = staticmethod(history_append)
    open_ssh = staticmethod(open_ssh)
    ssh_exec_read = staticmethod(ssh_exec_read)
    debug = staticmethod(debug)

    DEBUG_ERROR = 2
    DEBUG_NOTICE = 0
    DEBUG_NONE = -1
    DEBUG_WARNING = 1
    STDOUT = Lock()
