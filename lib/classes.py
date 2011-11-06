"""
worker classes

@author: Jev Kuznetsov
Licence: GPL v2
"""


import os
import tradingWithPython.lib.logger as logger
from tradingWithPython.lib.yahooFinance import getHistoricData
from tradingWithPython.lib.functions import estimateBeta
from datetime import date
from pandas import DataFrame
import numpy as np

class Symbol(object):
    ''' 
    Symbol class, the foundation of Trading With Python library,
    This class acts as an interface to Yahoo data, Interactive Brokers etc 
    '''
    def __init__(self,name):
        self.name = name
        self.log = logger.getLogger(self.name)
        self.log.debug('class created.')
        
        self.dataDir = os.getenv("USERPROFILE")+'\\twpData\\symbols\\'+self.name
        self.log.debug('Data dir:'+self.dataDir)    
        self.ohlc = None # historic OHLC data
     
    def downloadHistData(self, startDate=(2010,1,1),endDate=date.today().timetuple()[:3],\
                    source = 'yahoo'):
        ''' 
        get historical OHLC data from a data source (yahoo is default)
        startDate and endDate are tuples in form (d,m,y)
        '''
        self.log.debug('Getting OHLC data')
        self.ohlc = getHistoricData(self.name,startDate,endDate)
    
       
    def histData(self,column='adj_close'):
        '''
        Return a column of historic data.

        Returns
        -------------        
        df : DataFrame
        '''
        s = self.ohlc[column]
        return DataFrame(s.values,s.index,[self.name])
    
    @property
    def dayReturns(self):
        ''' close-close returns '''
        return (self.ohlc['adj_close']/self.ohlc['adj_close'].shift(1)-1)
        #return DataFrame(s.values,s.index,[self.name])


class Spread(object):
    ''' 
    Spread class, used to build a spread out of two symbols.    
    '''
    def __init__(self,symbolX, symbolY, name=None, capitalX = 100):
        '''
        Init Spread class, with two Symbol objects 
        '''
        if name is None:
            self.name = symbolX.name+'_'+symbolY.name
        
        self.symbolX = symbolX
        self.symbolY = symbolY
     
        # set capital ratios
        
        self.beta = estimateBeta(self.symbolX.ohlc['adj_close'], self.symbolY.ohlc['adj_close'])            
        self.capital = np.array([capitalX,-capitalX/self.beta])      
        
        #init log
        self.log = logger.getLogger(self.name)
        self.log.debug('Spread '+self.name+' created')
    
    @property 
    def dayReturns(self):
        '''
        Daily returns of the spread
        '''
        return self.capital[0]*self.symbolX.dayReturns + self.capital[1]*self.symbolY.dayReturns       
    
    @property    
    def X(self):
        ''' price matrix '''
        return self.symbolX.histData().join(self.symbolY.histData())
   
    @property
    def lastCloseShares(self):
        ''' amount of shares on last close '''
        sh = self.capital/self.X.ix[-1,:].values
        
        return sh
        
        
if __name__=='__main__':
    spy = Symbol('SPY')
    spy.downloadHistData()
    
    iwm = Symbol('IWM')
    iwm.downloadHistData()
    
    s = Spread(spy,iwm, capitalX = 10e3)
    
        