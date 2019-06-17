
import time
from Constants import *

def history(lst, elm):
    if type(lst) != list:
        lst = []

    lst.append({"value": elm, "date": time.time()})



