#!/usr/bin/python
import gnupg
from shutil import copyfile
import json
import os
import codecs
import time
import random
import string
from const import WORKING_DIR, GPG_DIR, BACKUP_DIR
from threading import Lock


class Database:
    def __init__(self):
        self.lock = Lock()
        self.gpg = gnupg.GPG(gnupghome=GPG_DIR)
        self.email = 'pynetmap@' + os.uname()[1]
        key = "none"
        while str(key) != "" and len(self.gpg.list_keys()) < 1:
            input_data = self.gpg.gen_key_input(
                name_email=self.email)
            key = self.gpg.gen_key(input_data)

        self._head = None
        self._schema = None

    def add(self, parent_id, obj, newid=None, lst=None):
        if lst == None:
            self.lock.acquire()
            lst = self.head()
            obj["__CHILDREN__"] = dict()
        if newid == None:
            newid = self.autoinc()
        if parent_id == None:
            self._head[newid] = obj
            self.lock.release()
            return True
        else:
            for key in lst.keys():
                if key == parent_id:
                    lst[key]["__CHILDREN__"][newid] = obj
                    self.lock.release()
                    return True
                elif self.add(parent_id, obj, newid, lst[key]["__CHILDREN__"]):
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
                    klst = klst[k]["__CHILDREN__"]
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
                    lst[key]["__CHILDREN__"][newid] = obj
                    self.lock.release()
                    return True
                elif self.edit(parent_id, newid, obj, lst[key]["__CHILDREN__"]):
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
                    del lst[key]["__CHILDREN__"][newid]
                    self.lock.release()
                    return True
                elif self.delete(parent_id, newid, lst[key]["__CHILDREN__"]):
                    return True

        return False

    def find_by_schema(self, schema, lst=None):
        out = dict()
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            key = str(key)
            if str(lst[key]["__SCHEMA__"]).upper() == str(schema).upper():
                out[key] = lst[key]
            out = dict(out.items() + self.find_by_schema(schema,
                                                         lst[key]["__CHILDREN__"]).items())

        return out

    def find_by_id(self, id, lst=None):
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            if key.upper() == id.upper():
                return lst[key]
            else:
                r = self.find_by_id(id, lst[key]["__CHILDREN__"])
                if r != None:
                    return r

        return None

    def find_by_name(self, id, lst=None):
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            if lst[key]["__ID__"].upper() == id.upper():
                r = dict()
                r[key] = lst[key]
                return r
            else:
                r = self.find_by_name(id, lst[key]["__CHILDREN__"])
                if r != None:
                    return r

        return None

    def search_in_attr(self, id, lst=None):
        if lst == None:
            lst = self.head()

        for key in lst.keys():
            for k in lst[key]:
                if k != "__CHILDREN__" and lst[key][k] != None and id.upper() in lst[key][k].upper():
                    return lst[key]
            else:
                r = self.search_in_attr(id, lst[key]["__CHILDREN__"])
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
                res = self.find_path(id, lst[key]["__CHILDREN__"])
                if len(res) > 0:
                    out.append(key)
                    out += res

        return out

    def encrypt(self, plaintext):
        return str(self.gpg.encrypt(plaintext, self.email))

    def decrypt(self, ciphertext):
        return self.gpg.decrypt(ciphertext).data

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
            jsonStr = self.decrypt(jsonStr)
            self._head = json.loads(jsonStr)
        except:
            self._head = dict()

        jsonFile = codecs.open(WORKING_DIR+"schema.json", "r", "utf-8")
        jsonStr = jsonFile.read()
        jsonFile.close()
        self._schema = json.loads(jsonStr)

    def write(self):
        copyfile(WORKING_DIR+"base.json", BACKUP_DIR +
                 "base"+str(time.time())+".json")
        try:
#            jsonStr = json.dumps(self.get_clean())
            jsonStr = json.dumps(self.head())
            jsonStr = self.encrypt(jsonStr)
            jsonFile = codecs.open(WORKING_DIR+"base.json", "w", "utf-8")
            jsonFile.write(jsonStr)
            jsonFile.close()
        except:
            print ("ERROR : Unable to export, database corrupted")

    def head(self):
        return self._head

    def get_clean(self, lst=None):
        cl = dict()
        if lst == None:
            lst = self._head

        for i in lst:

            cl[i] = dict()
            for j in lst[i]:
                if j in self.get_model(lst[i]["__SCHEMA__"]).keys():
                    cl[i][j] = lst[i][j]

            cl[i]["__SCHEMA__"] = lst[i]["__SCHEMA__"]
            cl[i]["__ID__"] = lst[i]["__ID__"]
            cl[i]["__CHILDREN__"] = self.get_clean(lst[i]["__CHILDREN__"])

        return cl

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
