# -*- coding: utf-8 -*-
"""
Created on Sun Aug 05 22:06:13 2012

@author: jev
"""
import numpy as np
from pandas import *
from matplotlib.pyplot import *



#df1 = DataFrame.from_csv('test1.csv').astype(np.dtype('f4'))
#df2 = DataFrame.from_csv('test2.csv').astype(np.dtype('f4'))
#df = DataFrame([df1,df2])
df = DataFrame.from_csv('test.csv').astype(np.dtype('f4'))

close('all')
clf()
ax1=subplot(2,1,1)
df[['high','low','WAP']].plot(grid=True,ax=gca())        
        
        
subplot(2,1,2,sharex=ax1)
df[['count','volume']].plot(ax=gca())