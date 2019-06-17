#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'
import os
import pkgutil
import time
import logging
from threading import Event, Semaphore, Thread
from Constants import *
from Settings import UPDATE_INTERVAL, BASE_DIR
from Core.Database.DbUtils import DbUtils
from Core.Utils import Fn


"""
Module -> ELM{
    history{
        status: [....]
    },
    status: running,
    lastUpdate: 123854798412
}
Config -> hypervisor [ ........... ]
Config -> monitor [ ........... ]

"""


class Collector:

    MONITOR = dict()
    DISCOVER = dict()

    def stop(self):
        self._stop.set()

    def set_status(self, id, status=None):
        if self.db[[DbUtils.MODULE, id, KEY_MONITOR_HISTORY, "status"]] is None:
                self.db[[DbUtils.MODULE, id, KEY_MONITOR_HISTORY, "status"]] = list()
        
        
        if status == RUNNING_STATUS:
            Fn.history(self.db[[DbUtils.MODULE, id, KEY_MONITOR_HISTORY, "status"]], 100)
            self.db[[DbUtils.MODULE, id, "status"]] = RUNNING_STATUS
        else:
            Fn.history(self.db[[DbUtils.MODULE, id, KEY_MONITOR_HISTORY, "status"]], 0)
            self.db[[DbUtils.MODULE, id, "status"]] = (
                'stopped' if status == None else status)

        self.db[[DbUtils.MODULE, id, "lastUpdate"]] = time.time()
        self.db.persist()

    def scan(self):
        self.db[[DbUtils.CONFIG, "monitor", "None"]] = 1
        self.db[[DbUtils.CONFIG, "hypervisor", "None"]] = 1
        path = BASE_DIR+"/Modules"
        packages = pkgutil.walk_packages([path])
        for (loader, name, is_pkg) in packages:
            if is_pkg and "." not in name:
                M = loader.find_module(
                    name).load_module(name)
                try:
                    Monitor = M.Monitor
                    Collector.MONITOR[name] = Monitor()
                    self.db[[DbUtils.CONFIG, "monitor", name]] = 1
                except Exception as e:
                    logging.error(e)
                try:
                    Discover = M.Discover
                    Collector.DISCOVER[name] = Discover()
                    self.db[[DbUtils.CONFIG, "hypervisor", name]] = 1

                except Exception as e:
                    logging.error(e)

    def discover(self, id):
        hypervisor = self.db[[DbUtils.BASE, id, "hypervisor"]]
        if hypervisor != None and hypervisor in Collector.DISCOVER.keys():
            Collector.DISCOVER[hypervisor].process(id)

    def monitor(self, id, parent=None):
        method = self.db[[DbUtils.BASE, id, "monitor"]]
        if method == None:
            method = "None"
            self.db[[DbUtils.BASE, id, "monitor"]] = method

        status = UNKNOWN_STATUS
        if method in Collector.MONITOR.keys():
            status = Collector.MONITOR[method].process(id)
            self.db[[DbUtils.MODULE, id, "monitor"]] = method

        self.set_status(id, status)

    def process(self, id, parent=None):
        if parent == None:
            self._semaphore.acquire()
        self.discover(id)
        self.monitor(id, parent)

        for key in self.db.find_children(id):
            self.process(key, id)
        if parent == None:
            self._semaphore.release()

    def __init__(self):
        self.db = DbUtils.getInstance()
        self._semaphore = Semaphore(4)
        self._threads = dict()
        self._stop = Event()
        self.scan()

    def clear(self):
        for t in list(self._threads.keys()):
            if not self._threads[t].isAlive():
                del self._threads[t]
                self._semaphore.release()

    def run(self):
        while True:
            self.db.persist()
            all = self.db.find(DbUtils.BASE, KEY_TYPE, "Noeud")
            for id in all:
                self.clear()
                thread = None
                thread = Thread(target=self.process, args=(id,))
                self._threads[id] = thread
                thread.daemon = True
                self._semaphore.acquire()
                thread.start()

            self._stop.wait(UPDATE_INTERVAL)
            if self._stop.isSet():
                break


def Test():
    c = Collector()
    c.run()
    c.stop()
