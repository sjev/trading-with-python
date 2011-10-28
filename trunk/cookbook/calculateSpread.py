'''
Created on 28 okt 2011

@author: jev
'''

from tradingWithPython.lib import yahooFinance

startDate = (2005,1,1)

# create two timeseries. data for SPY goes much further back
# than data of VXX
spy = yahooFinance.getHistoricData('SPY',sDate=startDate)
vxx = yahooFinance.getHistoricData('VXX',sDate=startDate)

# Combine two datasets
X = DataFrame({'VXX':vxx['adj_close'],'SPY':spy['adj_close']})

# remove NaN entries
X= X.dropna()
# make a nice picture
X.plot()