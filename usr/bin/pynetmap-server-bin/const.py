import os
import ConfigParser

CONFIG_FILE = "/etc/pynetmap-server/global.conf"
configuration = ConfigParser.ConfigParser()
with open(CONFIG_FILE) as fp:
    configuration.readfp(fp)

LISTENING_PORT = configuration.getint("Server", "Port")

BACKUP_DIR = configuration.get("Storage", "Backup")
WORKING_DIR = configuration.get("Storage", "Base")
GPG_DIR = configuration.get("Storage", "GPG")

ADMIN_USERNAME = configuration.get("Authentification", "Login")
ADMIN_PASSWORD = configuration.get("Authentification", "Password")

UPDATE_INTERVAL = configuration.getint("Statistics", "Refresh")

TUNNEL_HEADER = """killall sshuttle"""
TUNNEL_CORE = """sshuttle -D --pidfile /var/run/sshuttle-pid-[ID] -r [USER]@[IP] [NET] -e 'sshpass -p[PASS] ssh -p [PORT] -o StrictHostKeyChecking=no' > /dev/null 2>&1"""
NMAP_CORE = """sshpass -p[PASS] ssh -p [PORT] -o StrictHostKeyChecking=no [USER]@[IP] "apt-get install arp-scan -y 2> /dev/null ; arp-scan --quiet [NET]; ifconfig | grep -E '(inet |HWaddr|ether)' | grep -v '127.0.0.1' | awk '{ printf \$2; getline; print \\"\\t\\" \$2 }' " """

EXIT_ERROR_LOCK = 1
EXIT_ERROR_CORRUPT_DB = 2
EXIT_SUCCESS = 0
