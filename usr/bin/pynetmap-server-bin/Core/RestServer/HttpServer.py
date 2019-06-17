#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import os
import signal
import logging
from http.server import HTTPServer
from Constants import EXIT_SUCCESS
from Settings import LISTENING_PORT
from Core.RestServer.HttpHandler import HttpHandler


class HttpServer:
    @staticmethod
    def signal_handler(signal, frame):
        exit(EXIT_SUCCESS)

    @staticmethod
    def run():
        logging.info("System::API", "HTTP Server Starting")
        server_address = ('0.0.0.0', LISTENING_PORT)
        httpd = HTTPServer(server_address, HttpHandler)
        logging.info("System::API", "HTTP Server Running")
        signal.signal(signal.SIGINT, HttpServer.signal_handler)
        httpd.serve_forever()


def Test():
    HttpServer.run()
