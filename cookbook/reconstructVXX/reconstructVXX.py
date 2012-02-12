# -*- coding: utf-8 -*-
"""
Reconstructing VXX from futures data

author: Jev Kuznetsov

License : BSD
"""
from __future__ import division
from pandas import *
import numpy as np
import os

class Future(object):
    """ vix future class, used to keep data structures simple """
    def __init__(self,series,code=None):
        """ code is optional, example '2010_01' """
        self.series = series.dropna() # price data
        self.settleDate = self.series.index[-1]
        self.dt = len(self.series) # roll period (this is default, should be recalculated)
        self.code = code # string code 'YYYY_MM'
    
    def monthNr(self):
        """ get month nr from the future code """
        return int(self.code.split('_')[1])
         
    def dr(self,date):
        """ days remaining before settlement, on a given date """
        return(sum(self.series.index>date))
    
    
    def price(self,date):
        """ price on a date """
        return self.series.get_value(date)


def returns(df):
    """ daily return """
    return (df/df.shift(1)-1)


def recounstructVXX():
    """ 
    calculate VXX returns 
    needs a previously preprocessed file vix_futures.csv     
    """
    dataDir = os.path.expanduser('~')+'/twpData'
    X = DataFrame.from_csv(dataDir+'/vix_futures.csv') # raw data table
    
    # build end dates list & futures classes
    futures = []
    codes = X.columns
    endDates = []
    for code in codes:
        f = Future(X[code],code=code)
        print code,':', f.settleDate
        endDates.append(f.settleDate)
        futures.append(f)

    endDates = np.array(endDates) 

    # set roll period of each future
    for i in range(1,len(futures)):
        futures[i].dt = futures[i].dr(futures[i-1].settleDate)


    # Y is the result table
    idx = X.index
    Y = DataFrame(index=idx, columns=['first','second','days_left','w1','w2',
                                      'ret','30days_avg'])
  
    # W is the weight matrix
    W = DataFrame(data = np.zeros(X.values.shape),index=idx,columns = X.columns)

    # for VXX calculation see http://www.ipathetn.com/static/pdf/vix-prospectus.pdf
    # page PS-20
    for date in idx:
        i =np.nonzero(endDates>=date)[0][0] # find first not exprired future
        first = futures[i] # first month futures class
        second = futures[i+1] # second month futures class
        
        dr = first.dr(date) # number of remaining dates in the first futures contract
        dt = first.dt #number of business days in roll period
        
        W.set_value(date,codes[i],100*dr/dt)
        W.set_value(date,codes[i+1],100*(dt-dr)/dt)
     
        # this is all just debug info
        p1 = first.price(date)
        p2 = second.price(date)        
        w1 = 100*dr/dt
        w2 = 100*(dt-dr)/dt
        
        Y.set_value(date,'first',p1)
        Y.set_value(date,'second',p2)
        Y.set_value(date,'days_left',first.dr(date))
        Y.set_value(date,'w1',w1)
        Y.set_value(date,'w2',w2)
        
        
        Y.set_value(date,'30days_avg',(p1*w1+p2*w2)/100)
    
    valCurr = (X*W.shift(1)).sum(axis=1) # value on day N
    valYest = (X.shift(1)*W.shift(1)).sum(axis=1) # value on day N-1
    Y['ret'] = valCurr/valYest-1    # index return on day N

    return Y


  
    

##-------------------Main script---------------------------
if __name__=="__main__":
	Y = recounstructVXX()

	print Y.head(30)#
	Y.to_csv('reconstructedVXX.csv')

