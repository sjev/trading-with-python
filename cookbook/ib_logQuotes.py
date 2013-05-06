'''
Created on May 5, 2013
Copyright: Jev Kuznetsov
License: BSD

Demonstration of how to stream quotes from IB

'''
import datetime as dt
import time 
import os
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message


priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'}
sizeTicks = {0:'bid',3:'ask',5:'last',8:'volume'}

class TickLogger(object):
    ''' class for handling incoming ticks and saving them to file '''
    def __init__(self,tws, subscriptions):
        ''' init class, register handlers '''
        tws.registerAll(self._debugHandler)
        tws.register(self._priceHandler,message.TickPrice)
        tws.register(self._sizeHandler,message.TickSize)
        
        self.subscriptions = subscriptions        
        
        
        # save starting time of logging. All times will be in seconds relative
        # to this moment
        self._startTime = time.time() 
        
        # create data directory if it does not exist
        if not os.path.exists('tickLogs'): os.mkdir('tickLogs')     
        
        # open data file for writing
        fileName = 'tickLogs\\tickLog_%s.csv' % dt.datetime.now().strftime('%H_%M_%S')
        print 'Logging ticks to ' , fileName
        self.dataFile = open(fileName,'w')        
    
    def _debugHandler(self,msg):
        '''prints data to screen '''
        print '[msg]:', msg # print message to the screen
        
    def _priceHandler(self,msg):
        ''' price tick handler '''
        data = [self.subscriptions[msg.tickerId].m_symbol,'price',priceTicks[msg.field],msg.price] # data, second field is price tick type
        self._writeData(data)
        
    def _sizeHandler(self,msg):   
        ''' size tick handler '''
        data = [self.subscriptions[msg.tickerId].m_symbol,'size',sizeTicks[msg.field],msg.size]
        self._writeData(data)
    
    def _writeData(self,data):
        ''' write data to log file while adding a timestamp '''
        timestamp = '%.3f' % (time.time()-self._startTime) # 1 ms resolution
        dataLine = ','.join(str(bit) for bit in [timestamp]+data) + '\n'
        print dataLine
        self.dataFile.write(dataLine)
        
    def close(self):
        '''close file in a neat manner '''
        print 'Closing data file'
        self.dataFile.close()



def createContract(symbol):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= "STK"
    c.m_exchange = "SMART"
    c.m_currency = "USD"
    
    return c

#--------------main script------------------

if __name__ == '__main__':
    
    symbols = ['SPY','AAPL','XLE']    
    
    #---create subscriptions  dictionary. Keys are subscription ids   
    subscriptions = {}
    for idx, symbol in enumerate(symbols):
        subscriptions[idx+1] = createContract(symbol)
    
    tws = ibConnection()
    logger = TickLogger(tws,subscriptions)
    tws.connect()

    #-------subscribe to data
    for subId, c in subscriptions.iteritems():
        tws.reqMktData(subId,c,"",False)

    #-------print data for a couple of seconds, then close
    time.sleep(15)
                
    print 'All done'
    logger.close()             
    tws.disconnect()