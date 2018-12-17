

from utils import Utils
from database import Database
from error import EXIT_ERROR_CORRUPT_DB


class Model:

    def __init__(self):
        self.store = Database()
        self.utils = Utils(self.store)

    def persist(self):
        try:
            self.store.cleanup()
            self.store.write()
            return True
        except:
            return False

    def load(self):
        try:
            self.store.read()
            return True
        except:
            return False
