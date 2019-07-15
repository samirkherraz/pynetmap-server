#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

from threading import Lock
from shutil import copyfile
import json
import codecs
import time


class Table:

    def __init__(self, name, persist=True):
        self._head = None
        self._name = name
        self._lock = Lock()
        self._persist = persist
        self.read()

    def keys(self):
        return self._head.keys()

    def __setitem__(self, name, value):
        with self._lock:
            if type(name) is not list:
                name = [name, ]
            if len(name) > 0:
                cont = None
                key = None
                d = self._head
                while len(name) > 0:
                    e = name.pop(0)
                    cont = d
                    key = e
                    if e in d.keys():
                        d = d[e]
                    else:
                        d[e] = dict() if len(name) > 0 else None
                cont[key] = value
            else:
                self._head = value
            self.write()

    def __getitem__(self, name):
        if type(name) is not list:
            name = [name, ]
        d = self._head
        while len(name) > 0:
            e = name.pop(0)
            if type(d) is dict:
                if e in d.keys():
                    d = d[e]
                else:
                    d[e] = dict() if len(name) > 0 else None
                    d = d[e]
            else:
                return None
        return d

    def delete(self, key):
        with self._lock:
            try:
                del self._head[key]
                self.write()
                return True
            except Exception as e:
                return False

    def cleanup(self, lst=None):
        with self._lock:
            _changed = False
            if lst != None:
                for k in list(self._head.keys()):
                    if k not in lst:
                        del self._head[k]
                        _changed = True
                for k in lst:
                    if k not in list(self._head.keys()):
                        self._head[k] = {}
                        _changed = True
            if _changed:
                self.write()

    def read(self):
        if self._persist:
            try:
                jsonFile = codecs.open(
                    "/var/lib/pynetmap/"+self._name+".json", "r", "utf-8")
                jsonStr = jsonFile.read()
                jsonFile.close()
                self._head = json.loads(jsonStr)
            except :
                self._head = dict()
                self.write()
        else:
            self._head = dict()

    def write(self):

        if self._persist:
            # try:
            #     copyfile("/var/lib/pynetmap/"+self._name+".json", BACKUP_DIR +
            #              self._name+"_"+str(time.time())+".json")
            # except Exception as e:
            #     pass
            jsonStr = json.dumps(self._head)
            jsonFile = codecs.open(
                "/var/lib/pynetmap/"+self._name+".json", "w", "utf-8")
            jsonFile.write(jsonStr)
            jsonFile.close()
