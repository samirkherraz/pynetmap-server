#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import codecs
import json
import time
from shutil import copyfile
from threading import Lock

from Constants import *
from Core.Database.Secret import Secret
from Core.Utils.Logging import getLogger

logging = getLogger(__package__)


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
        with self._lock:
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
                if cont[key] != value:
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
        with self._lock:
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
                if cont[key] is not None:
                    del cont[key]
                    self._changed = True
            else:
                del self._head
                self._head = dict()
                self._changed = True


    def cleanup(self, lst=None):
        with self._lock:
            if lst != None:
                for k in list(self._head.keys()):
                    if k not in lst:
                        del self._head[k]
                        self._changed = True
                for k in lst:
                    if k not in list(self._head.keys()):
                        self._head[k] = {}
                        self._changed = True

    def read(self):
        with self._lock:
            if self._persist:
                try:
                    jsonFile = codecs.open(
                        "/var/lib/pynetmap/"+self._name+self.ext, "rb")
                    jsonStr = jsonFile.read()
                    jsonFile.close()
                    if self._secret:
                        jsonStr = Secret(
                            CRYPTO_KEY_ENCRYPTION).decrypt(jsonStr)
                    self._head = json.loads(jsonStr)
                except:
                    self._head = dict()
            else:
                self._head = dict()

    def write(self):
        with self._lock:
            if self._persist and self._changed:
                logging.info(f'WRITE TABLE {self._name}')
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
