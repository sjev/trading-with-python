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
        """ set number of shares. shares: Series({symbol:shares}) """
        
        if len(shares) != self.histPrice.shape[1]:
            raise AttributeError('Wrong size of shares vector.')
        self.params['shares'] = shares
        
    
    def setCapital(self,capital):
        if len(capital) != self.histPrice.shape[1]:
            raise AttributeError('Wrong size of shares vector.')
        self.params['capital'] = capital
    
   
    def returns(self):
        pass
    
    @property
    def symbols(self):
        return self.histPrice.columns.tolist()
    
    def __repr__(self):
        return ("Spread %s \n" % self.name ) + str(self.params)
        #return ('Spread %s :' % self.name ) + str.join(',',
        #        ['%s*%.2f' % t  for t in zip(self.symbols,self.capital)])
        
        
    


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
        self.stats = None
        
        if name is None:
            self.name = str.join("_",self.df.columns)
        else:
            self.name = name
        
        self._params2 = DataFrame(columns=df.columns) # properties for a matrix
        self._calculate(capital,bet)
       
    def __repr__(self):
        
        header = '-'*10+self.name+'-'*10
        return header+'\n'+str(self.stats)+'\n'+str(self._params2.T)
         
    def _calculate(self,capital,bet):
        ''' internal data calculation, update self._params2 ''' 
        
        res = DataFrame(index= self.symbols)
        res['last close'] = self.df.ix[-1,:]
        res['beta'] = np.nan 

        # set capital ratios
        if capital is None:
            beta = estimateBeta(self.df.ix[:,0],self.df.ix[:,1])
            res['gain'] = [1, -1/beta]
            res['capital'] = res['gain']*bet
            res.ix[1,'beta'] = beta
        else:
            res['capital'] = capital
            res['gain'] = res['capital']/bet
        
        
        res['shares'] = res['capital']/res['last close']
        
        self._params2 = res
        
        self.returns = (returns(self.df)*self._params2['gain']).sum(axis=1)    
   
    def calculateStatistics(self,other=None):
        ''' calculate spread statistics, save internally '''
        res = {}
        res['micro'] = rank(self.returns[-1],self.returns)
        res['macro'] = rank(self.spread[-1], self.spread)

        #res['75%'] = self.spread.quantile(.75)
        #res['25%'] = self.spread.quantile(.25)
        res['last'] = self.spread[-1]
        res['samples'] = len(self.df)
        if other is not None:
            res['corr'] = self.returns.corr(returns(other))
        
        return   Series(res,name=self.name)    
    @property
    def spread(self):
        return (self.df*self._params2['shares']).sum(axis=1)
   
    
    @property
    def symbols(self):
        return self.df.columns.tolist()
    
    #-----------plotting functions-------------------
    def plot(self, figure=None, rebalanced=True):
        
        if figure is None:
            figure = plt.gcf()
      
        figure.clear()
        
        ax1 = plt.subplot(2,1,1)
        if rebalanced:
            ret = returns(self.df)
            ret['spread'] = self.returns
            (100*ret).cumsum().plot(ax=ax1)
            plt.ylabel('% change')
            plt.title('Cum returns '+self.name) 
        else:
            self.spread.plot(ax=ax1, style = 'o-')
            p = self._params2.T
            plt.title('Spread %.2f %s vs %.2f %s' %(p.ix['shares',0], p.columns[0], p.ix['shares',1],p.columns[1] ))
                
        
        ax2 = plt.subplot(2,1,2,sharex = ax1)
        (self.returns*100).plot(ax=ax2, style= 'o-')
        plt.title('returns')
        plt.ylabel('% change')
        
   
        
        
if __name__=='__main__':
    spy = Symbol('SPY')
    spy.downloadHistData()
    
    iwm = Symbol('IWM')
    iwm.downloadHistData()
    
    s = Spread(spy,iwm, capitalX = 10e3)
    
        