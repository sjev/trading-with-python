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


 
# create two timeseries. data for SPY goes much further back
# than data of VXX


y = yahooFinance.HistData()
y.startDate = (2006,12,1)

dataFile = 'spreadCalc.csv'               

#symbols = ['SPY','XLE']
symbols = ['IBM','GWW']


y.loadSymbols(dataFile,symbols)
df =y.df[symbols]

p = Portfolio(df, name='test spread')

p.setShares([30,-50])
print p

p.setCapital([1.,-0.86])
print p

p.value.plot()

stat = p.calculateStatistics()
print stat

#
#ret = returns(df).dropna().values
#plot(ret[:,0],ret[:,1],'x')

# check log beta
x = log(df.ix[:,0])
y = log(df.ix[:,1])
plot(x,y)

(a,b) = polyfit(x,y,1)
yf = polyval([a,b],x)
plot(x,y,'x',x,yf,'r-')