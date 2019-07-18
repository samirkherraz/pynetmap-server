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
from Constants import *
from Core.Database.Secret import Secret


class Table:

    def __init__(self, name, persist=True, secret=True):
        self._head = dict()
        self._secret = secret
        self.ext = ".bin" if secret else ".json"
        self._name = name
        self._lock = Lock()
        self._persist = persist
        self._changed = False
        self.read()

    def keys(self):
        return self._head.keys()

    def __setitem__(self, name, value):
        if type(name) is not list:
            name = [name, ]
        if len(name) > 0:
            cont = None
            key = None
            d = self._head
            while len(name) > 0:
                e = name.pop(0)
                cont = d if type(d) is dict else dict()
                key = e
                if e in d.keys():
                    d = d[e]
                else:
                    d[e] = dict() if len(name) > 0 else None
            with self._lock:
                cont[key] = value
                self._changed = True
        else:
            with self._lock:
                self._head = value
                self._changed = True

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

    def __delitem__(self, name):
        if type(name) is not list:
            name = [name, ]
        if len(name) > 0:
            cont = None
            key = None
            d = self._head
            while len(name) > 0:
                e = name.pop(0)
                cont = d if type(d) is dict else dict()
                key = e
                if e in d.keys():
                    d = d[e]
                else:
                    d[e] = dict() if len(name) > 0 else None
            with self._lock:
                del cont[key]
                self._changed = True
        else:
            del self._head

    def delete(self, key):
        with self._lock:
            try:
                del self._head[key]
                self._changed = True
                return True
            except:
                return False

    def cleanup(self, lst=None):
        if lst != None:
            for k in list(self._head.keys()):
                if k not in lst:
                    with self._lock:
                        del self._head[k]
                        self._changed = True
            for k in lst:
                if k not in list(self._head.keys()):
                    with self._lock:
                        self._head[k] = {}
                        self._changed = True

    def read(self):
        if self._persist:
            try:
                jsonFile = codecs.open(
                    "/var/lib/pynetmap/"+self._name+self.ext, "rb")
                jsonStr = jsonFile.read()
                jsonFile.close()
                if self._secret:
                    jsonStr = Secret(CRYPTO_KEY_ENCRYPTION).decrypt(jsonStr)
                with self._lock:
                    self._head = json.loads(jsonStr)
            except:
                with self._lock:
                    self._head = dict()
        else:
            self._head = dict()

    def write(self):
        with self._lock:
            if self._persist and self._changed:
                self._changed = False
                jsonStr = json.dumps(self._head)
                jsonFile = codecs.open(
                    "/var/lib/pynetmap/"+self._name+self.ext, "wb")
                if self._secret:
                    jsonStr = Secret(CRYPTO_KEY_ENCRYPTION).encrypt(jsonStr)
                else:
                    jsonStr = jsonStr.encode()
                jsonFile.write(jsonStr)
                jsonFile.close()
