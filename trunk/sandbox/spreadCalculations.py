'''
Created on 28 okt 2011

@author: jev
''' 

from tradingWithPython import estimateBeta, Spread, returns
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

ref = ['SPY']
symbols = ['GLD','GDX','IWM','XLE','VXX']

#os.remove(dataFile)
   
try:    
    print 'reading data file '
    y.from_csv(dataFile)
    df = y.df[ref+symbols]
except Exception as e:
    print e, 'Downloading'
    y.downloadData(ref+symbols)
    y.to_csv(dataFile)
    df = y.df[ref+symbols] 

#---build spreads
lookback = 500
spreads = []
for symbol in symbols:
    spread = Spread(df[ref+[symbol]].tail(lookback)) 
    spread.calculateStatistics(returns(df[ref[0]]))
    spreads.append(spread)

spread.plot(rebalanced=True)
#s = Spread(df)
#s.calculateStatistics(df[symbols[0]])

#print s
#print '-'*30
#print yahooFinance.getQuote(symbols)
#(s.spreadReturns).cumsum().plot()

#f = plt.figure(1)
#s.plot(f)