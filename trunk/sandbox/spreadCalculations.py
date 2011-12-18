'''
Created on 28 okt 2011

@author: jev
''' 

from tradingWithPython import estimateBeta, Spread, returns, Portfolio
from tradingWithPython.lib import yahooFinance
from pandas import DataFrame
import numpy as np
import matplotlib.pyplot as plt
import os


startDate = (2010,1,1)
# create two timeseries. data for SPY goes much further back
# than data of VXX


y = yahooFinance.HistData()

dataFile = 'spreadCalc.csv'               

symbols = ['GLD','GDX']


y.loadSymbols(dataFile,symbols)
df =y.df.tail(500)


p = Portfolio(df, name='test spread')
print p
#


#s = Spread(df)
#s.calculateStatistics(df[symbols[0]])

#print s
#print '-'*30
#print yahooFinance.getQuote(symbols)
#(s.spreadReturns).cumsum().plot()

#f = plt.figure(1)
#s.plot(f)