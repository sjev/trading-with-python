'''
Created on 28 okt 2011

@author: jev
''' 

from tradingWithPython import estimateBeta, Spread, returns, Portfolio, readBiggerScreener
from tradingWithPython.lib import yahooFinance
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import os


 
# create two timeseries. data for SPY goes much further back
# than data of VXX

spreads = readBiggerScreener('CointPairs.csv') 

y = yahooFinance.HistData()
y.startDate = (2006,12,1)

           

#symbols = ['SPY','XLE']
symbols = [spreads.ix[0,'symbolA'],spreads.ix[0,'symbolB']]


y.loadSymbols(dataFile,symbols)
df =y.df[symbols]

p = Portfolio(df, name='test spread')

beta = estimateBeta(df[symbols[0]],df[symbols[1]])


p.setShares([30,-50])
print p

p.setCapital([100.,-beta*100])
print p

p.value.plot()

stat = p.calculateStatistics()
print stat

#
#ret = returns(df).dropna().values
#plot(ret[:,0],ret[:,1],'x')

# check log beta
