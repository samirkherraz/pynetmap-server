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
from threading import Thread
from Core.RestServer.HttpServer import HttpServer
from Core.Collector.Collector import Collector
from Core.Database.DbUtils import DbUtils
from Core.Utils.Fn import renew
from Constants import *
if __name__ == "__main__":
    if(len(sys.argv) > 1):
        db = DbUtils.getInstance()
        sys.argv.pop(0)
        cmd = sys.argv.pop(0)
        if cmd == "get":
            print(db[sys.argv])
        elif cmd == "set":
            print(db[sys.argv])
            value = input("> ")
            print(f'{sys.argv} = {value} ?' )
            if input("Replace ? (y/n) [n]").upper() == "Y":
                db[sys.argv] = value
        # cmd = sys.argv[1]
        # if cmd == "config":
        #     
        #     if(len(sys.argv) > 2):
        #         action = sys.argv[2]
        #         if action == "list":
        #             for e in db[DB_SERVER].keys():
        #                 print(e)
        #         elif action == "set":
        #             if(len(sys.argv) == 6):
        #                 section = sys.argv[3]
        #                 key = sys.argv[4]
        #                 value = sys.argv[5]
        #                 db[DB_SERVER, section, key] = value
        #             else:
        #                 print("not enough args")
        #         elif action == "get":
        #             if(len(sys.argv) == 5):
        #                 section = sys.argv[3]
        #                 key = sys.argv[4]
        #                 print( db[DB_SERVER, section, key] )
        #             elif(len(sys.argv) == 4):
        #                 section = sys.argv[3]
        #                 for e in db[DB_SERVER, section].keys():
        #                     print(e)
    else:
        renew()
        collector = Collector()
        CollectorDaemon = Thread(target=collector.run)
        CollectorDaemon.daemon = True
        CollectorDaemon.start()
        HttpServer.run()
