#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'


class Alerts:

    ALERT_ERROR = 1
    ALERT_INFO = 0

    def __init__(self, store, utils):
        self.store = store
        self.utils = utils

    def disk(self, el):
        try:
            value = int(self.store.get_attr(
                "module", el, "module.state.history.disk")[::-1][0])
            msg = "Disk is " + \
                str(value) + \
                "%"

            if value > 90:
                self.store.set_attr("alert", el, "alert.disk", self.alert(
                    Alerts.ALERT_ERROR, msg))
            elif value > 80:
                self.store.set_attr("alert", el, "alert.disk", self.alert(
                    Alerts.ALERT_INFO,  msg))

        except:
            pass

    def required_fields(self, el):
        base = self.store.get(
            "base", el)
        impo = []
        if base["base.core.schema"] == "Noeud":
            impo.append("base.net.ip")
            impo.append("base.ssh.user")
            impo.append("base.ssh.password")
        elif base["base.core.schema"] == "VM":
            impo.append("base.net.ip")
            impo.append("base.ssh.user")
            impo.append("base.ssh.password")
        elif base["base.core.schema"] == "Container":
            impo.append("base.net.ip")
            impo.append("base.ssh.user")
            impo.append("base.ssh.password")
        elif base["base.core.schema"] == "Server":
            impo.append("base.tunnel.ip")
            impo.append("base.tunnel.user")
            impo.append("base.tunnel.password")
            impo.append("base.tunnel.network")
        required = []
        for e in impo:
            if e not in base or base[e] == "":
                required.append(e)

        if len(required) > 0:
            self.store.set_attr("alert", el, "alert.required_fields", self.alert(
                Alerts.ALERT_INFO,  required))

    def tunnel(self, el):
        try:
            value = self.store.get_attr("module", el, "module.tunnel.status")
            msg = "Tunnel is down"

            if value == "Lost":
                self.store.set_attr("alert", el, "alert.tunnel", self.alert(
                    Alerts.ALERT_ERROR,  msg))
        except:
            pass

    def cpu(self, el):
        try:
            i = 0
            fatal = True
            info = True
            while i < 10:
                fatal &= int(self.store.get_attr(
                    "module", el, "module.state.history.cpuusage")[::-1][i]) > 90
                info &= int(self.store.get_attr(
                    "module", el, "module.state.history.cpuusage")[::-1][i]) > 80
                i += 1
            msg = "CPU Usage usage is " + str(int(self.store.get_attr(
                "module", el, "module.state.history.cpuusage")[::-1][0])) + "% for 5 minutes"

            if fatal:
                self.store.set_attr("alert", el, "alert.cpu", self.alert(
                    Alerts.ALERT_ERROR,  msg))
            elif info:
                self.store.set_attr("alert", el, "alert.cpu", self.alert(
                    Alerts.ALERT_INFO, msg))

        except:
            pass

    def memory(self, el):
        try:
            i = 0
            fatal = True
            info = True
            while i < 10:
                fatal &= int(self.store.get_attr(
                    "module", el, "module.state.history.memory")[::-1][i]) > 90
                info &= int(self.store.get_attr(
                    "module", el, "module.state.history.memory")[::-1][i]) > 80
                i += 1
            msg = "Memory usage is " + str(int(self.store.get_attr(
                "module", el, "module.state.history.memory")[::-1][0])) + "% for 5 minutes"

            if fatal:
                self.store.set_attr("alert", el, "alert.memory", self.alert(
                    Alerts.ALERT_ERROR,  msg))
            elif info:
                self.store.set_attr("alert", el, "alert.memory", self.alert(
                    Alerts.ALERT_INFO, msg))

        except:
            pass

    def status(self, el):
        try:
            value1 = int(self.store.get_attr(
                "module", el, "module.state.history.status")[::-1][0])
            value0 = int(self.store.get_attr(
                "module", el, "module.state.history.status")[::-1][1])
            if value1 > value0:
                self.store.set_attr("alert", el, "alert.status", self.alert(
                    Alerts.ALERT_INFO,  "Status is UP"))
            elif value1 < value0:
                self.store.set_attr("alert", el, "alert.status", self.alert(
                    Alerts.ALERT_ERROR, "Status is Down"))
        except:
            pass

    def mounts(self, el):
        try:
            for mount in self.store.get_attr("module", el, "module.state.mounts"):
                value = int(mount["usage"])
                msg = "Mount point " + \
                    mount["point"] + " is "+str(value) + "% "
                if value > 90:
                    self.store.set_attr("alert", el, "alert.mounts", self.alert(
                        Alerts.ALERT_ERROR,  msg))
                elif value > 80:
                    self.store.set_attr("alert", el, "alert.mounts", self.alert(
                        Alerts.ALERT_INFO,  msg))
        except:
            pass

    def check(self, key):
        self.utils.debug("System::Alerts", self.store.get_attr(
            "base", key, "base.name"))
        self.clear(key)
        self.disk(key)
        self.mounts(key)
        self.cpu(key)
        self.memory(key)
        self.tunnel(key)
        self.status(key)
        self.required_fields(key)

    def clear(self, key):
        self.store.set("alert", key, dict())

    def alert(self, severity, msg):
        k = dict()
        k["severity"] = severity
        k["content"] = msg
        return k
