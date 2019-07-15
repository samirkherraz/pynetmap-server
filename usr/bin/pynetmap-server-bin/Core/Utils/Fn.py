
import time
import string
import random
import os 
from Core.Database.DbUtils import DbUtils
from Constants import *

def history(lst, elm):
    if type(lst) != list:
        lst = []

    lst.append({"value": elm, "date": time.time()})

def renew():
    token = ''.join(random.choice(
                string.ascii_uppercase + string.digits) for _ in range(16))
    DbUtils.getInstance()[DB_SERVER, "ssh","password"] = token
    os.system('echo "pynetmap:'+token+'" | chpasswd')


