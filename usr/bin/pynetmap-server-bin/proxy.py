#!/usr/bin/env python
__author__ = 'Samir KHERRAZ'
__copyright__ = '(c) Samir HERRAZ 2018-2019'
__version__ = '1.2.0'
__licence__ = 'GPLv3'
import os
import sys
import Constants
Constants.LOGGING = False
from Core.Utils.Proxy import Proxy


print(""" 
  _____       _   _      _   __  __          _____
 |  __ \     | \ | |    | | |  \/  |   /\   |  __ \\
 | |__) |   _|  \| | ___| |_| \  / |  /  \  | |__) |
 |  ___/ | | | . ` |/ _ \ __| |\/| | / /\ \ |  ___/
 | |   | |_| | |\  |  __/ |_| |  | |/ ____ \| |
 |_|    \__, |_| \_|\___|\__|_|  |_/_/    \_\_|
         __/ |
        |___/

""")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        try:
            proxy = Proxy(sys.argv[1])
        except:
            print("""
        ___________________________________________________

                    Unable to access ssh 
        ___________________________________________________
        """)
            exit(0)
