#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'
import os
import pkgutil
import time
from threading import Event, Semaphore, Thread

from const import DEBUG, LISTENING_PORT, UPDATE_INTERVAL
from error import EXIT_ERROR_CORRUPT_DB
from model import Model


class Core:

    MONITOR = dict()
    DISCOVER = dict()

    def set_status(self, id, status=None):
        print("TATUS !!!!" + status)
        if status == self.model.utils.RUNNING_STATUS:
            self.model.utils.debug("System::Status",
                                   str(self.model.store.get_attr("base", id, "base.name"))+"::UP")
            self.model.store.set_attr("module", id, "module.state.history.status",
                                      self.model.utils.history_append(self.model.store.get_attr(
                                          "module", id, "module.state.history.status"), 100))
            self.model.store.set_attr(
                "module", id, "module.state.status", 'running')
        else:
            self.model.utils.debug("System::Status",
                                   str(self.model.store.get_attr("base", id, "base.name"))+"::DOWN", 1)
            self.model.store.set_attr("module", id, "module.state.history.status",
                                      self.model.utils.history_append(self.model.store.get_attr(
                                          "module", id, "module.state.history.status"), 0))
            self.model.store.set_attr("module", id, "module.state.status",
                                      ('stopped' if status == None else status))
        self.model.store.set_attr(
            "module", id, "module.state.lastupdate", time.time())

    def scan(self):
        path = os.path.dirname(os.path.abspath(__file__))+"/Modules"
        packages = pkgutil.walk_packages([path])
        for (loader, name, is_pkg) in packages:
            if is_pkg and "." not in name:
                M = loader.find_module(
                    name).load_module(name)
                try:
                    Monitor = M.Monitor
                    self.register_monitor(
                        name, Monitor(self.model))
                    self.model.utils.debug("System::Modules",
                                           name+"::MONITOR")
                except:
                    pass
                try:
                    Discover = M.Discover
                    self.register_discover(
                        name, Discover(self.model))
                    self.model.utils.debug("System::Modules",
                                           name+"::DISCOVER")
                except:
                    pass

        for e in ["Noeud", "VM", "Container"]:
            data = self.model.store.get("schema", e)
            data["Fields"]["base.monitor.method"] = list(Core.MONITOR.keys()) + \
                ["None"]
            self.model.store.set("schema", e, data)
        for e in ["Noeud"]:
            data = self.model.store.get("schema", e)
            data["Fields"]["base.hypervisor"] = list(Core.DISCOVER.keys()) + \
                ["None"]
            self.model.store.set("schema", e, data)

    def register_monitor(self, name, handler):
        Core.MONITOR[name] = handler

    def register_discover(self, name, handler):
        Core.DISCOVER[name] = handler

    def discover(self, id):
        hypervisor = self.model.store.get_attr("base", id, "base.hypervisor")
        if hypervisor != None and hypervisor in Core.DISCOVER:
            self.model.utils.debug(
                "System::Discovery", hypervisor + "::"+self.model.store.get_attr("base", id, "base.name"))
            Core.DISCOVER[hypervisor].process(id)

    def monitor(self, id, parent=None):

        method = self.model.store.get_attr("base", id, "base.monitor.method")
        if method == None:
            method = list(Core.MONITOR.keys())[0]
            self.model.store.set_attr(
                "base", id, "base.monitor.method", method)

        status = self.model.utils.UNKNOWN_STATUS
        if method in Core.MONITOR:
            self.model.utils.debug(
                "System::Monitor", method + "::"+str(self.model.store.get_attr("base", id, "base.name")))
            status = Core.MONITOR[method].process(id)
            self.model.store.set_attr(
                "module", id, "module.monitor.agent", method)

        self.set_status(id, status)

    def process(self, id, parent=None):
        if parent == None:
            self.semaphore.acquire()
        self.discover(id)
        self.monitor(id, parent)
        # self.alerts.check(id)

        for key in self.model.store.get_children(id):
            self.process(key, id)
        if parent == None:
            self.semaphore.release()

    def __init__(self):
        self.model = Model()
        if not self.model.load():
            exit(EXIT_ERROR_CORRUPT_DB)
        self.semaphore = Semaphore(4)
        self.threads = dict()
        self._stop = Event()
        self.scan()

    def clear(self):
        self.semaphore.acquire()
        for t in list(self.threads.keys()):
            if not self.threads[t].isAlive():
                del self.threads[t]
            else:
                self.semaphore.release()

    def run(self):
        while True:
            self.model.persist()
            all = self.model.store.find_by_schema("Noeud")
            for id in all:
                if DEBUG:
                    self.process(id)
                else:
                    try:
                        self.clear()
                        thread = None
                        thread = Thread(name=self.model.store.get_attr(
                            "base", id, "base.name"), target=self.process, args=(id,))
                        self.threads[id] = thread
                        thread.daemon = True
                        thread.start()
                    except ValueError as e:
                        pass
            try:
                self._stop.wait(UPDATE_INTERVAL)
            except:
                pass
