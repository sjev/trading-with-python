"""
worker classes

@author: Jev Kuznetsov
Licence: GPL v2
"""

__docformat__ = 'restructuredtext'

import os
import tradingWithPython.lib.logger as logger
from tradingWithPython.lib.yahooFinance import getHistoricData
from tradingWithPython.lib.functions import estimateBeta, returns, rank
from datetime import date
from pandas import DataFrame, Series
import numpy as np
import matplotlib.pyplot as plt

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

class Portfolio(object):
    def __init__(self,histPrice,name=''):
        """
        Constructor
        
        Parameters
        ----------
        histPrice : historic price
        
        """
        self.histPrice = histPrice
        self.params = DataFrame(index=self.symbols)
        self.params['capital'] = 100*np.ones(self.histPrice.shape[1],dtype=np.float)
        self.params['last'] = self.histPrice.tail(1).T.ix[:,0]
        self.params['shares'] = self.params['capital']/self.params['last']
        self.name= name
        
        
    def setHistPrice(self,histPrice):
        self.histPrice = histPrice
    
    def setShares(self,shares):
        """ set number of shares, adjust capital
        shares: list, np array or Series
        """
        
        if len(shares) != self.histPrice.shape[1]:
            raise AttributeError('Wrong size of shares vector.')
        self.params['shares'] = shares
        self.params['capital'] = self.params['shares']*self.params['last']
    
    def setCapital(self,capital):
        """ Set target captial, adjust number of shares """
        if len(capital) != self.histPrice.shape[1]:
            raise AttributeError('Wrong size of shares vector.')
        self.params['capital'] = capital
        self.params['shares'] = self.params['capital']/self.params['last']
    
    
    def calculateStatistics(self,other=None):
        ''' calculate spread statistics, save internally '''
        res = {}
        res['micro'] = rank(self.returns[-1],self.returns)
        res['macro'] = rank(self.value[-1], self.value)

        res['last'] = self.value[-1]
        
        if other is not None:
            res['corr'] = self.returns.corr(returns(other))
        
        return   Series(res,name=self.name)    
        
    @property
    def symbols(self):
        return self.histPrice.columns.tolist() 
    
    @property   
    def returns(self):
        return (returns(self.histPrice)*self.params['capital']).sum(axis=1)
     
    @property
    def value(self):
        return (self.histPrice*self.params['shares']).sum(axis=1)
    
    def __repr__(self):
        return ("Portfolio %s \n" % self.name ) + str(self.params)
        #return ('Spread %s :' % self.name ) + str.join(',',
        #        ['%s*%.2f' % t  for t in zip(self.symbols,self.capital)])
        
        
    


class Spread(object):
    ''' 
    Spread class, used to build a spread out of two symbols.    
    '''
    def __init__(self,symbols, bet = 100, histClose=None, beta = None):
        """ symbols : ['XYZ','SPY'] . first one is primary , second one is hedge """
        self.symbols = symbols
        self.histClose =  histClose
        if self.histClose is None:
            self._getYahooData()
        
        self.params = DataFrame(index=self.symbols)
        if beta is None:
            self.beta =self._estimateBeta()
        else:
            self.beta = beta
       
        
        self.params['capital'] = Series({symbols[0]:bet, symbols[1]:-bet/self.beta})
        self.params['lastClose'] = self.histClose.tail(1).T.ix[:,0]
        self.params['last'] = self.params['lastClose']
        self.params['shares'] = (self.params['capital']/self.params['last']) 
        
    
        self._calculate()
    def _calculate(self):
        """ internal calculations """
        self.params['change'] = (self.params['last']-self.params['lastClose'])*self.params['shares']
        self.params['mktValue'] = self.params['shares']*self.params['last']
        
    def setLast(self,last):
        """ set current price, perform internal recalculation """
        self.params['last'] = last
        self._calculate()
    
    def setShares(self,shares):
        """ set target shares, adjust capital """
        self.params['shares'] = shares
        self.params['capital'] = self.params['last']*self.params['shares']
    
    def _getYahooData(self, startDate=(2007,1,1)):
        """ fetch historic data """
        data = {}        
        for symbol in self.symbols:
            print 'Downloading %s' % symbol
            data[symbol]=(getHistoricData(symbol,startDate)['adj_close'] )
           
        self.histClose = DataFrame(data).dropna()
       
    
    def _estimateBeta(self):
        return estimateBeta(self.histClose[self.symbols[1]],self.histClose[self.symbols[0]])
        
    def __repr__(self):
        
        header = '-'*10+self.name+'-'*10
        return header+'\n'+str(self.params)+'\n'
    
    @property   
    def change(self):
        return (returns(self.histClose)*self.params['capital']).sum(axis=1)
    
    @property     
    def value(self):
        """ historic market value of the spread """
        return (self.histClose*self.params['shares']).sum(axis=1)
   
    @property
    def name(self):
        return str.join('_',self.symbols)
   
    def calculateStatistics(self):
        ''' calculate spread statistics '''
        res = {}
        res['micro'] = rank(self.params['change'].sum(),self.change)
        res['macro'] = rank(self.params['mktValue'].sum(), self.value)
        res['last'] = self.params['mktValue'].sum()
             
        return   Series(res,name=self.name)    
    
    
  
    
    #-----------plotting functions-------------------
    def plot(self, figure=None):
        
        if figure is None:
            figure = plt.gcf()
      
        figure.clear()
        
        ax1 = plt.subplot(2,1,1)
        self.value.plot(ax=ax1, style = 'o-')
        p = self.params.T
        plt.title('Spread %.2f (\$ %.2f) %s vs %.2f (\$%.2f) %s ' %(p.ix['shares',0],p.ix['capital',0], p.columns[0], 
                                                            p.ix['shares',1],p.ix['capital',1],p.columns[1]))
                
        
        ax2 = plt.subplot(2,1,2,sharex = ax1)
        (self.change).plot(ax=ax2, style= 'o-')
        plt.title('daily change')
        plt.ylabel('$ change')
        
#        ax3 = plt.subplot(3,1,3,sharex = ax1)
#        self.histClose.plot(ax=ax3)
#        plt.title('Price movements')
#        plt.ylabel('$')
        
        
if __name__=='__main__':
    
    
    s = Spread(['SPY','IWM'])
    
        