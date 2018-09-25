#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import ConfigParser


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
TUNNEL_CORE = """sshuttle -r [USER]@[IP] [NET] -e 'sshpass -p[PASS] ssh -p [PORT] -o StrictHostKeyChecking=no -o ExitOnForwardFailure=yes -o ServerAliveInterval=0 -o TCPKeepAlive=yes'  > /dev/null 2>&1"""

EXIT_ERROR_LOCK = 1
EXIT_ERROR_CORRUPT_DB = 2
EXIT_SUCCESS = 0


DEBUG = False
