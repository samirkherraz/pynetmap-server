#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'
import os
import time
from threading import Thread, Event
import pkgutil
from const import UPDATE_INTERVAL, DEBUG


class Core:
    MONITOR = dict()
    DISCOVER = dict()

    def set_status(self, id, status=None):
        el = self.store.get("base", id)
        if status == self.utils.RUNNING_STATUS:
            self.utils.debug("System::Status",
                             el["base.name"]+"::UP")
            self.store.set_attr("module", id, "module.state.history.status",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.status"), 100))
            self.store.set_attr(
                "module", id, "module.state.status", 'running')
        else:
            self.utils.debug("System::Status",
                             el["base.name"]+"::DOWN", 1)
            self.store.set_attr("module", id, "module.state.history.status",
                                self.utils.history_append(self.store.get_attr(
                                    "module", id, "module.state.history.status"), 0))
            self.store.set_attr("module", id, "module.state.status",
                                ('stopped' if status == None else status))
        self.store.set_attr(
            "module", id, "module.state.lastupdate", time.time())

    def scan(self):
        for loader, name, is_pkg in pkgutil.walk_packages([os.path.dirname(os.path.abspath(__file__))+"/Modules"]):
            if is_pkg and "." not in name:
                M = loader.find_module(
                    name).load_module(name)
                try:
                    Monitor = M.Monitor
                    self.register_monitor(
                        name, Monitor(self.store, self.utils))
                    self.utils.debug("System::Modules",
                                     name+"::MONITOR")
                except:
                    pass
                try:
                    Discover = M.Discover
                    self.register_discover(
                        name, Discover(self.store, self.utils))
                    self.utils.debug("System::Modules",
                                     name+"::DISCOVER")
                except:
                    pass

    def register_monitor(self, name, handler):
        Core.MONITOR[name] = handler

    def register_discover(self, name, handler):
        Core.DISCOVER[name] = handler

    def discover(self, id):
        hypervisor = self.store.get_attr("base", id, "base.type")
        if hypervisor != None and hypervisor in Core.DISCOVER:
            self.utils.debug(
                "System::Discovery", hypervisor + "::"+self.store.get_attr("base", id, "base.name"))
            Core.DISCOVER[hypervisor].process(id)

    def monitor(self, id, parent=None):
        hypervisor = self.store.get_attr(
            "base", parent, "base.type")
        os = self.store.get_attr("base", id, "base.os")
        status = self.utils.UNKNOWN_STATUS
        if os in Core.MONITOR:
            self.utils.debug(
                "System::Monitor", os + "::"+self.store.get_attr("base", id, "base.name"))
            status = Core.MONITOR[os].process(id)
            self.store.set_attr("module", id, "module.state.discoverer", os)
        if status != self.utils.RUNNING_STATUS and hypervisor in Core.MONITOR:
            self.utils.debug("System::Monitor", hypervisor +
                             "::"+str(self.store.get_attr("base", id, "base.name")))
            status = Core.MONITOR[hypervisor].process(id)
            self.store.set_attr(
                "module", id, "module.state.discoverer", hypervisor)

        self.set_status(id,  status)

    def process(self, id, parent=None):
        self.discover(id)
        if self.store.get_attr("base", id, "base.monitor") == None:
            self.store.set_attr("base", id, "base.monitor", "Yes")

        if self.store.get_attr("base", id, "base.monitor") == "Yes":
            self.monitor(id, parent)
            self.alerts.check(id)
        else:
            self.alerts.clear(id)

        for key in self.store.get_children(id):
            self.process(key, id)

    def __init__(self, store, utils, alerts):
        self.store = store
        self.utils = utils
        self.alerts = alerts
        self.threads = []

        self._stop = Event()
        self.scan()

    def clear(self):
        for t in self.threads:
            print t.is_alive
        self.threads = []

    def run(self):
        while True:
            self.clear()
            self.store.write()
            all = self.store.find_by_schema("Noeud")
            for id in all:
                try:
                    if DEBUG:
                        self.process(id)
                    else:
                        thread = None
                        thread = Thread(target=self.process, args=(id,))
                        self.threads.append(thread)
                        thread.daemon = True
                        thread.start()
                except:
                    pass
            try:
                self._stop.wait(UPDATE_INTERVAL)
            except:
                pass
