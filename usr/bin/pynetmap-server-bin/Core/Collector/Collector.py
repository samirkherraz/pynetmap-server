#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'
import os
import pkgutil
import time
from threading import Event, Semaphore, Thread

from Constants import *
from Core.Database.DbUtils import DbUtils
from Core.Utils import Fn
from Core.Utils.Logging import getLogger


class Collector:

    MONITOR = dict()
    DISCOVER = dict()

    def stop(self):
        self._stop.set()

    def set_status(self, id, status=None):
        logging = getLogger(__package__, DbUtils.getInstance()[
                            DB_BASE, id, KEY_NAME])

        if DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR_HISTORY, KEY_STATUS] is None:
            DbUtils.getInstance()[DB_MODULE, id,
                                  KEY_MONITOR_HISTORY, KEY_STATUS] = list()

        if status == RUNNING_STATUS:
            Fn.history(
                DbUtils.getInstance()[DB_MODULE, id,
                                      KEY_MONITOR_HISTORY, KEY_STATUS],
                100
            )
            DbUtils.getInstance()[DB_MODULE, id, KEY_STATUS] = RUNNING_STATUS
        else:
            Fn.history(
                DbUtils.getInstance()[DB_MODULE, id,
                                      KEY_MONITOR_HISTORY, KEY_STATUS],
                0
            )
            DbUtils.getInstance()[DB_MODULE, id, KEY_STATUS] = (
                'stopped' if status == None else status)
        DbUtils.getInstance()[DB_MODULE, id, KEY_LAST_UPDATE] = time.time()

        logging.info(f'STATUS SET TO {status}')

    def scan(self):
        logging = getLogger(__package__)
        DbUtils.getInstance()[DB_CONFIG, KEY_MONITOR, "None"] = 1
        DbUtils.getInstance()[DB_CONFIG, KEY_HYPERVISOR, "None"] = 1
        path = BASE_DIR+"/Modules"
        packages = pkgutil.walk_packages([path])
        for (loader, name, is_pkg) in packages:
            if is_pkg and "." not in name:
                M = loader.find_module(
                    name).load_module(name)
                try:
                    Monitor = M.Monitor
                    Collector.MONITOR[name] = Monitor()
                    DbUtils.getInstance()[DB_CONFIG, KEY_MONITOR, name] = 1
                    logging.info(f'MODULE MONITOR {name} WAS FOUND')
                except Exception as e:
                    logging.debug(e)
                    logging.warning(f'MODULE MONITOR {name} WAS NOT FOUND')
                try:
                    Discover = M.Discover
                    Collector.DISCOVER[name] = Discover()
                    DbUtils.getInstance()[DB_CONFIG, KEY_HYPERVISOR, name] = 1
                    logging.info(f'MODULE DISCOVER {name} WAS FOUND')
                except Exception as e:
                    logging.debug(e)
                    logging.warning(f'MODULE DISCOVER {name} WAS NOT FOUND')

    def discover(self, id):
        hypervisor = DbUtils.getInstance()[DB_BASE, id, KEY_HYPERVISOR]
        if hypervisor != None and hypervisor in Collector.DISCOVER.keys():
            logging = getLogger(__package__, DbUtils.getInstance()[
                                DB_BASE, id, KEY_NAME])
            logging.info(f'DISCOVER BY {hypervisor}')
            Collector.DISCOVER[hypervisor].process(id)

    def monitor(self, id, parent=None):
        method = DbUtils.getInstance()[DB_BASE, id, KEY_MONITOR]
        if method == None:
            method = "None"
            DbUtils.getInstance()[DB_BASE, id, KEY_MONITOR] = method
            DbUtils.getInstance().persist()

        status = UNKNOWN_STATUS
        if method in Collector.MONITOR.keys():
            logging = getLogger(__package__, DbUtils.getInstance()[
                                DB_BASE, id, KEY_NAME])
            logging.info(f'MONITOR BY {method}')
            DbUtils.getInstance()[DB_MODULE, id, KEY_MONITOR] = method
            status = Collector.MONITOR[method].process(id)

        self.set_status(id, status)

    def process(self, id, parent=None):
        self.discover(id)
        self.monitor(id, parent)
        for key in DbUtils.getInstance().find_children(id):
            self.process(key, id)
        if parent == None:
            self._semaphore.release()
            logging = getLogger(__package__)
            logging.info(f'LOCK RELEASE , REMAINING {self._semaphore._value }')

    def __init__(self):
        self._semaphore = Semaphore(8)
        self._threads = dict()
        self._stop = Event()
        self.scan()

    def run(self):
        while True:
            all = DbUtils.getInstance().find(DB_BASE, KEY_TYPE, "Noeud")
            for id in all:
                self._semaphore.acquire()
                logging = getLogger(__package__)
                logging.info(
                    f'LOCK ACQUIRED , REMAINING {self._semaphore._value }')
                thread = Thread(target=self.process, args=(id,))
                thread.daemon = True
                thread.start()

            self._stop.wait(
                int(DbUtils.getInstance()[DB_SERVER, "trigger", "update_interval"]))
            if self._stop.isSet():
                break
