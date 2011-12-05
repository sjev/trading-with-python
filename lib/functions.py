# -*- coding: utf-8 -*-
"""
twp support functions

@author: Jev Kuznetsov
Licence: GPL v2
"""

from scipy  import  polyfit, polyval
from datetime import datetime, date
import urllib2
from pandas import DataFrame, Index
import numpy as np


def estimateBeta(priceX,priceY):
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
        
    return beta    

def renameTs(series, name=None):
    ''' 
    return a renamed copy of time series
    '''
    s = series.copy()    
    s.name =name
    return s