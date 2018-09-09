#!/usr/bin/python
import gnupg
from shutil import copyfile
import json
import os
import codecs
import time
import random
import string
from const import WORKING_DIR, BACKUP_DIR
from threading import Lock
from table import Table
from utils import Utils


class Database:
    def __init__(self):
        self.lock = Lock()
        self.tables = dict()
        self.specials = []
        self.register("schema", True)
        self.register("structure", True)
        self.register("users", True)
        self.register("server", True)

        self.register("base")
        self.register("module")
        self.register("alert")
        self.read()
        self.cleanup()
        self.write()

    def cleanup(self):
        valides = self.rebuild()
        for name in self.tables:
            if name not in self.specials:
                self.tables[name].cleanup(valides)

    def register(self, name, special=False):
        if special == True:
            self.specials.append(name)
        self.tables[name] = Table(name)

    def get_table(self, name):
        try:
            return self.tables[name].get_data()
        except:
            return None

    def set_table(self, name, data):
        try:
            self.tables[name].set_data(data)
        except:
            pass

    def autoinc(self):
        return "EL_"+str(str(time.time()))+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    def rebuild(self, lst=None):
        if lst == None:
            lst = self.tables["structure"].get_data()

        out = []
        for key in lst.keys():
            out.append(key)
            out = out + self.rebuild(lst[key])

        return out

    def create(self, parent_id=None, newid=None, lst=None):
        if lst == None:
            lst = self.tables["structure"].get_data()
        if newid == None:
            newid = self.autoinc()
        if parent_id == None:
            self.tables["structure"].get_data()[newid] = {}
            self.cleanup()
            return newid
        else:
            for key in lst.keys():
                if key == parent_id:
                    lst[key][newid] = {}
                    self.cleanup()
                    return newid
                elif self.create(parent_id, newid, lst[key]):
                    return newid
        return None

    def move(self, id, parentid, elm=None, lst=None):
        if lst == None:
            lst = self.tables["structure"].get_data()
            path = self.find_path(id)
            elm = lst
            par = None
            elmid = None
            for e in path:
                par = elm
                elmid = e
                elm = par[elmid]
            del par[elmid]

        for key in lst.keys():
            if key == parentid:
                lst[key][id] = elm
                self.cleanup()
                return True
            elif self.move(id, parentid, elm, lst[key]):
                return True

        return False

    def get(self, table, key):
        try:
            return self.tables[table].get(key)
        except ValueError as e:
            Utils.debug("Database", e, 2)

    def set(self, table, key, value):
        self.tables[table].set(key, value)

    def set_attr(self, table, id, key, value):
        try:
            self.tables[table].set_attr(id, key, value)
        except ValueError as e:
            Utils.debug("Database", e, 2)

    def get_attr(self, table, id, key):
        try:
            return self.tables[table].get_attr(id, key)
        except ValueError as e:
            Utils.debug("Database", e, 2)

    def delete(self, parent_id, newid, lst=None):
        if lst == None:
            lst = self.tables["structure"].get_data()
        if parent_id == None:
            del self.tables["structure"].get_data()[newid]
            self.cleanup()
            return True
        else:
            for key in lst.keys():
                if key == parent_id:
                    del lst[key][newid]
                    self.cleanup()
                    return True
                elif self.delete(parent_id, newid, lst[key]):
                    return True
        return False

    def get_children(self, id, lst=None):
        if lst == None:
            lst = self.tables["structure"].get_data()

        for key in lst.keys():
            if key == id:
                return lst[key]
            else:
                out = self.get_children(id, lst[key])
                if out != None:
                    return out

        return None

    def find_by_attr(self,  id, attr=None):
        out = []
        for key in self.get_table("base"):
            if attr != None:
                if str(self.tables["base"].get(key)[attr]).upper() == str(id).upper():
                    out.append(key)
            for value in self.tables["base"].get(key):
                if str(self.tables["base"].get(key)[value]).upper() == str(id).upper():
                    out.append(key)
        return out

    def find_by_schema(self, schema):
        out = []
        for key in self.get_table("base"):
            if str(self.tables["base"].get(key)["base.core.schema"]).upper() == str(schema).upper():
                out.append(key)

        return out

    def find_parent(self, id, lst=None):
        try:
            return self.find_path(id).reverse()[1]
        except:
            return None

    def find_path(self, id, lst=None):
        out = []
        if lst == None:
            lst = self.tables["structure"].get_data()

        for key in lst.keys():
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
        for name in self.tables:
            self.tables[name].read()

    def write(self):
        for name in self.tables:
            self.tables[name].write()
