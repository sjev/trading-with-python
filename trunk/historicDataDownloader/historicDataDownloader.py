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

#----error def
class TimingError(Exception):
    ''' Exception raised when timing constraints are not met '''
    def __init__(self,msg):
        self.msg = msg


class DataHandler(object):
    ''' handles incoming messages '''
    def __init__(self,tws):
        tws.register(self.msgHandler,message.HistoricalData)
        self.reset()
    
    def reset(self):
        self.dataReady = False
        self._timestamp = []
        self._data = {'open':[],'high':[],'low':[],'close':[],'volume':[],'count':[],'WAP':[]}
    
    def msgHandler(self,msg):
        print '[msg]', msg
        
        if msg.date[:8] == 'finished':
            print 'got data'
            self.dataReady = True
            return
        
        self._timestamp.append(dt.datetime.strptime(msg.date,"%Y%m%d %H:%M:%S"))
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
     
    @property
    def data(self):
        return self._dataHandler.data 
        
    def _debugHandler(self,msg):
        print '[debug]', msg
        
    
    def requestData(self,contract,endDateTime,durationStr='1800 S',barSizeSetting='1 secs',whatToShow='TRADES',useRTH=1,formatDate=1):  
        self._log.debug('Requesting data for %s end time %s' % (contract.m_symbol,endDateTime))
        
        nrRequests = self._timeKeeper.nrRequests(timeSpan=15)
        self._log.debug('Past requests: %i' % nrRequests)
        if  nrRequests > 0:
            raise TimingError('Too many requests:%i' % nrRequests)
        
        self._timeKeeper.addRequest()
        self._dataHandler.reset()
        self.tws.reqHistoricalData(self._reqId,contract,endDateTime,durationStr,barSizeSetting,whatToShow,useRTH,formatDate)
        self._reqId+=1
    
    def disconnect(self):
        self.tws.disconnect()    
        
        
if __name__=='__main__':
    
    dl = Downloader(debug=True)
    
    c = Contract()
    c.m_symbol = 'SPY'
    c.m_secType = 'STK'
    c.m_exchange = 'SMART'
    c.m_currency = 'USD'
    try:
        dl.requestData(c, '20120803 16:00:00 EST')
    except TimingError as e:
        print 'Timing error,skipping download.'+e.msg
    
    sleep(3)
    dl.disconnect()
    
    df = dl.data
    df.to_csv('test.csv')
    
    print 'Done.'