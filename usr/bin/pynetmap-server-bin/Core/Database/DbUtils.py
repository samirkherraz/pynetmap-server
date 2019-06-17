
from Core.Database.Table import Table
from Core.Database.Database import Database


class DbUtils:
    __DB__ = None
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

    @staticmethod
    def getInstance():
        if DbUtils.__DB__ == None:
            DbUtils.__DB__ = Database()
            DbUtils.__DB__.register(DbUtils.CONFIG, True, False)
            DbUtils.__DB__.register(DbUtils.LANG, True, False)
            DbUtils.__DB__.register(DbUtils.SCHEMA, True, True)
            DbUtils.__DB__.register(DbUtils.STRUCT, True, True)
            DbUtils.__DB__.register(DbUtils.USERS, True, True)
            DbUtils.__DB__.register(DbUtils.SERVER, True, True)
            DbUtils.__DB__.register(DbUtils.BASE, False, True)
            DbUtils.__DB__.register(DbUtils.SECRET, False, True)
            DbUtils.__DB__.register(DbUtils.MODULE, False, False)
            DbUtils.__DB__.register(DbUtils.ALERT, False, False)

        return DbUtils.__DB__
