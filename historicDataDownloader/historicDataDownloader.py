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


class Downloader(object):
    def __init__(self,debug=False):
        self._log = logger.getLogger('DLD')        
        self._log.debug('Initializing data dwonloader. Pandas version={0}, ibpy version:{1}'.format(pandas.__version__,ib.version))

        self.tws = ibConnection()
        
        if debug:
            self.tws.registerAll(self.debugHandler)
            
        self._log.debug('Connecting to tws')
        self.tws.connect() 
        
        self._reqId = 1 # current request id
        
    def debugHandler(self,msg):
        print '[debug]', msg

    
    def requestData(self,contract,endDateTime,durationStr='1800 S',barSizeSetting='1 secs',whatToShow='TRADES',useRTH=1,formatDate=1):  
        self._log.debug('Requesting data for %s end time %s' % (contract.m_symbol,endDateTime))
        
        self.tws.reqHistoricalData(self._reqId,contract,endDateTime,durationStr,barSizeSetting,whatToShow,useRTH,formatDate)
        self._reqId+=1
        
if __name__=='__main__':
    dl = Downloader(debug=True)
    
    c = Contract()
    c.m_symbol = 'SPY'
    c.m_secType = 'STK'
    c.m_exchange = 'SMART'
    c.m_currency = 'USD'
    dl.requestData(c, '20120803 22:00:00')
    sleep(3)
    
    print 'Done.'