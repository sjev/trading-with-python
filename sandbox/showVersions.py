# -*- coding: utf-8 -*-
"""
show versions of essential modules
"""
import ib
import pandas as pd
import tradingWithPython as twp
import sys

print 'sys: ' , sys.version
print 'twp:', twp.__version__
print 'ibpy:' , ib.version
print 'Pandas: ', pd.__version__



