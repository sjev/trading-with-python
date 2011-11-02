"""
worker classes

@author: Jev Kuznetsov
Licence: GPL v2
"""


import os
import tradingWithPython.lib.logger as logger
from tradingWithPython.lib.yahooFinance import getHistoricData
from datetime import date
from pandas import DataFrame

class Symbol:
    ''' 
    Symbol class, the foundation of Trading With Python library,
    This class acts as an interface to Yahoo data, Interactive Brokers etc 
    '''
    def __init__(self,symbol):
        self.symbol = symbol
        self.log = logger.getLogger(self.symbol)
        self.log.debug('class created.')
        
        self.dataDir = os.getenv("USERPROFILE")+'\\twpData\\symbols\\'+self.symbol
        self.log.debug('Data dir:'+self.dataDir)    
        self.ohlc = None # historic OHLC data
     
    def downloadHistData(self, startDate=(2010,1,1),endDate=date.today().timetuple()[:3],\
                    source = 'yahoo'):
        ''' 
        get historical OHLC data from a data source (yahoo is default)
        startDate and endDate are tuples in form (d,m,y)
        '''
        self.log.debug('Getting OHLC data')
        self.ohlc = getHistoricData(self.symbol,startDate,endDate)
    
       
    def histData(self,column='adj_close'):
        '''
        Return a column of historic data.

        Returns
        -------------        
        df : DataFrame
        '''
        s = self.ohlc[column]
        return DataFrame(s.values,s.index,[self.symbol])
        
if __name__=='__main__':
    spy = Symbol('SPY')
    spy.getOHLCData()
    
    iwm = Symbol('IWM')
    iwm.getOHLCData()
    
    joined = spy.histData().join(iwm.histData())
