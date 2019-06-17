#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2018'
__version__ = '1.1.0'
__licence__ = 'GPLv3'

import time
import random
import string
import logging
from Core.Database.Table import Table

from threading import Lock


class Database:

    def __init__(self):
        self._tables = dict()
        self._specials = []
        self._lock = Lock()

    def register(self, name, special, persist):
        if special == True:
            self._specials.append(name)
        self._tables[name] = Table(name, persist)
        logging.getLogger(__package__).info(
            "Register Table %s as %s", name, persist)

    def reindex(self):
        valides = self.rebuild_index()
        for name in self._tables:
            if name not in self._specials:
                self._tables[name].cleanup(valides)

    def rebuild_index(self, lst=None):
        if lst == None:
            lst = self._tables["structure"]

        out = []
        for key in list(lst.keys()):
            out.append(key)
            out = out + self.rebuild_index(lst[key])

        return out

    def __getitem__(self, name):
        if type(name) != list:
            name = [name, ]
        t = name.pop(0)
        return self._tables[t][name]

    def __setitem__(self, name, value):
        with self._lock:
            if type(name) != list:
                name = [name, ]
            t = name.pop(0)
            self._tables[t][name] = value

    def genid(self):
        return "EL_"+str(str(time.time()))+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    def create(self, parent_id=None, newid=None, lst=None):
        if lst == None:
            lst = self._tables["structure"]
        if newid == None:
            newid = self.genid()
        if parent_id == None:
            self._tables["structure"][newid] = {}
            self.reindex()
            return newid
        else:
            for key in list(lst.keys()):
                if key == parent_id:
                    lst[key][newid] = {}
                    self.reindex()
                    return newid
                elif self.create(parent_id, newid, lst[key]):
                    return newid
        return None

    def move(self, id, parentid, elm=None, lst=None):
        if lst == None:
            lst = self._tables["structure"]
            path = self.find_path(id)
            elm = lst
            par = None
            elmid = None
            for e in path:
                par = elm
                elmid = e
                elm = par[elmid]
            del par[elmid]

        for key in list(lst.keys()):
            if key == parentid:
                lst[key][id] = elm
                self.reindex()
                return True
            elif self.move(id, parentid, elm, lst[key]):
                return True

        return False

    def delete(self, parent_id, newid, lst=None):
        if lst == None:
            lst = self._tables["structure"]
        if parent_id == None:
            self._tables["structure"].delete(newid)
            self.reindex()
            return True
        else:
            for key in list(lst.keys()):
                if key == parent_id:
                    del lst[key][newid]
                    self._tables["structure"]._changed = True
                    self.reindex()
                    return True
                elif self.delete(parent_id, newid, lst[key]):
                    return True
        return False

    def find(self, table, attr, value):
        out = []
        for key in list(self._tables[table].keys()):
            if attr != None:
                try:
                    if str(self._tables[table][key][attr]).upper() == str(value).upper():
                        out.append(key)
                except Exception as e:
                    logging.error(e)
                    pass
        return out

    def find_children(self, id, lst=None):
        if lst == None:
            lst = self._tables["structure"]

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
        except Exception as e:
            logging.error(e)
            return None

    def find_path(self, id, lst=None):
        out = []
        if lst == None:
            lst = self._tables["structure"]

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
        for name in self._tables:
            self._tables[name].read()

    def write(self):
        for name in self._tables:
            self._tables[name].write()

    def persist(self):
        self.write()


def Test():
    db = Database()
    db.read()
    logging.info(db[DbUtils.SCHEMA])
    logging.info(db.find(DbUtils.BASE, "base.type", "Proxmox"))
    logging.info(db.find(DbUtils.BASE, "base.os", "Linux"))
    db[DbUtils.CONFIG]["SSH"]["name"] = "samir"
    logging.info(db[DbUtils.CONFIG].toDict())
