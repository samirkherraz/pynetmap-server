#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import configparser
import os
import sys

import logging
LOGFORMAT = "%(asctime)s [%(levelname)s] %(threadName)s::%(module)s \n %(message)s"
logging.basicConfig(
    stream=sys.stdout, level=logging.DEBUG, format=LOGFORMAT)

CONFIG_FILE = "/etc/pynetmap-server/global.conf"
configuration = configparser.ConfigParser()
with open(CONFIG_FILE) as fp:
    configuration.readfp(fp)

LISTENING_PORT = configuration.getint("Server", "Port")

BACKUP_DIR = configuration.get("Storage", "Backup")
WORKING_DIR = configuration.get("Storage", "Base")

ADMIN_USERNAME = configuration.get("Authentification", "Login")
ADMIN_PASSWORD = configuration.get("Authentification", "Password")
HISTORY = configuration.getint("Statistics", "History")
UPDATE_INTERVAL = configuration.getint("Statistics", "Refresh")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True
