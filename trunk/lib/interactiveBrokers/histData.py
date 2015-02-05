'''
Created on May 8, 2013
Copyright: Jev Kuznetsov
License: BSD

Module for downloading historic data from IB

'''

import ib
import pandas as pd
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message

import logger as logger

from pandas import DataFrame, Index

import os
import datetime as dt
import time
from time import sleep
from extra import timeFormat, dateFormat

class Downloader(object):
    def __init__(self,debug=False):
        self._log = logger.getLogger('DLD')        
        self._log.debug('Initializing data dwonloader. Pandas version={0}, ibpy version:{1}'.format(pd.__version__,ib.version))

        self.tws = ibConnection()
        self._dataHandler = _HistDataHandler(self.tws)
        
        if debug:
            self.tws.registerAll(self._debugHandler)
            self.tws.unregister(self._debugHandler,message.HistoricalData)
            
        self._log.debug('Connecting to tws')
        self.tws.connect() 
        
        self._timeKeeper = TimeKeeper() # keep track of past requests
        self._reqId = 1 # current request id
     
        
    def _debugHandler(self,msg):
        print '[debug]', msg
        
    
    def requestData(self,contract,endDateTime,durationStr='1 D',barSizeSetting='30 secs',whatToShow='TRADES',useRTH=1,formatDate=1):  
        
        if isinstance(endDateTime,dt.datetime): # convert to string
            endDateTime = endDateTime.strftime(timeFormat)
        
        
        self._log.debug('Requesting data for %s end time %s.' % (contract.m_symbol,endDateTime))
        
        
        while self._timeKeeper.nrRequests(timeSpan=600) > 59:
            print 'Too many requests done. Waiting... '
            time.sleep(10)
        
        self._timeKeeper.addRequest()
        self._dataHandler.reset()
        self.tws.reqHistoricalData(self._reqId,contract,endDateTime,durationStr,barSizeSetting,whatToShow,useRTH,formatDate)
        self._reqId+=1
    
        #wait for data
        startTime = time.time()
        timeout = 3
        while not self._dataHandler.dataReady and (time.time()-startTime < timeout):
            sleep(2)
        
        if not self._dataHandler.dataReady:
            self._log.error('Data timeout')    
         
        print self._dataHandler.data
        
        return self._dataHandler.data  
    
#     def getIntradayData(self,contract, dateTuple ):
#         ''' get full day data on 1-s interval 
#             date: a tuple of (yyyy,mm,dd)
#         '''
#         
#         openTime = dt.datetime(*dateTuple)+dt.timedelta(hours=16)
#         closeTime =  dt.datetime(*dateTuple)+dt.timedelta(hours=22)
#         
#         timeRange = pd.date_range(openTime,closeTime,freq='30min')
#         
#         datasets = []
#         
#         for t in timeRange:
#             datasets.append(self.requestData(contract,t.strftime(timeFormat)))
#         
#         return pd.concat(datasets)
        
    
    def disconnect(self):
        self.tws.disconnect()    

class _HistDataHandler(object):
    ''' handles incoming messages '''
    def __init__(self,tws):
        self._log = logger.getLogger('DH') 
        tws.register(self.msgHandler,message.HistoricalData)
        self.reset()
    
    def reset(self):
        self._log.debug('Resetting data')
        self.dataReady = False
        self._timestamp = []
        self._data = {'open':[],'high':[],'low':[],'close':[],'volume':[],'count':[],'WAP':[]}
    
    def msgHandler(self,msg):
        #print '[msg]', msg
        
        if msg.date[:8] == 'finished':
            self._log.debug('Data recieved') 
            self.dataReady = True
            return
        
        if len(msg.date) > 8:
            self._timestamp.append(dt.datetime.strptime(msg.date,timeFormat))
        else:
            self._timestamp.append(dt.datetime.strptime(msg.date,dateFormat))
                        
            
        for k in self._data.keys():
            self._data[k].append(getattr(msg, k))
    
    @property
    def data(self):
        ''' return  downloaded data as a DataFrame '''
        df = DataFrame(data=self._data,index=Index(self._timestamp))
        return df
    

        
class TimeKeeper(object):
    ''' 
    class for keeping track of previous requests, to satify the IB requirements
    (max 60 requests / 10 min)
    
    each time a requiest is made, a timestamp is added to a txt file in the user dir.
    
    '''
    
    def __init__(self):
        self._log = logger.getLogger('TK') 
        dataDir = os.path.expanduser('~')+'/twpData'
        
        if not os.path.exists(dataDir):
            os.mkdir(dataDir)

        self._timeFormat = "%Y%m%d %H:%M:%S"
        self.dataFile = os.path.normpath(os.path.join(dataDir,'requests.txt'))
        
        # Create file if it's missing
        if not os.path.exists(self.dataFile):  
            open(self.dataFile,'w').close() 
        
        self._log.debug('Data file: {0}'.format(self.dataFile))
        
    def addRequest(self):
        ''' adds a timestamp of current request'''
        with open(self.dataFile,'a') as f:
            f.write(dt.datetime.now().strftime(self._timeFormat)+'\n')
            

    def nrRequests(self,timeSpan=600):
        ''' return number of requests in past timespan (s) '''
        delta = dt.timedelta(seconds=timeSpan)
        now = dt.datetime.now()
        requests = 0

        with open(self.dataFile,'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if now-dt.datetime.strptime(line.strip(),self._timeFormat) < delta:
                requests+=1
    
        if requests==0: # erase all contents if no requests are relevant
            open(self.dataFile,'w').close() 
            
        self._log.debug('past requests: {0}'.format(requests))
        return requests


if __name__ == '__main__':
 
    from extra import createContract
     
    dl = Downloader(debug=True) # historic data downloader class
     
    contract = createContract('SPY') # create contract using defaults (STK,SMART,USD)
    data = dl.requestData(contract,"20141208 16:00:00 EST") # request 30-second data bars up till now
     
    data.to_csv('SPY.csv') # write data to csv
     
    print 'Done'