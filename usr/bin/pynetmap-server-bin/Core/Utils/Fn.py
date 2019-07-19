
import os
import random
import string
import time

from Constants import *
from Core.Database.DbUtils import DbUtils


def history(lst, elm):
    if type(lst) != list:
        lst = []

    lst.append({"value": elm, "date": time.time()})


def renew_ssh_pwd():
    token = ''.join(random.choice(
        string.ascii_uppercase + string.digits) for _ in range(16))
    DbUtils.getInstance()[DB_SERVER, "ssh", "password"] = token
    os.system('echo "pynetmap:'+token+'" | chpasswd')
