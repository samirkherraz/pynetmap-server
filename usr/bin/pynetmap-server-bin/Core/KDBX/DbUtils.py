from pykeepass import PyKeePass
from pykeepass.entry import Entry
import json
from lxml_to_dict import lxml_to_dict
class DbUtils:
    __DB__ = None
    FILENAME = "database.kdbx"
    PASSWORD = "aQm445WYn"
    CONFIG = "config"
    LANG = "lang"
    SCHEMA = "schema"
    STRUCT = "structure"
    USERS = "users"
    SERVER = "server"
    BASE = "base"
    SECRET = "secret"
    MODULE = "module"
    ALERT = "alert"


    ENTRY_NAME = "__PYNETMAP__"

    def register(self, groupname):
        group = self.__db.find_groups_by_name(groupname)
        if len(group) > 0:
            self.__common_groups[groupname] = group[0].uuid
        else:
            self.__common_groups[groupname] = self.__db.add_group(destination_group = self.__db.root_group, group_name=groupname).uuid

    def __init__(self):
        self.__db =  PyKeePass(DbUtils.FILENAME, password=DbUtils.PASSWORD) 
        self.__common_groups = dict()
    
    def save(self):
        self.__db.save()

    def set(self,id, data={}):
        parent = self.__db.find_groups_by_uuid(id)
        if len(parent) <= 0:
                return None
        else:
                parent = parent[0]
        for e in parent.entries:
            if e.title == DbUtils.ENTRY_NAME:
                for k,v in data.items():
                    e._set_string_field(k, v)
                self.save()
        
    def structure(self, parent=None):
        d = dict()
        if parent is None:
            parent = self.__db.root_group
        for e in parent.subgroups:
            d[e.uuid] = self.__db.tree(e)
        return d

    def get(self, id, keys=["UserName", "PassWord", "Ip", "Port"]):
        parent = self.__db.find_groups_by_uuid(id)
        if len(parent) <= 0:
                return None
        else:
                parent = parent[0]
        for e in parent.entries:
            if e.title == "__PYNETMAP__":
                d = {}
                for k in keys:
                    d[k] = e._get_string_field(k)
                return d  

    
    
    def create(self, parent,title, data={}):
        if parent is None:
            parent = self.__db.root_group
        else:
            parent = self.__db.find_groups_by_uuid(parent)
            if len(parent) <= 0:
                return None
            else:
                parent = parent[0]
        
        group = self.__db.add_group(destination_group=parent, group_name=title)
        e = self.__db.add_entry(destination_group=group, title=DbUtils.ENTRY_NAME, username="", password="")
        for k,v in data.items():
            e._set_string_field(k, v)
        self.save()
        return group.uuid


db = DbUtils()

#db.close()
