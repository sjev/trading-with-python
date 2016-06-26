"""
worker classes

@author: Jev Kuznetsov
Licence: GPL v2
"""

__docformat__ = 'restructuredtext'

import os
from . import logger as logger
from . import yahooFinance as yahoo
from .functions import returns, rank
from datetime import date
from pandas import DataFrame, Series
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt



class PCA(object):
    """ class for executing pca transformation, works on pandas structures """
    
    def __init__(self,ds):
        """ intit with a dataset, rows are observations, columns are features """
        
        # the dataset will be normalized to zero mean per column
        self.mean = ds.mean(0)
       
        ds = ds - self.mean # subtract mean
                
        # transform
        cov_mat = np.cov(ds.T) # create covariance matrix
        eig_val, eig_vec = np.linalg.eig(cov_mat)
        
        idx = np.argsort(eig_val) # sort eigenvalues
        idx = idx[::-1] # in ascending order
        
        eig_vec = eig_vec[:,idx]
        eig_val = eig_val[idx]
               
        self.eig_vec = pd.DataFrame(eig_vec, index= ds.columns)
        self.eig_val = pd.DataFrame(eig_val, index= ds.columns)
        
    def transform(self,ds):
        """ gransform dataset to a new one """
        return pd.DataFrame(np.dot(self.eig_vec.T,ds.T).T, index=ds.index)
       




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
        self.ohlc = yahoo.getHistoricData(self.name,startDate,endDate)
    
       
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
    
    def __init__(self,stock,hedge,beta=None):
        ''' init with symbols or price series '''
        
        if isinstance(stock,str) and isinstance(hedge,str):
            self.symbols = [stock,hedge]
            self._getYahooData()
        elif isinstance(stock,pd.Series) and isinstance(hedge,pd.Series):
            self.symbols = [stock.name,hedge.name]
            self.price = pd.DataFrame(dict(list(zip(self.symbols,[stock,hedge])))).dropna()
        else:
            raise ValueError('Both stock and hedge should be of the same type, symbol string or Series')
    
        # calculate returns
        self.returns = self.price.pct_change()
        
        if beta is not None:
            self.beta = beta
        else:
            self.estimateBeta()
            
            
        # set data
        self.data = pd.DataFrame(index = self.symbols)
        self.data['beta'] = pd.Series({self.symbols[0]:1., self.symbols[1]:-self.beta})
    
    def calculateShares(self,bet):
        ''' set number of shares based on last quote '''
        if 'price' not in self.data.columns:
            print('Getting quote...')
            self.getQuote()
        self.data['shares'] = bet*self.data['beta']/self.data['price']    
        
    
    def estimateBeta(self,plotOn=False):
        """ linear estimation of beta """
        x = self.returns[self.symbols[1]] # hedge
        y = self.returns[self.symbols[0]] # stock
        
        #avoid extremes
        low = np.percentile(x,20)
        high = np.percentile(x,80)
        iValid = (x>low) & (x<high)
        
        x = x[iValid]
        y = y[iValid]
        
        if plotOn:
            plt.plot(x,y,'o')
            plt.grid(True)
        
        iteration = 1
        nrOutliers = 1
        while iteration < 3 and nrOutliers > 0 :
            
            (a,b) = np.polyfit(x,y,1)
            yf = np.polyval([a,b],x)
            
            err = yf-y
            idxOutlier = abs(err) > 3*np.std(err)
            nrOutliers =sum(idxOutlier)
            beta = a
            #print 'Iteration: %i beta: %.2f outliers: %i' % (iteration,beta, nrOutliers)
            x = x[~idxOutlier]
            y = y[~idxOutlier]
            iteration += 1

    
        if plotOn:
            yf = x*beta
            plt.plot(x,yf,'-',color='red')
            plt.xlabel(self.symbols[1])
            plt.ylabel(self.symbols[0])
        
        self.beta = beta
        return beta
    
    @property
    def spread(self):
        ''' return daily returns of the pair '''
        return (self.returns*self.data['beta']).sum(1)

    
    def getQuote(self):
        ''' get current quote from yahoo '''
        q = yahoo.getQuote(self.symbols)
        self.data['price'] = q['last']
        
    def _getYahooData(self, startDate=(2007,1,1)):
        """ fetch historic data """
        data = {}        
        for symbol in self.symbols:
            print('Downloading %s' % symbol)
            data[symbol]=(yahoo.getHistoricData(symbol,sDate=startDate)['adj_close'] )
           
        self.price = pd.DataFrame(data).dropna()
   
        
    def __repr__(self):
        return 'Spread 1*%s & %.2f*%s ' % (self.symbols[0],-self.beta,self.symbols[1])
        
    @property
    def name(self):
        return str.join('_',self.symbols)


        
if __name__=='__main__':
    
    
    s = Spread(['SPY','IWM'])
    
        