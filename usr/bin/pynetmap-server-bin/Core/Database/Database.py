#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import random
import string
import time
from threading import Event, Lock, Thread

from Constants import *
from Core.Database.Table import Table
from Core.Utils.Logging import getLogger

logging = getLogger(__package__)


class Database:

    def __init__(self):
        self._tables = dict()
        self._specials = []
        self._write_running = Event()
        self._write_lock = Lock()
        self._write_running.set()

    def register(self, name, special, persist, secret):
        if special == True:
            self._specials.append(name)
        self._tables[name] = Table(name, persist, secret)
        logging.info(
            f'REGISTER TABLE {name} [ PERSISTANCE={persist} , ENCRYPTION={secret} ]')

    def reindex(self):
        self._write_running.wait()
        valides = self._rebuild_index()
        for name in self._tables:
            if name not in self._specials:
                self._tables[name].cleanup(valides)

    def _rebuild_index(self, lst=None):
        if lst == None:
            lst = self._tables[DB_STRUCT]

        out = []
        for key in list(lst.keys()):
            out.append(key)
            out = out + self._rebuild_index(lst[key])

        return out

    def __getitem__(self, name):
        if type(name) is str:
            t = name
            others = []
        elif type(name) is tuple:
            t, *others = name
        elif type(name) is list:
            copyname = name.copy()
            t = copyname.pop(0)
            others = copyname

        return self._tables[t][others]

    def __setitem__(self, name, value):
        if type(name) is str:
            t = name
            others = []
        elif type(name) is tuple:
            t, *others = name
        elif type(name) is list:
            copyname = name.copy()
            t = copyname.pop(0)
            others = copyname
        self._write_running.wait()
        self._tables[t][others] = value

    def __delitem__(self, name):
        if type(name) is str:
            t = name
            del self._tables[t]
            return
        elif type(name) is tuple:
            t, *others = name
        elif type(name) is list:
            copyname = name.copy()
            t = copyname.pop(0)
            others = copyname
        self._write_running.wait()
        del self._tables[t][others]

    def _gen_id(self):
        return "EL_"+str(str(time.time()))+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    def create(self, parent_id=None, newid=None):
        self._write_running.wait()
        if newid is None:
            newid = self._gen_id()
        if parent_id is None:
            path = [DB_STRUCT,newid]
            self[path] = {}
            self.reindex()
            return newid
        else:
            path = self.find_path(parent_id)
            path.insert(0,DB_STRUCT)
            path.append(newid)
            self[path] = {}
            self.reindex()
            return newid



    def move(self, id, parentid):
        self._write_running.wait()
        path = self.find_path(id)
        path.insert(0, DB_STRUCT)
        data = self[path]
        del self[path]
        newpath = self.find_path(parentid)
        newpath.insert(0, DB_STRUCT)
        newpath.append(id)
        self[newpath] = data
        self.reindex()
        
    def delete(self, id):
        self._write_running.wait()
        path = self.find_path(id)
        path.insert(0, DB_STRUCT)
        del self[path]
        self.reindex()

        

    def find(self, table, attr, value):
        out = []
        for key in list(self._tables[table].keys()):
            if attr != None:
                try:
                    if str(value).upper() in str(self._tables[table][key][attr]).upper():
                        out.append(key)
                except:
                    pass
            else:
                try:
                    for e in self._tables[table][key]:
                        if str(value).upper() in str(self._tables[table][key][e]).upper():
                            out.append(key)
                except:
                    pass
        return out

    def find_children(self, id, lst=None):
        if lst == None:
            lst = self._tables[DB_STRUCT]

        for key in list(lst.keys()):
            if key == id:
                return list(lst[key].keys())
            else:
                out = self.find_children(id, lst[key])
                if out != None:
                    return out

        return None

    def find_parent(self, id, lst=None):
        try:
            path = self.find_path(id)
            return path[len(path)-2]
        except:
            return None

    def find_path(self, id, lst=None):
        out = []
        if lst == None:
            lst = self._tables[DB_STRUCT]

        for key in list(lst.keys()):
            key = str(key)
            if key == id:
                out.append(id)
                return out
            else:
                res = self.find_path(id, lst[key])
                if len(res) > 0:
                    out.append(key)
                    out += res

        return out

    def read(self):
        with self._write_lock:
            for name in self._tables:
                self._tables[name].read()

    def write(self):
        with self._write_lock:
            self._write_running.clear()
            for name in self._tables:
                self._tables[name].write()
            self._write_running.set()

    def persist(self):
        self.write()
