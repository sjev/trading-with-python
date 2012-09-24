# -*- coding: utf-8 -*-
"""
intraday data handlers in csv format.

@author: jev
"""

from __future__ import division

from pandas import *
import numpy as np
import datetime as dt
import os

dateFormat = "%Y%m%d" # date format for converting filenames to dates
dateTimeFormat = "%Y%m%d %H:%M:%S"

def fileName2date(fName):
    '''convert filename to date'''
    name, ext = os.path.splitext(fName)
    return dt.datetime.strptime(name.split('_')[1],dateFormat).date() 
    
def parseDateTime(dateTimeStr):
    return dt.datetime.strptime(dateTimeStr,dateTimeFormat)
    
class HistDataCsv(object):
    '''class for working with historic database in .csv format'''
    def __init__(self,symbol,dbDir):
        self.symbol = symbol
        self.dbDir = os.path.normpath(os.path.join(dbDir,symbol))
        
        self.dates = []        
        
        for fName in os.listdir(self.dbDir):
            self.dates.append(fileName2date(fName))
     
    def loadDate(self,date):  
        ''' load data '''
        s = self.symbol+'_'+date.strftime(dateFormat)+'.csv' # file name
        
        df = DataFrame.from_csv(os.path.join(self.dbDir,s))
        
        cols = [col.strip() for col in df.columns.tolist()]
        df.columns = cols
       
       
        return df
        
            
    def __repr__(self):
        return '{symbol} dataset wit {nrDates} days of data'.format(symbol=self.symbol, nrDates=len(self.dates))
        
         
        
        
#--------------------

if __name__=='__main__':

    dbDir =os.path.normpath('D:/data/30sec')
    vxx = HistDataCsv('VXX',dbDir)
    spy = HistDataCsv('SPY',dbDir)
   
    date = vxx.dates[-1]   
    
    pair = DataFrame({'SPY':spy.loadDate(date)['wap'],'VXX':vxx.loadDate(date)['wap']})