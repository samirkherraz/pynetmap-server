#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import os
import signal
import logging
from http.server import HTTPServer
from Constants import *
from Core.RestServer.HttpHandler import HttpHandler
from Core.Database.DbUtils import DbUtils

class HttpServer:
    @staticmethod
    def signal_handler(signal, frame):
        exit(EXIT_SUCCESS)

    @staticmethod
    def run():
        port =  int(float(DbUtils.getInstance()[DB_SERVER,"server", "port" ]))
        print(port)
        server_address = ('0.0.0.0',port)
        httpd = HTTPServer(server_address, HttpHandler)
        signal.signal(signal.SIGINT, HttpServer.signal_handler)
        httpd.serve_forever()

