#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'

import http.cookies
import random
import string
import logging
from Constants import *
from Core.Database.DbUtils import DbUtils


class Actions():
    def __init__(self):
        self.db = DbUtils.getInstance()

    def user_auth(self, path, data, cookies):
        k = dict()
        access = False
        try:
            access = True
            access &= data["username"] in self.db[DB_USERS].keys()
            print(access)
            access &= self.db[DB_USERS, data["username"], "password" ] == data["password"]
            print(self.db[DB_USERS, data["username"], "password" ])
            print(data["password"])
            print(access)
        except ValueError as e:
            logging.error(e)
            access = False
        if access:
            token = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(16))
            self.db[DB_USERS, data["username"], "token"] = token
            self.db.persist()
            k["TOKEN"] = token
        else:
            k["TOKEN"] = None
        return k

    def user_auth_check(self,path, data ,cookies):
        return {"AUTHORIZATION": True}

    def user_check(self,cookies):
        token = cookies["TOKEN"].value if "TOKEN" in list(
            cookies.keys()) else None
        username = cookies["USERNAME"].value if "USERNAME" in list(cookies.keys(
        )) else None

        if username != None and token != None:
            if self.db[DB_USERS, username, "token"] == token:
                return True
        return False


    
    def user_privilege(self,cookies,privilege):
        return self.db[DB_USERS, cookies["USERNAME"].value , "privilege", privilege] == True
        
        
    def get_data(self, path, data, cookies):
        if len(path) > 0:
            data = self.db[path[::-1]]
        else:
            data = dict()
        return data

    def set_data(self, path, data, cookies):
        if len(path) > 1:
            self.db[path[::-1]] = data
            self.db.persist()
            
            

    def create_data(self, path, data, cookies):
        if len(path) == 2:
            cid = self.db.create(path[1], path[0])
            self.db.persist()
            return {"ID": cid}
        elif len(path) == 1:
            cid = self.db.create(path[0])
            self.db.persist()
            return {"ID": cid}
        else:
            cid = self.db.create()
            self.db.persist()
            return {"ID": cid}

    def delete_data(self, path, data, cookies):
        if len(path) == 2:
            self.db.delete(path[1], path[0])
        elif len(path) == 1:
            self.db.delete(None, path[0])

        self.db.persist()
        return ["success"]

    def cleanup_data(self, path, data, cookies):
        self.db.persist()
        return ["success"]

    def move_data(self, path, data, cookies):
        if len(path) == 2:
            self.db.move(path[1], path[0])
            self.db.persist()
            return ["success"]

    def find(self, path, data, cookies):
        if len(path) == 1:
            return self.db.find(path[0], data["attribute"], data["value"])
        else:
            return []

    def find_path(self, path, data, cookies):
        if len(path) == 1:
            return self.db.find_path(path[0])
        else:
            return []

    def find_parent(self, path, data, cookies):
        if len(path) == 1:
            return {"Parent": self.db.find_parent(path[0])}
        else:
            return {"Parent": None}

    def find_children(self, path, data, cookies):
        if len(path) == 1:
            return self.db.find_children(path[0])
        else:
            return []

    def ping(self, path,data,cookies ):
        return True
    # def user_create(self, path, data, cookies):
    #     if not self.db.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
    #         return {"AUTHORIZATION": False}
    #     k = dict()
    #     try:
    #         if data["username"] not in list(self.db.get_table("users").keys()):
    #             k = dict()
    #             k["users.password"] = data["password"]
    #             k["users.privilege.edit"] = data["privilege.edit"]
    #             k["users.privilege.terminal"] = data["privilege.terminal"]
    #             k["users.token"] = None
    #             k["users.lastname"] = data["lastname"]
    #             k["users.firstname"] = data["firstname"]
    #             k["users.privilege.manage"] = data["privilege.manage"]
    #             self.db.tables["users"].set(data["username"], k)
    #             self.db.persist()

    #     except:
    #         pass

    # def user_delete(self, path, data, cookies):
    #     if not self.db.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
    #         return {"AUTHORIZATION": False}
    #     self.db.tables["users"].delete(path[0])
    #     self.db.persist()

    # def tunnel_reload(self, path, data, cookies):
    #     if not self.db.get_attr("users", cookies["USERNAME"].value, "users.privilege.manage"):
    #         return {"AUTHORIZATION": False}

    # def filter(self, data, terminal, edit, path=None):
    #     if path != None:
    #         for key in path:
    #             if not terminal and key in self.terminal_fields:
    #                 return None
    #             elif not edit and key in self.edit_fields:
    #                 return None
    #         if type(data) is dict:
    #             data = data.copy()
    #     if type(data) is dict:
    #         for key in list(data.keys()):
    #             if not terminal and key in self.terminal_fields:
    #                 del data[key]
    #             elif not edit and key in self.edit_fields:
    #                 del data[key]
    #             else:
    #                 data[key] = self.filter(data[key], terminal, edit)

    #     return data

    def user_access(self, path, data, cookies):
        try:
            return {"AUTHORIZATION": self.user_privilege(cookies,path[0])}
        except Exception as e:
            logging.error(e)
            return {"AUTHORIZATION": False}

