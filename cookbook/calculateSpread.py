'''
Created on 28 okt 2011

@author: jev
'''

from tradingWithPython import Symbol, estimateBeta
from tradingWithPython.lib import yahooFinance
from pandas import DataFrame
import numpy as np

startDate = (2010,1,1)
# create two timeseries. data for SPY goes much further back
# than data of VXX



symbolX = Symbol('SPY')
symbolY = Symbol('IWM')


symbolX.downloadHistData(startDate)
symbolY.downloadHistData(startDate)



beta = estimateBeta(symbolX.ohlc['adj_close'],symbolY.ohlc['adj_close'])


print beta