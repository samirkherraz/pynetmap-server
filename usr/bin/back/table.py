#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

from shutil import copyfile
import json
import codecs
import time
from const import WORKING_DIR, BACKUP_DIR
from threading import Lock


class Table:
    def __init__(self, name, persist=True):
        self._head = None
        self._name = name
        self._lock = Lock()
        self._persist = persist
        self._changed = False
        self.read()

    def read(self):
        self._changed = True
        try:
            jsonFile = codecs.open(
                WORKING_DIR+self._name+".json", "r", "utf-8")
            jsonStr = jsonFile.read()
            jsonFile.close()
            self._head = json.loads(jsonStr)
        except:
            self._head = dict()
            self.write()

    def write(self):
        if self._changed:
            if self._persist:
                try:
                    copyfile(WORKING_DIR+self._name+".json", BACKUP_DIR +
                             self._name+"_"+str(time.time())+".json")
                except:
                    pass
            jsonStr = json.dumps(self.get_data())
            jsonFile = codecs.open(
                WORKING_DIR+self._name+".json", "w", "utf-8")
            jsonFile.write(jsonStr)
            jsonFile.close()
            self._changed = False

    def get_data(self):
        return self._head

    def set_data(self, data):
        with self._lock:
            self._head = data
            self._changed = True

    def set(self, key, value):
        with self._lock:
            self._head[key] = value
            self._changed = True

    def get(self, key):
        try:
            return self._head[key]
        except:
            return None

    def set_attr(self, id, key, value):
        with self._lock:
            if value != None:
                self._head[id][key] = value
            else:
                del self._head[id][key]
            self._changed = True

    def get_attr(self, id, key):
        try:
            return self._head[id][key]
        except:
            return None

    def cleanup(self, lst=None):
        with self._lock:
            for k in list(self._head.keys()):
                if lst != None and k not in lst:
                    del self._head[k]
                    self._changed = True
                else:
                    for e in list(self._head[k].keys()):
                        if not e.startswith(self._name):
                            del self._head[k][e]
                            self._changed = True
                        elif self._head[k][e] == "":
                            del self._head[k][e]
                            self._changed = True

            if lst != None:
                for k in lst:
                    if k not in self._head:
                        self._head[k] = {}
                        self._changed = True

    def delete(self, key):
        with self._lock:
            try:
                del self._head[key]
                self._changed = True
            except:
                pass
