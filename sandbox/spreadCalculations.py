'''
Created on 28 okt 2011

@author: jev
''' 

from tradingWithPython import estimateBeta, Spread, returns, Portfolio, readBiggerScreener
from tradingWithPython.lib import yahooFinance
from pandas import DataFrame, Series
import numpy as np
import matplotlib.pyplot as plt
import os


 
symbols = ['SPY','IWM']
y = yahooFinance.HistData('temp.csv')
y.startDate = (2007,1,1)

df = y.loadSymbols(symbols,forceDownload=False)
#df = y.downloadData(symbols)

res = readBiggerScreener('CointPairs.csv')

#---check with spread scanner
#sp = DataFrame(index=symbols)
#
#sp['last'] = df.ix[-1,:]
#sp['targetCapital'] = Series({'SPY':100,'IWM':-100})
#sp['targetShares'] = sp['targetCapital']/sp['last']
#print sp

#The dollar-neutral ratio is about 1 * IWM - 1.7 * IWM. You will get the spread = zero (or probably very near zero)


#s = Spread(symbols, histClose = df)
#print s

#s.value.plot()

#print 'beta (returns)', estimateBeta(df[symbols[0]],df[symbols[1]],algo='returns')
#print 'beta (log)', estimateBeta(df[symbols[0]],df[symbols[1]],algo='log')
#print 'beta (standard)', estimateBeta(df[symbols[0]],df[symbols[1]],algo='standard')

#p = Portfolio(df)
#p.setShares([1, -1.7])
#p.value.plot()


quote = yahooFinance.getQuote(symbols)
print quote


s = Spread(symbols,histClose=df, estimateBeta = False)
s.setLast(quote['last'])

s.setShares(Series({'SPY':1,'IWM':-1.7}))
print s
#s.value.plot()
#s.plot()
fig = figure(2)
s.plot()


