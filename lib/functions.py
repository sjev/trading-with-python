# -*- coding: utf-8 -*-
"""
twp support functions

@author: Jev Kuznetsov
Licence: GPL v2
"""

from scipy  import  polyfit, polyval
from datetime import datetime, date
from pandas import DataFrame, Index
import numpy as np
import csv

def estimateBeta(priceX,priceY,algo = 'log'):
    '''
    estimate stock Y vs stock X beta using iterative linear
    regression. Outliers outside 3 sigma boundary are filtered out
    
    Parameters
    --------
    priceX : price series of x
    priceY : price series of y
    
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
        beta = 1/a
    
    else:
        raise TypeError("unknown algorithm type, use 'log' or 'returns'")
        
    return beta    

def rank(current,past):
    ''' calculate a relative rank 0..1 for a value against series '''
    return (current>past).sum()/float(past.count())


def returns(df):
    return (df/df.shift(1)-1)


def readBiggerScreener(fName):
    ''' import data from Bigger Capital screener '''
    with open(fName,'rb') as f:
        reader = csv.reader(f)
        rows = [row for row in reader]

    symbolA = []
    symbolB = []
    priceRatio = []
    for row in rows[1:]:
        symbolA.append(row[0])
        symbolB.append(row[1])
        priceRatio.append(row[2])
        
    
    data = {'symbolA':symbolA,'symbolB':symbolB,'priceRatio':priceRatio}
    
    return DataFrame(data)
