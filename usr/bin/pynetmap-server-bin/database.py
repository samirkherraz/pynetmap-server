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


class Database:
    def __init__(self):
        self.lock = Lock()
        self._head = None
        self._schema = None

    def add(self, parent_id, obj, newid=None, lst=None):
        if lst == None:
            self.lock.acquire()
            lst = self.head()
            obj["base.core.children"] = dict()
        if newid == None:
            newid = self.autoinc()
        if parent_id == None:
            self._head[newid] = obj
            self.lock.release()
            return True
        else:
            for key in lst.keys():
                if key == parent_id:
                    lst[key]["base.core.children"][newid] = obj
                    self.lock.release()
                    return True
                elif self.add(parent_id, obj, newid, lst[key]["base.core.children"]):
                    return True

        return False

    def edit(self, parent_id, newid, obj, lst=None):
        if lst == None:
            self.lock.acquire()
            klst = self.head()
            f = self.find_path(newid)
            i = 0
            for k in f:
                i += 1
                nobj = klst[k]
                if i < len(f):
                    klst = klst[k]["base.core.children"]
            del klst[f[len(f)-1]]
            for k in obj:
                nobj[k] = obj[k]
            lst = self.head()
            obj = nobj
        if parent_id == None:
            self._head[newid] = obj
            self.lock.release()
            return True
        else:
            for key in lst.keys():
                if key == parent_id:
                    lst[key]["base.core.children"][newid] = obj
                    self.lock.release()
                    return True
                elif self.edit(parent_id, newid, obj, lst[key]["base.core.children"]):
                    return True
        return False

    def delete(self, parent_id, newid, lst=None):
        if lst == None:
            self.lock.acquire()
            lst = self.head()
        if parent_id == None:
            del self._head[newid]
            self.lock.release()
            return True
        else:
            for key in lst.keys():
                if key == parent_id:
                    del lst[key]["base.core.children"][newid]
                    self.lock.release()
                    return True
                elif self.delete(parent_id, newid, lst[key]["base.core.children"]):
                    return True

        return False

    def find_by_schema(self, schema, lst=None):
        out = dict()
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            key = str(key)
            if str(lst[key]["base.core.schema"]).upper() == str(schema).upper():
                out[key] = lst[key]
            out = dict(out.items() + self.find_by_schema(schema,
                                                         lst[key]["base.core.children"]).items())

        return out

    def find_parent(self, id, lst=None):
        try:
            return self.find_path(id).reverse()[1]
        except:
            return None

    def find_by_id(self, id, lst=None):
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            if key.upper() == id.upper():
                r = dict()
                r[key] = lst[key]
                return r
            else:
                r = self.find_by_id(id, lst[key]["base.core.children"])
                if r != None:
                    return r

        return None

    def find_by_name(self, id, lst=None):
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            if lst[key]["base.core.name"].upper() == id.upper():
                r = dict()
                r[key] = lst[key]
                return r
            else:
                r = self.find_by_name(id, lst[key]["base.core.children"])
                if r != None:
                    return r

        return None

    def search_in_attr(self, id, lst=None):
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            for k in lst[key]:
                if k != "base.core.children" and lst[key][k] != None and id.upper() in lst[key][k].upper():
                    return lst[key]
            else:
                r = self.search_in_attr(id, lst[key]["base.core.children"])
                if r != None:
                    return r

        return None

    def find_path(self, id, lst=None):
        out = []
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            key = str(key)
            if key == id:
                out.append(id)
                return out
            else:
                res = self.find_path(id, lst[key]["base.core.children"])
                if len(res) > 0:
                    out.append(key)
                    out += res

        return out

    def replace_data(self, data):

        with self.lock:
            self._head = data

    def replace_schema(self, data):
        with self.lock:
            self._schema = data

    def read(self):
        try:
            jsonFile = codecs.open(WORKING_DIR+"base.json", "r", "utf-8")
            jsonStr = jsonFile.read()
            jsonFile.close()
            self._head = json.loads(jsonStr)
        except:
            print "Error"
            self._head = dict()

        try:
            jsonFile = codecs.open(WORKING_DIR+"history.json", "r", "utf-8")
            jsonStr = jsonFile.read()
            jsonFile.close()
            self._head.update(json.loads(jsonStr))
        except:
            print "Error"

        jsonFile = codecs.open(WORKING_DIR+"schema.json", "r", "utf-8")
        jsonStr = jsonFile.read()
        jsonFile.close()
        self._schema = json.loads(jsonStr)

    def write(self):
        copyfile(WORKING_DIR+"base.json", BACKUP_DIR +
                 "base"+str(time.time())+".json")
        jsonStr = json.dumps(self.get_persistant())
        jsonFile = codecs.open(WORKING_DIR+"base.1.json", "w", "utf-8")
        jsonFile.write(jsonStr)
        jsonFile.close()

        try:
            jsonStr = json.dumps(self.get_volatile())
            jsonFile = codecs.open(WORKING_DIR+"history.json", "w", "utf-8")
            jsonFile.write(jsonStr)
            jsonFile.close()
        except:
            print ("ERROR : Unable to export, database corrupted")

    def head(self):
        return self._head

    def get_persistant(self, lst=None):
        return self.filter("base.")

    def filter(self, module, lst=None):
        cl = dict()
        if lst == None:
            lst = self._head

        for i in lst:

            cl[i] = dict()
            for j in lst[i]:
                if type(module) is list:
                    for e in module:
                        if e in j:
                            cl[i][j] = lst[i][j]
                else:
                    if j.startswith(module):
                        cl[i][j] = lst[i][j]
            cl[i]["base.core.children"] = self.filter(
                module, lst[i]["base.core.children"])

        return cl

    def get_volatile(self, lst=None):
        return self.filter("module.")

    def autoinc(self):
        return "EL_"+str(str(time.time()))+''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(5))

    def schema(self):
        return self._schema["__MODEL__"]

    def get_model(self, model):
        return self.schema()[model]["Fields"]

    def add_model(self, model):
        self.schema()[model] = dict()
        self.schema()[model]["Fields"] = dict()
        self.schema()[model]["AutoInc"] = 0

    def remove_model(self, model):
        del self.schema()[model]

    def update_model(self, model, name):
        m = self.schema()[model]
        del self.schema()[model]
        self.schema()[name] = m
        m = self.schema()[model]
        del self.schema()[model]
        self.schema()[name] = m

    def add_field(self, model, name, default=None):
        self.schema()[model]["Fields"][name] = default
        for k in self.schema()[model].keys():
            self.schema()[model][k][name] = default

    def remove_field(self, model, name):
        del self.schema()[model]["Fields"][name]
        for k in self.schema()[model].keys():
            del self.schema()[model][k][name]

    def update_field(self, model, name, new, default=None):
        del self.schema()[model]["Fields"][name]
        self.schema()[model]["Fields"][new] = default
        for k in self.schema()[model].keys():
            m = self.schema()[model][k][name]
            del self.schema()[model][k][name]
            self.schema()[model][k][new] = m
