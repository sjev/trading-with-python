# -*- coding: utf-8 -*-
"""
twp support functions

@author: Jev Kuznetsov
Licence: GPL v2
"""

from scipy  import  polyfit, polyval
import datetime as dt
#from datetime import datetime, date
from pandas import DataFrame, Index, Series
import csv
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def nans(shape, dtype=float):
    ''' create a nan numpy array '''
    a = np.empty(shape, dtype)
    a.fill(np.nan)
    return a


def plotCorrelationMatrix(price, thresh = None):
    ''' plot a correlation matrix as a heatmap image
        inputs:
            price: prices DataFrame
            thresh: correlation threshold to use for checking, default None

    '''
    symbols = price.columns.tolist()
    R = price.pct_change()


    correlationMatrix = R.corr()

    if thresh is not None:
        correlationMatrix = correlationMatrix > thresh

    plt.imshow(abs(correlationMatrix.values),interpolation='none')
    plt.xticks(range(len(symbols)),symbols)
    plt.yticks(range(len(symbols)),symbols)
    plt.colorbar()
    plt.title('Correlation matrix')

    return correlationMatrix


def pca(A):
    """ performs principal components analysis
    (PCA) on the n-by-p DataFrame A
    Rows of A correspond to observations, columns to variables.

    Returns :
     coeff : principal components, column-wise
     transform: A in principal component space
     latent :  eigenvalues

    """
    # computing eigenvalues and eigenvectors of covariance matrix
    M = (A - A.mean()).T # subtract the mean (along columns)
    [latent,coeff] = np.linalg.eig(np.cov(M)) # attention:not always sorted

    idx = np.argsort(latent) # sort eigenvalues
    idx = idx[::-1] # in ascending order

    coeff = coeff[:,idx]
    latent = latent[idx]

    score = np.dot(coeff.T,A.T) # projection of the data in the new space

    transform = DataFrame(index = A.index, data = score.T)

    return coeff,transform,latent



def pos2pnl(price,position , ibTransactionCost=False ):
    """
    calculate pnl based on price and position
    Inputs:
    ---------
    price: series or dataframe of price
    position: number of shares at each time. Column names must be same as in price
    ibTransactionCost: use bundled Interactive Brokers transaction cost of 0.005$/share

    Returns a portfolio DataFrame
    """

    delta=position.diff()
    port = DataFrame(index=price.index)

    if isinstance(price,Series): # no need to sum along 1 for series
        port['cash'] = (-delta*price).cumsum()
        port['stock'] = (position*price)

    else: # dealing with DataFrame here
        port['cash'] = (-delta*price).sum(axis=1).cumsum()
        port['stock'] = (position*price).sum(axis=1)



    if ibTransactionCost:
        tc = -0.005*position.diff().abs() # basic transaction cost
        tc[(tc>-1) & (tc<0)] = -1  # everything under 1$ will be ceil'd to 1$
        if isinstance(price,DataFrame): 
            tc = tc.sum(axis=1)
        port['tc'] = tc.cumsum()
    else:
        port['tc'] = 0.

    port['total'] = port['stock']+port['cash']+port['tc']



    return port

def tradeBracket(price,entryBar,maxTradeLength,bracket):
    '''
    trade a symmetrical bracket on price series, return price delta and exit bar #
    Input
    ------
        price : series of price values
        entryBar: entry bar number
        maxTradeLength : max trade duration in bars
        bracket : allowed price deviation


    '''

    lastBar = min(entryBar+maxTradeLength,len(price)-1)
    p = price[entryBar:lastBar]-price[entryBar]

    idxOutOfBound = np.nonzero(abs(p)>bracket) # find indices where price comes out of bracket
    if idxOutOfBound[0].any(): # found match
        priceDelta = p[idxOutOfBound[0][0]]
        exitBar =  idxOutOfBound[0][0]+entryBar
    else: # all in bracket, exiting based on time
        priceDelta = p[-1]
        exitBar = lastBar

    return priceDelta, exitBar


def estimateBeta(priceY,priceX,algo = 'standard'):
    '''
    estimate stock Y vs stock X beta using iterative linear
    regression. Outliers outside 3 sigma boundary are filtered out

    Parameters
    --------
    priceX : price series of x (usually market)
    priceY : price series of y (estimate beta of this price)

    Returns
    --------
    beta : stockY beta relative to stock X
    '''

    X = DataFrame({'x':priceX,'y':priceY})

    if algo=='returns':
        ret = (X/X.shift(1)-1).dropna().values

        #print len(ret)
        
        x = ret[:,0]
        y = ret[:,1]
        
        # filter high values
        low = np.percentile(x,20)
        high = np.percentile(x,80)
        iValid = (x>low) & (x<high)
        
        x = x[iValid]
        y = y[iValid]
        

        iteration = 1
        nrOutliers = 1
        while iteration < 10 and nrOutliers > 0 :
            (a,b) = polyfit(x,y,1)
            yf = polyval([a,b],x)
            #plot(x,y,'x',x,yf,'r-')
            err = yf-y
            idxOutlier = abs(err) > 3*np.std(err)
            nrOutliers =sum(idxOutlier)
            beta = a
            #print 'Iteration: %i beta: %.2f outliers: %i' % (iteration,beta, nrOutliers)
            x = x[~idxOutlier]
            y = y[~idxOutlier]
            iteration += 1

    elif algo=='log':
        x = np.log(X['x'])
        y = np.log(X['y'])
        (a,b) = polyfit(x,y,1)
        beta = a

    elif algo=='standard':
        ret =np.log(X).diff().dropna()
        beta = ret['x'].cov(ret['y'])/ret['x'].var()



    else:
        raise TypeError("unknown algorithm type, use 'standard', 'log' or 'returns'")

    return beta

def estimateVolatility(ohlc, N=10, algo='YangZhang'):
    """ 
    Volatility estimation 
    Possible algorithms: ['YangZhang', 'CC']
    
    """
    
    
    cc = np.log(ohlc.close/ohlc.close.shift(1))
    
    if algo == 'YangZhang': # Yang-zhang volatility
        ho = np.log(ohlc.high/ohlc.open)
        lo = np.log(ohlc.low/ohlc.open)
        co = np.log(ohlc.close/ohlc.open)
        
        oc = np.log(ohlc.open/ohlc.close.shift(1))
        oc_sq = oc**2
        
        
        cc_sq = cc**2
        
        rs = ho*(ho-co)+lo*(lo-co)
        
        close_vol = pd.rolling_sum(cc_sq, window=N) * (1.0 / (N - 1.0))
        open_vol = pd.rolling_sum(oc_sq, window=N) * (1.0 / (N - 1.0))
        window_rs = pd.rolling_sum(rs, window=N) * (1.0 / (N - 1.0))
        
        result = (open_vol + 0.164333 * close_vol + 0.835667 * window_rs).apply(np.sqrt) * np.sqrt(252)
        
        result[:N-1] = np.nan
    
    elif algo == 'CC': # standard close-close estimator
        result = np.sqrt(252)*np.sqrt(((pd.rolling_sum(cc**2,N))/N))
        
    else:
        raise ValueError('Unknown algo type.')
   
    return result*100 


def rank(current,past):
    ''' calculate a relative rank 0..1 for a value against series '''
    return (current>past).sum()/float(past.count())


def returns(df):
    return (df/df.shift(1)-1)

def logReturns(df):
    t = np.log(df)
    return t-t.shift(1)

def dateTimeToDate(idx):
    ''' convert datetime index to date '''
    dates = []
    for dtm in idx:
        dates.append(dtm.date())
    return dates



def readBiggerScreener(fName):
    ''' import data from Bigger Capital screener '''
    with open(fName,'rb') as f:
        reader = csv.reader(f)
        rows = [row for row in reader]

    header = rows[0]
    data = [[] for i in range(len(header))]

    for row in rows[1:]:
        for i,elm in enumerate(row):
            try:
                data[i].append(float(elm))
            except Exception:
                data[i].append(str(elm))



    return DataFrame(dict(zip(header,data)),index=Index(range(len(data[0]))))[header]

def sharpe(pnl):
    return  np.sqrt(250)*pnl.mean()/pnl.std()


def drawdown(s):
    """
    calculate max drawdown and duration

    Input:
        s, price or cumulative pnl curve $
    Returns:
        drawdown : vector of drawdwon values
        duration : vector of drawdown duration


    """
    # convert to array if got pandas series, 10x speedup
    if isinstance(s,pd.Series):
        idx = s.index
        s = s.values
        returnSeries = True
    else:
        returnSeries = False
     
    if s.min() < 0: # offset if signal minimum is less than zero
        s = s-s.min() 
     
    highwatermark = np.zeros(len(s))
    drawdown = np.zeros(len(s))
    drawdowndur = np.zeros(len(s))
 
  
    for t in range(1,len(s)):
        highwatermark[t] = max(highwatermark[t-1], s[t])
        drawdown[t] = (highwatermark[t]-s[t])
        drawdowndur[t]= (0 if drawdown[t] == 0 else drawdowndur[t-1]+1)
        
    if returnSeries:
        return pd.Series(index=idx,data=drawdown), pd.Series(index=idx,data=drawdowndur)
    else:
        return drawdown , drawdowndur


def profitRatio(pnl):
    '''
    calculate profit ratio as sum(pnl)/drawdown
    Input: pnl  - daily pnl, Series or DataFrame
    '''
    def processVector(pnl): # process a single column
        s = pnl.fillna(0)
        dd = drawdown(s)[0]
        p = s.sum()/dd.max()
        return p

    if isinstance(pnl,Series):
        return processVector(pnl)

    elif isinstance(pnl,DataFrame):

        p = Series(index = pnl.columns)

        for col in pnl.columns:
            p[col] = processVector(pnl[col])

        return p
    else:
        raise TypeError("Input must be DataFrame or Series, not "+str(type(pnl)))




def candlestick(df,width=0.5, colorup='b', colordown='r'):
    ''' plot a candlestick chart of a dataframe '''

    O = df['open'].values
    H = df['high'].values
    L = df['low'].values
    C = df['close'].values

    fig =  plt.gcf()
    ax =  plt.axes()
    #ax.hold(True)

    X = df.index


    #plot high and low
    ax.bar(X,height=H-L,bottom=L,width=0.1,color='k')

    idxUp = C>O
    ax.bar(X[idxUp],height=(C-O)[idxUp],bottom=O[idxUp],width=width,color=colorup)

    idxDown = C<=O
    ax.bar(X[idxDown],height=(O-C)[idxDown],bottom=C[idxDown],width=width,color=colordown)

    try:
        fig.autofmt_xdate()
    except Exception:  # pragma: no cover
        pass


    ax.grid(True)

    #ax.bar(x,height=H-L,bottom=L,width=0.01,color='k')

def datetime2matlab(t):
    ''' convert datetime timestamp to matlab numeric timestamp '''
    mdn = t + dt.timedelta(days = 366)
    frac = (t-dt.datetime(t.year,t.month,t.day,0,0,0)).seconds / (24.0 * 60.0 * 60.0)
    return mdn.toordinal() + frac


def getDataSources(fName = None):
    ''' return data sources directories for this machine.
    directories are defined in datasources.ini or provided filepath'''
    import socket
    from ConfigParser import ConfigParser

    pcName = socket.gethostname()

    p = ConfigParser()
    p.optionxform = str


    if fName is None:
        fName = 'datasources.ini'

    p.read(fName)

    if pcName not in p.sections():
        raise NameError('Host name section %s not found in file %s' %(pcName,fName))

    dataSources = {}
    for option in p.options(pcName):
        dataSources[option] = p.get(pcName,option)

    return dataSources

if __name__ == '__main__':
    df = DataFrame({'open':[1,2,3],'high':[5,6,7],'low':[-2,-1,0],'close':[2,1,4]})
    plt.clf()
    candlestick(df)