'''
Created on 28 okt 2011

@author: jev
'''

from tradingWithPython.lib import yahooFinance
from pandas import DataFrame
import numpy as np

startDate = (2005,1,1)

# create two timeseries. data for SPY goes much further back
# than data of VXX
spy = yahooFinance.getHistoricData('SPY',sDate=startDate)
iwm = yahooFinance.getHistoricData('IWM',sDate=startDate)

# Combine two datasets
X = DataFrame({'SPY':spy['adj_close'],'IWM':iwm['adj_close']})

# remove NaN entries
X= X.dropna()
# make a nice picture
X.plot(subplots=True)

# build a spread
lastPrice = X.values[-1,:]
bet = [100, -100]
shares = np.round(bet/lastPrice)

spread = (X*shares).sum(axis=1)
spread.plot()