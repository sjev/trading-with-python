# -*- coding: utf-8 -*-
"""
intraday data handlers in csv format.

@author: jev
"""



import pandas as pd
import datetime as dt
import os
import numpy as np
from .extra import ProgressBar

dateFormat = "%Y%m%d" # date format for converting filenames to dates
dateTimeFormat = "%Y%m%d%H%M%S"

def fileName2date(fName):
    '''convert filename to date'''
    name = os.path.splitext(fName)[0]
    try:
        return dt.datetime.strptime(name.split('_')[1],dateTimeFormat) 
    except ValueError:
        return dt.datetime.strptime(name.split('_')[1],dateFormat) 
    
def parseDateTime(dateTimeStr):
    return dt.datetime.strptime(dateTimeStr,dateTimeFormat)
    
def loadCsv(fName):
    ''' load DataFrame from csv file '''
    return pd.DataFrame.from_csv(fName)
    
    
class HistDataCsv(object):
    '''class for working with historic database in .csv format'''
    def __init__(self,symbol,dbDir,autoCreateDir=False):
        self.symbol = symbol
        self.dbDir = os.path.normpath(os.path.join(dbDir,symbol))
        
        if not os.path.exists(self.dbDir) and autoCreateDir:
            print('Creating data directory ', self.dbDir)
            os.mkdir(self.dbDir)
        
        self.dates = []        
        
    @property 
    def files(self):
        """ a list of csv files present """
        files = os.listdir(self.dbDir)
        files.sort()
        
        return files
    
    def loadAll(self):
        """ load all files from the database and return as DataFrame """
        
        files = self.files
        
        data = [self._loadCsv(f) for f in files]
        data = pd.concat(data) 
        
        data = data.groupby(data.index).first() # remove duplicate rows
        
        return data
    
    def to_hdf(self,fName):
        """ 
        convert data to hdf5 file. If no fName is provided, the file is created in
        the database root directory """
        
        df = self.loadAll()
        df.to_hdf(fName,self.symbol)     
        
    @property        
    def dateRange(self):
        """ get min and max values of the timestamps in database """
        
        files = self.files
        if len(files) == 0:
            return (None, None)
        
        ts = [fileName2date(fName) for fName in files]
        
        # earliest
        t0 =  self._loadCsv(files[np.argmin(ts)]).index[0]
        t1 =  self._loadCsv(files[np.argmax(ts)]).index[-1]    
        
        return (t0,t1)
    
    def _loadCsv(self,fName):
        """ convenience function, prepending right path """
        return pd.DataFrame.from_csv(os.path.join(self.dbDir,fName))
    
    def saveData(self, df,lowerCaseColumns=True):
        ''' add data to database'''
        
        if lowerCaseColumns: # this should provide consistency to column names. All lowercase
            df.columns = [ c.lower() for c in df.columns]
        
        s = self.symbol+'_'+df.index[-1].strftime(dateTimeFormat)+'.csv' # file name
        dest = os.path.join(self.dbDir,s) # full path destination
        print('Saving data to: ', dest)
        df.to_csv(dest)
    
  
            
    def __repr__(self):
        rng = self.dateRange
        return '%s dataset %i files\nrange: %s ... %s' % (self.symbol, len(self.files), rng[0], rng[1] )
        
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
        
        
        for k,v in self.csv.items():
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
        t = [v.dates for v in self.csv.values()] # get all dates in a list
        
        d = list(set(t[0]).intersection(*t[1:]))
        return sorted(d)
        
     
    def __repr__(self):
        s = '-----Hist CSV Database-----\n'
        for k,v in self.csv.items():
            s+= (str(v)+'\n')
        return s
  
          
#--------------------

if __name__=='__main__':

    dbDir =os.path.normpath('D:/data/30sec')
    vxx = HistDataCsv('VXX',dbDir)
    spy = HistDataCsv('SPY',dbDir)
#   
    date = dt.date(2012,8,31)
    print(date)
#    
    pair = pd.DataFrame({'SPY':spy.loadDate(date)['close'],'VXX':vxx.loadDate(date)['close']})
    
    print(pair.tail())