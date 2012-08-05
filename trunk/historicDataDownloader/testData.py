# -*- coding: utf-8 -*-
"""
Created on Sun Aug 05 22:06:13 2012

@author: jev
"""

from pandas import *
from matplotlib.pyplot import *

df = DataFrame.from_csv('test.csv')

clf()
subplot(2,1,1)
df[['open','high','low','close','WAP']].plot(ax=gca())