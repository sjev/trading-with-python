# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 19:03:09 2011

@author: jev
"""
import numpy as np
from pandas import *

dataFile = 'D:\\Development\\tradingWithPython\\cookbook\\tritonDaily.csv'

spy = DataFrame.from_csv(dataFile)['SPY']

pos = Series(np.zeros(spy.shape[0]),index=spy.index)
pos[10:20] = 10

#pos.plot()


d = {'price':spy, 'pos':pos}
df = DataFrame(d)
df['port'] = df['price']*df['pos']

df.to_csv('pnl.csv',index_label='dates')
# = DataFrame(d)

# test data frame
#idx = spy.index[:10]
idx = DateRange('1/1/2000', periods=10)
data = np.random.rand(10,2)
df = DataFrame(data=data,index=idx,columns =['a','b'])
df.to_csv('foo.csv')


df = read_csv('foo.csv',index_col=0, parse_dates=True)
df.to_csv('bar.csv')