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
import numpy as np
import csv
import matplotlib.pyplot as plt

def pos2pnl(price,position ):
    """
    calculate pnl based on price and position
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
        
    
    port['total'] = port['stock']+port['cash']

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
    

def drawdown(pnl):
    """
    calculate max drawdown and duration  

    Input:
        pnl, in $
    Returns:
        drawdown : vector of drawdwon values
        duration : vector of drawdown duration
      
    
    """
    cumret = pnl.cumsum()

    highwatermark = [0]

    idx = pnl.index
    drawdown = Series(index = idx)
    drawdowndur = Series(index = idx)
    
    for t in range(1, len(idx)) :
        highwatermark.append(max(highwatermark[t-1], cumret[t]))
        drawdown[t]= (highwatermark[t]-cumret[t])
        drawdowndur[t]= (0 if drawdown[t] == 0 else drawdowndur[t-1]+1)
    
    return drawdown, drawdowndur

def candlestick(df,width=0.5, colorup='b', colordown='r'):
    ''' plot a candlestick chart of a dataframe '''
    
    O = df['open'].values
    H = df['high'].values
    L = df['low'].values
    C = df['close'].values
    
    fig = plt.gcf()
    ax = plt.axes()
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
    
    
if __name__ == '__main__':
    df = DataFrame({'open':[1,2,3],'high':[5,6,7],'low':[-2,-1,0],'close':[2,1,4]})
    plt.clf()
    candlestick(df)