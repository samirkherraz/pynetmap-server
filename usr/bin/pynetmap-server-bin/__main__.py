#!/usr/bin/env python
# import server
import sys
import os
import pkgutil
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'
import logging
logging.basicConfig(filename="test.log", level=logging.DEBUG)
from threading import Thread
from Core.RestServer.HttpServer import HttpServer
from Core.Collector.Collector import Collector
if __name__ == "__main__":
    if(len(sys.argv) > 2):
        test_module = sys.argv[1]
        test_class = sys.argv[2]
        path = os.path.dirname(os.path.abspath(__file__))+"/"+test_module
        packages = pkgutil.walk_packages([path])
        for (loader, name, is_pkg) in packages:
            if test_class in name:
                M = loader.find_module(name).load_module(name)
                try:
                    M.Test()
                    logging.info("[Success]")
                except ValueError as e:
                    logging.info(e)
                    logging.info("[Fail]")
    else:
        collector = Collector()
        CollectorDaemon = Thread(target=collector.run)
        CollectorDaemon.daemon = True
        CollectorDaemon.start()
        HttpServer.run()
