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
    def __init__(self,df,capital=None, name=None, bet = 100):
        '''
        Init Spread class, with two Symbol objects 
        
        Parameters
        ----------
        df         : input data frame. First symbol is x, second y
        capital    : amount of capital on each leg 
        
        '''
        self.df = df # price data frame
        self._params = {} # normal properties
        self._params['samples'] = len(self.df)
        
        self._params2 = DataFrame(columns=df.columns) # properties for a matrix
        self._calculate(capital,bet)
       
    def __repr__(self):
        
        items =  str.join("\n",['%s:%.2f' % item for item in self._params.items()])
        
        return '-'*30+'\n'+items+'\n'+str(self._params2.T)
         
    def _calculate(self,capital,bet):
        ''' internal data calculation, update self._params2 ''' 
        
        res = DataFrame(index= self.symbols)
        res['last close'] = self.df.ix[-1,:]
        res['beta'] = 1. 
             
#        cap = DataFrame(dict(zip(cols,)))
        # set capital ratios
        if capital is None:
            beta = estimateBeta(self.df.ix[:,0],self.df.ix[:,1])
            res['gain'] = [1, -1/beta]
            res['capital'] = res['gain']*bet
            res.ix[1,'beta'] = beta
        else:
            res['capital'] = capital
        
        
        res['shares'] = res['capital']/res['last close']
        
        self._params2 = res
    
    @property
    def spread(self):
        return (self.df*self._params2['shares']).sum(axis=1)
   
    
    @property
    def symbols(self):
        return self.df.columns.tolist()
    
    
    @property 
    def returns(self):
        return (self.df/self.df.shift(1)-1)
    
    @property 
    def spreadReturns(self):
        '''
        Daily returns of the spread
        '''
        return (self.returns*self._params2['gain']).sum(axis=1)     
    
   
        
        
if __name__=='__main__':
    spy = Symbol('SPY')
    spy.downloadHistData()
    
    iwm = Symbol('IWM')
    iwm.downloadHistData()
    
    s = Spread(spy,iwm, capitalX = 10e3)
    
        