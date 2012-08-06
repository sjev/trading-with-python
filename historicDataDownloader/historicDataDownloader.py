'''
Created on 4 aug. 2012
Copyright: Jev Kuznetsov
License: BSD

a module for downloading historic data from IB

'''
import ib
import pandas
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from time import sleep
import tradingWithPython.lib.logger as logger
from pandas import DataFrame, Index
import datetime as dt
from timeKeeper import TimeKeeper
import time

timeFormat = "%Y%m%d %H:%M:%S"

class DataHandler(object):
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
        
        self._timestamp.append(dt.datetime.strptime(msg.date,timeFormat))
        for k in self._data.keys():
            self._data[k].append(getattr(msg, k))
    
    @property
    def data(self):
        ''' return  downloaded data as a DataFrame '''
        df = DataFrame(data=self._data,index=Index(self._timestamp))
        return df
    
        
class Downloader(object):
    def __init__(self,debug=False):
        self._log = logger.getLogger('DLD')        
        self._log.debug('Initializing data dwonloader. Pandas version={0}, ibpy version:{1}'.format(pandas.__version__,ib.version))

        self.tws = ibConnection()
        self._dataHandler = DataHandler(self.tws)
        
        if debug:
            self.tws.registerAll(self._debugHandler)
            self.tws.unregister(self._debugHandler,message.HistoricalData)
            
        self._log.debug('Connecting to tws')
        self.tws.connect() 
        
        self._timeKeeper = TimeKeeper() # keep track of past requests
        self._reqId = 1 # current request id
     
        
    def _debugHandler(self,msg):
        print '[debug]', msg
        
    
    def requestData(self,contract,endDateTime,durationStr='1800 S',barSizeSetting='1 secs',whatToShow='TRADES',useRTH=1,formatDate=1):  
        self._log.debug('Requesting data for %s end time %s.' % (contract.m_symbol,endDateTime))
        
        
        while self._timeKeeper.nrRequests(timeSpan=600) > 59:
            print 'Too many requests done. Waiting... '
            time.sleep(1)
        
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
    
    def getIntradayData(self,contract, dateTuple ):
        ''' get full day data on 1-s interval 
            date: a tuple of (yyyy,mm,dd)
        '''
        
        openTime = dt.datetime(*dateTuple)+dt.timedelta(hours=16)
        closeTime =  dt.datetime(*dateTuple)+dt.timedelta(hours=22)
        
        timeRange = pandas.date_range(openTime,closeTime,freq='30min')
        
        datasets = []
        
        for t in timeRange:
            datasets.append(self.requestData(contract,t.strftime(timeFormat)))
        
        return pandas.concat(datasets)
        
    
    def disconnect(self):
        self.tws.disconnect()    
        
        
if __name__=='__main__':
    
    dl = Downloader(debug=True)
    
    c = Contract()
    c.m_symbol = 'SPY'
    c.m_secType = 'STK'
    c.m_exchange = 'SMART'
    c.m_currency = 'USD'
    df = dl.getIntradayData(c, (2012,8,6))
    df.to_csv('test.csv')
    
#    df =    dl.requestData(c, '20120803 22:00:00')
#    df.to_csv('test1.csv')
#    df =    dl.requestData(c, '20120803 21:30:00')
#    df.to_csv('test2.csv')
    
    dl.disconnect()
    
    
    
    print 'Done.'