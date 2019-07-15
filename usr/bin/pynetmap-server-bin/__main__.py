#!/usr/bin/env python
# import server
import sys
import os
import pkgutil
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'
import logging
logging.basicConfig(filename="test.log", level=logging.DEBUG)
from threading import Thread
from Core.RestServer.HttpServer import HttpServer
from Core.Collector.Collector import Collector
from Core.Database.DbUtils import DbUtils
from Core.Utils.Fn import renew
from Constants import *
if __name__ == "__main__":
    if(len(sys.argv) > 1):
        cmd = sys.argv[1]
        if cmd == "config":
            db = DbUtils.getInstance()
            if(len(sys.argv) > 2):
                action = sys.argv[2]
                if action == "list":
                    for e in db[DB_SERVER].keys():
                        print(e)
                elif action == "set":
                    if(len(sys.argv) == 6):
                        section = sys.argv[3]
                        key = sys.argv[4]
                        value = sys.argv[5]
                        db[DB_SERVER, section, key] = value
                    else:
                        print("not enough args")
                elif action == "get":
                    if(len(sys.argv) == 5):
                        section = sys.argv[3]
                        key = sys.argv[4]
                        print( db[DB_SERVER, section, key] )
                    elif(len(sys.argv) == 4):
                        section = sys.argv[3]
                        for e in db[DB_SERVER, section].keys():
                            print(e)
    else:
        renew()
        collector = Collector()
        CollectorDaemon = Thread(target=collector.run)
        CollectorDaemon.daemon = True
        CollectorDaemon.start()
        HttpServer.run()
