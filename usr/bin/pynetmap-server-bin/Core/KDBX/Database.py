from pykeepass import PyKeePass
from pykeepass.entry import Entry

class Database:
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


    def __init__(self):
        self.__db =  PyKeePass(Database.FILENAME, password=Database.PASSWORD) 
    
    def save(self):
        self.__db.save()

    def set(self,id, data={},table="__PYNETMAP__"):
        parent = self.__db.find_groups_by_uuid(id)
        if len(parent) <= 0:
                return False
        else:
                parent = parent[0]
        found = False
        for e in parent.entries:
            if e.title == table:
                found = True
                for k,v in data.items():
                    e._set_string_field(k, v)
                self.save()
        if not found:
            e = self.__db.add_entry(destination_group=parent, title=table, username="", password="")
            for k,v in data.items():
                e._set_string_field(k, v)
            self.save()
        return True
        
    def move(self, id, dest):
        self.__db.move_group(id, dest)

    def structure(self, parent=None):
        d = dict()
        if parent is None:
            parent = self.__db.root_group
        for e in parent.subgroups:
            d[e.uuid] = self.structure(e)
        return d


    def get(self,id,table="__PYNETMAP__", keys=["UserName", "PassWord", "Ip", "Port"]):
        parent = self.__db.find_groups_by_uuid(id)
        if len(parent) <= 0:
                return None
        else:
                parent = parent[0]
        for e in parent.entries:
            if e.title == table:
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
        e = self.__db.add_entry(destination_group=group, title=Database.ENTRY_NAME, username="", password="")
        for k,v in data.items():
            e._set_string_field(k, v)
        self.save()
        return group.uuid

