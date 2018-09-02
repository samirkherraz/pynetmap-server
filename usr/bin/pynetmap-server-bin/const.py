import os
import ConfigParser
from threading import Lock
CONFIG_FILE = "/etc/pynetmap-server/global.conf"
configuration = ConfigParser.ConfigParser()
with open(CONFIG_FILE) as fp:
    configuration.readfp(fp)

LISTENING_PORT = configuration.getint("Server", "Port")

BACKUP_DIR = configuration.get("Storage", "Backup")
WORKING_DIR = configuration.get("Storage", "Base")

ADMIN_USERNAME = configuration.get("Authentification", "Login")
ADMIN_PASSWORD = configuration.get("Authentification", "Password")
HISTORY = configuration.getint("Statistics", "History")
UPDATE_INTERVAL = configuration.getint("Statistics", "Refresh")

TUNNEL_HEADER = """killall sshuttle > /dev/null 2>&1"""
TUNNEL_CORE = """sshuttle -r [USER]@[IP] [NET] -e 'sshpass -p[PASS] ssh -p [PORT] -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=0'  > /dev/null 2>&1"""
NMAP_CORE = """sshpass -p[PASS] ssh -p [PORT] -o StrictHostKeyChecking=no [USER]@[IP] "apt-get install arp-scan -y 2> /dev/null ; arp-scan --quiet [NET]; ifconfig | grep -E '(inet |HWaddr|ether)' | grep -v '127.0.0.1' | awk '{ printf \$2; getline; print \\"\\t\\" \$2 }' " """

EXIT_ERROR_LOCK = 1
EXIT_ERROR_CORRUPT_DB = 2
EXIT_SUCCESS = 0

DEBUG_ERROR = 2
DEBUG_NOTICE = 0
DEBUG_NONE = -1
DEBUG_WARNING = 1

STDOUT = Lock()


class Debug:
    def __init__(self, elm, msg, level=0):
        if level == DEBUG_NONE:
            return
        elif level == DEBUG_NOTICE:
            lvl = "[  Notice  ]"
        elif level == DEBUG_WARNING:
            lvl = "[  Warning ]"
        elif level == DEBUG_ERROR:
            lvl = "[  Error   ]"

        head = lvl + " [ " + elm
        while len(head) < 35:
            head += " "
        head += " ] - "
        with STDOUT:
            print head + msg
