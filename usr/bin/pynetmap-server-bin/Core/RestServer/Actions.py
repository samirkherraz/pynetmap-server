#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import http.cookies
import random
import string

from Constants import *
from Core.Database.DbUtils import DbUtils
from Core.Utils.Logging import getLogger
logging = getLogger(__package__)





class Actions():
    def __init__(self, path, data, cookies):
        self.path = path
        self.data = data
        self.cookies = cookies

    def user_auth(self):
        k = dict()
        access = False
        try:
            access = self.data["username"] in DbUtils.getInstance()[DB_USERS].keys()
            access = access and DbUtils.getInstance()[DB_USERS, self.data["username"], "password" ] == self.data["password"]
        except:
            access = False
        if access:
            token = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(16))
            DbUtils.getInstance()[DB_USERS, self.data["username"], "token"] = token
            k["TOKEN"] = token
        else:
            k["TOKEN"] = None
        return k

    def user_auth_check(self):
        return {"AUTHORIZATION": True}

    def user_check(self):
        token = self.cookies["TOKEN"].value if "TOKEN" in list(
            self.cookies.keys()) else None
        username = self.cookies["USERNAME"].value if "USERNAME" in list(self.cookies.keys(
        )) else None

        if username != None and token != None:
            if DbUtils.getInstance()[DB_USERS, username, "token"] == token:
                return True
        return False

     
    def user_privilege(self, privilege):
        return DbUtils.getInstance()[DB_USERS, self.cookies["USERNAME"].value , "privilege", privilege] == True
        
        
    def get_data(self):
        if len(self.path) > 0:
            data = DbUtils.getInstance()[self.path]

        else:
            data = dict()
        return data

    def set_data(self):
        if len(self.path) > 1:
            DbUtils.getInstance()[self.path] = self.data
            DbUtils.getInstance().persist()
            
            

    def create_data(self):
        if len(self.path) == 2:
            cid = DbUtils.getInstance().create(self.path[0], self.path[1])
            DbUtils.getInstance().persist()
            return {"ID": cid}
        elif len(self.path) == 1:
            cid = DbUtils.getInstance().create(self.path[0])
            DbUtils.getInstance().persist()
            return {"ID": cid}
        else:
            cid = DbUtils.getInstance().create()
            DbUtils.getInstance().persist()
            return {"ID": cid}

    def delete_data(self):
        if len(self.path) == 2:
            DbUtils.getInstance().delete(self.path[0], self.path[1])
        elif len(self.path) == 1:
            DbUtils.getInstance().delete(None, self.path[0])

        DbUtils.getInstance().persist()
        return ["success"]

    def rm_data(self):
        del DbUtils.getInstance()[self.path]
        DbUtils.getInstance().persist()
        return ["success"]

    def cleanup_data(self):
        DbUtils.getInstance().cleanup()
        DbUtils.getInstance().persist()
        return ["success"]

    def move_data(self):
        if len(self.path) == 2:
            DbUtils.getInstance().move(self.path[0], self.path[1])
            DbUtils.getInstance().persist()
            return ["success"]

    def find(self):
        if len(self.path) == 3:
            return DbUtils.getInstance().find(self.path[0], self.path[1], self.path[2])
        elif len(self.path) == 2:
            return DbUtils.getInstance().find(self.path[0], None, self.path[1])
        else:
            return []

    def find_path(self):
        if len(self.path) == 1:
            return DbUtils.getInstance().find_path(self.path[0])
        else:
            return []

    def find_parent(self):
        if len(self.path) == 1:
            return {"Parent": DbUtils.getInstance().find_parent(self.path[0])}
        else:
            return {"Parent": None}

    def find_children(self):
        if len(self.path) == 1:
            return DbUtils.getInstance().find_children(self.path[0])
        else:
            return []

    def ping(self):
        return True

    def user_access(self):
        try:
            return {"AUTHORIZATION": self.user_privilege(self.path[0])}
        except:
            pass
            return {"AUTHORIZATION": False}

