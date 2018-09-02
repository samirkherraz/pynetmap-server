#!/usr/bin/python
import os
from const import NMAP_CORE
import threading


class NMap:
    def ssh_exec_read(self, ssh, cmd):
        out = ""
        ssh_stdin, stdout, ssh_stderr = ssh.exec_command(cmd, get_pty=True)
        for line in stdout.read().splitlines():
            if line != "":
                out += line

        return str(out).strip()

    def __init__(self, l):
        self.passed = []
        self.arp = dict()
        self.process(l)

    def core_writter(self, elm):
        try:
            if str(elm["base.tunnel.ip"]).strip() == "" or str(elm["base.tunnel.password"]).strip() == "" or str(
                    elm["base.tunnel.user"]).strip() == "":
                return

            cmd = NMAP_CORE
            cmd = cmd.replace("[ID]", str(elm["base.core.name"]).strip())
            cmd = cmd.replace("[IP]", str(elm["base.tunnel.ip"]).strip())
            cmd = cmd.replace("[USER]", str(elm["base.tunnel.user"]).strip())
            cmd = cmd.replace("[PORT]", str(elm["base.tunnel.port"]).strip())
            cmd = cmd.replace("[NET]", str(elm["base.tunnel.network"]).strip())
            cmd = cmd.replace("[PASS]", str(
                elm["base.tunnel.password"]).replace("'", "\\'").strip())
            cmd = cmd.replace("[NET]", str(elm["base.tunnel.network"]).strip())

        except:
            return

        if cmd not in self.passed:
            self.passed.append(cmd)

    def process(self, lst):
        for elm in lst.find_by_schema("Serveur"):
            self.core_writter(lst.find_by_id(elm))

    def get(self):
        self.read()
        return self.arp

    def read(self):
        k = "IFS=$'\\n';for i in $( "
        i = 0
        for cmd in self.passed:
            i += 1
            k += cmd
            if i < len(self.passed):
                k += " & "
        k += " ); do echo -e $i;done"
        popen = os.popen(k)
        output = popen.read().split("\n")
        popen.close()
        for line in output:
            if line.count('.') < 3 or line.count(':') < 5:
                continue

            args = line.split("\t")
            self.arp[args[1].upper()] = args[0].upper()
