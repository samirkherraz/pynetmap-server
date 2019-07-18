
from Core.Database.Table import Table
from Core.Database.Database import Database
from Constants import *
from Core.Database.Table import Table
from shutil import copyfile
import codecs
from Core.Utils.Logging import getLogger
logging = getLogger(__package__)




class DbUtils:
    __DB__ = None

    __TABLES__ = [
        (DB_CONFIG, True, False, False),
        (DB_MODULE, False, False, False),
        (DB_ALERT, False, False, False),
        (DB_BASE, False, True, True),
        (DB_SCHEMA, True, True, True),
        (DB_STRUCT, True, True, True),
        (DB_USERS, True, True, True),
        (DB_SERVER, True, True, True)
    ]

    @staticmethod
    def getInstance():
        if DbUtils.__DB__ is None:
            DbUtils.encrypt_databases()
            DbUtils.__DB__ = Database()
            for args in DbUtils.__TABLES__:
                DbUtils.__DB__.register(*args)
            DbUtils.__DB__.reindex()

        return DbUtils.__DB__

    @staticmethod
    def encrypt_databases():
        for (name, _, persist, secret) in DbUtils.__TABLES__:
            try:
                copyfile("/var/lib/pynetmap/"+name+".bin",
                        "/var/lib/pynetmap/"+name+".bin.bak")
                copyfile("/var/lib/pynetmap/"+name+".json",
                        "/var/lib/pynetmap/"+name+".json.bak")
            except:
                pass
            try:
                jsonFile = codecs.open(
                    "/var/lib/pynetmap/"+name+".json", "rb")
                jsonFile.close()
                tdec = Table(name, persist, False)
                tenc = Table(name, persist, secret)
                tenc._head = tdec._head
                tenc._changed = True
                tenc.write()
                os.remove("/var/lib/pynetmap/"+name+".json")
                logging.info(f'Encrypted  {name}')
            except:
                pass    
