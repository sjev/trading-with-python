# -*- coding: utf-8 -*-
"""
intraday data handlers in csv format.

@author: jev
"""

from __future__ import division

import pandas as pd
import datetime as dt
import os
from extra import ProgressBar

dateFormat = "%Y%m%d" # date format for converting filenames to dates
dateTimeFormat = "%Y%m%d %H:%M:%S"

def fileName2date(fName):
    '''convert filename to date'''
    name = os.path.splitext(fName)[0]
    return dt.datetime.strptime(name.split('_')[1],dateFormat).date() 
    
def parseDateTime(dateTimeStr):
    return dt.datetime.strptime(dateTimeStr,dateTimeFormat)
    
def loadCsv(fName):
    ''' load DataFrame from csv file '''
    with open(fName,'r') as f:
        lines = f.readlines()
    
    dates= []    
    header = [h.strip() for h in lines[0].strip().split(',')[1:]]
    data = [[] for i in range(len(header))]
   
    
    for line in lines[1:]:
        fields = line.rstrip().split(',')
        dates.append(parseDateTime(fields[0]))
        for i,field in enumerate(fields[1:]):
            data[i].append(float(field))
     
    return pd.DataFrame(data=dict(zip(header,data)),index=pd.Index(dates))    
    
    
class HistDataCsv(object):
    '''class for working with historic database in .csv format'''
    def __init__(self,symbol,dbDir,autoCreateDir=False):
        self.symbol = symbol
        self.dbDir = os.path.normpath(os.path.join(dbDir,symbol))
        
        if not os.path.exists(self.dbDir) and autoCreateDir:
            print 'Creating data directory ', self.dbDir
            os.mkdir(self.dbDir)
        
        self.dates = []        
        
        for fName in os.listdir(self.dbDir):
            self.dates.append(fileName2date(fName))
    
    
    def saveData(self,date, df,lowerCaseColumns=True):
        ''' add data to database'''
        
        if lowerCaseColumns: # this should provide consistency to column names. All lowercase
            df.columns = [ c.lower() for c in df.columns]
        
        s = self.symbol+'_'+date.strftime(dateFormat)+'.csv' # file name
        dest = os.path.join(self.dbDir,s) # full path destination
        print 'Saving data to: ', dest
        df.to_csv(dest)
    
    def loadDate(self,date):  
        ''' load data '''
        s = self.symbol+'_'+date.strftime(dateFormat)+'.csv' # file name
        
        df = pd.DataFrame.from_csv(os.path.join(self.dbDir,s))
        cols = [col.strip() for col in df.columns.tolist()]
        df.columns = cols
        #df = loadCsv(os.path.join(self.dbDir,s))
       
        return df
        
    def loadDates(self,dates):
        ''' load multiple dates, concantenating to one DataFrame '''
        tmp =[]
        print 'Loading multiple dates for ' , self.symbol        
        p = ProgressBar(len(dates))
        
        for i,date in enumerate(dates):
            tmp.append(self.loadDate(date))
            p.animate(i+1)
            
        print ''
        return pd.concat(tmp)
        
        
    def createOHLC(self):
        ''' create ohlc from intraday data'''
        ohlc = pd.DataFrame(index=self.dates, columns=['open','high','low','close'])
        
        for date in self.dates:
            
            print 'Processing', date
            try:
                df = self.loadDate(date)
                
                ohlc.set_value(date,'open',df['open'][0])
                ohlc.set_value(date,'high',df['wap'].max())
                ohlc.set_value(date,'low', df['wap'].min())
                ohlc.set_value(date,'close',df['close'][-1])
        
            except Exception as e:
                print 'Could not convert:', e
                
        return ohlc
            
    def __repr__(self):
        return '{symbol} dataset with {nrDates} days of data'.format(symbol=self.symbol, nrDates=len(self.dates))
        
class HistDatabase(object):
    ''' class working with multiple symbols at once '''
    def __init__(self, dataDir):
        
        # get symbols from directory names
        symbols = []
        for l in os.listdir(dataDir):
            if os.path.isdir(os.path.join(dataDir,l)):
                symbols.append(l)
        
        #build dataset
        self.csv = {} # dict of HistDataCsv halndlers

        for symbol in symbols:
            self.csv[symbol] = HistDataCsv(symbol,dataDir)
    
    
    def loadDates(self,dates=None):
        ''' 
        get data for all symbols as wide panel
        provide a dates list. If no dates list is provided, common dates are used.
        '''
        if dates is None: dates=self.commonDates
        
        tmp = {}
        
        
        for k,v in self.csv.iteritems():
            tmp[k] = v.loadDates(dates)
            
        return pd.WidePanel(tmp)
        
    def toHDF(self,dataFile,dates=None):
        ''' write wide panel data to a hdfstore file '''
        
        if dates is None: dates=self.commonDates
        store = pd.HDFStore(dataFile)        
        wp = self.loadDates(dates)
        
        store['data'] = wp
        store.close()
        
        
        
        
    
    @property 
    def commonDates(self):
        ''' return dates common for all symbols '''
        t = [v.dates for v in self.csv.itervalues()] # get all dates in a list
        
        d = list(set(t[0]).intersection(*t[1:]))
        return sorted(d)
        
     
    def __repr__(self):
        s = '-----Hist CSV Database-----\n'
        for k,v in self.csv.iteritems():
            s+= (str(v)+'\n')
        return s
  
          
#--------------------

if __name__=='__main__':

    dbDir =os.path.normpath('D:/data/30sec')
    vxx = HistDataCsv('VXX',dbDir)
    spy = HistDataCsv('SPY',dbDir)
#   
    date = dt.date(2012,8,31)
    print date
#    
    pair = pd.DataFrame({'SPY':spy.loadDate(date)['close'],'VXX':vxx.loadDate(date)['close']})
    
    print pair.tail()