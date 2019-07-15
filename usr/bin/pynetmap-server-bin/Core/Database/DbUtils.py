
from Core.Database.Table import Table
from Core.Database.Database import Database
from Constants import *

class DbUtils:
    __DB__ = None
    

    @staticmethod
    def getInstance():
        if DbUtils.__DB__ == None:
            DbUtils.__DB__ = Database()
            DbUtils.__DB__.register(DB_CONFIG, True, False)
            DbUtils.__DB__.register(DB_LANG, True, False)
            DbUtils.__DB__.register(DB_SCHEMA, True, True)
            DbUtils.__DB__.register(DB_STRUCT, True, True)
            DbUtils.__DB__.register(DB_USERS, True, True)
            DbUtils.__DB__.register(DB_SERVER, True, True)
            DbUtils.__DB__.register(DB_BASE, False, True)
            DbUtils.__DB__.register(DB_SECRET, False, True)
            DbUtils.__DB__.register(DB_MODULE, False, False)
            DbUtils.__DB__.register(DB_ALERT, False, False)

        return DbUtils.__DB__
