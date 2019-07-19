#!/usr/bin/env python

__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import os
import pkgutil
import sys
from threading import Thread

from Constants import *
from Core.Collector.Collector import Collector
from Core.Database.DbUtils import DbUtils
from Core.RestServer.HttpServer import HttpServer
from Core.Utils.Fn import renew_ssh_pwd

if __name__ == "__main__":
    if(len(sys.argv) > 1):
        sys.argv.pop(0)
        cmd = sys.argv.pop(0)
        if cmd == "get":
            print(DbUtils.getInstance()[sys.argv])
        elif cmd == "set":
            print(DbUtils.getInstance()[sys.argv])
            value = input("> ")
            print(f'{sys.argv} = {value} ?')
            if input("Replace ? (y/n) [n]").upper() == "Y":
                DbUtils.getInstance()[sys.argv] = value
                DbUtils.getInstance().persist()

    else:
        renew_ssh_pwd()
        collector = Collector()
        CollectorDaemon = Thread(target=collector.run)
        CollectorDaemon.daemon = True
        CollectorDaemon.start()
        HttpServer.run()
