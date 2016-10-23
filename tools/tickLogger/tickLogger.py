"""

``tickLogger.py`` is a script to log tick events to a file.

* symbols to log and data location are stored in a `yml` config file
* default configuration is read from ``settings.yml`` , you can provide different
  file through command line parameter.
* ticks are logged to a rotating csv file, new file will start on midnight

.. :note:
    If you need to run this program for longer time periods, it is advisable
    to use IB Gateway instead of IB TWS. The latter, will automatically log off at
    the end of each day.



Running script
----------------

.. argparse::
	:module: tickLogger
	:func: getParser
	:prog: tickLogger


 
"""

import argparse # command line argument parser
import datetime as dt # date and time functions
import time # time module for timestamping
import os # used to create directories
import sys # used to print a dot to a terminal without new line
import yaml
 
#--------ibpy imports ----------------------
from ib.ext.Contract import Contract
from ib.opt import ibConnection
 
# tick type definitions, see IB api manual
priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'}
sizeTicks = {0:'bid',3:'ask',5:'last',8:'volume'}
 

 
class RotatingFile():
    """ data file rotated each day """
    
    def __init__(self,path):
        
        self._path = path
        
        
        # open file
        self._newFile()
        
    def _day_changed(self):
        return self._day != time.localtime().tm_mday 

    def _newFile(self):
        """ create filename """
        fileName = 'tickLog_%s.csv' % dt.datetime.now().strftime('%Y%m%d_%H%M%S')
        fileName = os.path.join(self._path, fileName)
        print('Logging ticks to ' , fileName)
        self._file = open(fileName,'w')       
        
        self._day = time.localtime().tm_mday
        
    def write(self, *args):
        
        if self._day_changed():
            self._file.close()
            self._newFile()
        
        return getattr(self._file,'write')(*args)
    
    def close(self):
        self._file.close()
        
    def flush(self):
        self._file.flush()
        
    def __del__(self):
        self._file.close()


class TickLogger(object):
    ''' class for handling incoming ticks and saving them to file 
        will create a subdirectory 'tickLogs' if needed and start logging
        to a file with current timestamp in its name.
        All timestamps in the file are in seconds relative to start of logging
 
    '''
    def __init__(self,tws, subscriptions,dataDir ):
        ''' init class, register handlers '''
 
        tws.register(self._priceHandler,'TickPrice')
        tws.register(self._sizeHandler,'TickSize')
 
        self.subscriptions = subscriptions        
 
        # save starting time of logging. All times will be in seconds relative
        # to this moment
        self._startTime = time.time() 
 
        # create data directory if it does not exist
        if not os.path.exists(dataDir): os.mkdir(dataDir)     
 
        # open data file for writing
        self.dataFile = RotatingFile(dataDir)      
 
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
        timestamp = '%.3f' % (time.time()) # 1 ms resolution
        dataLine = ','.join(str(bit) for bit in [timestamp]+data) + '\n'
        self.dataFile.write(dataLine)
 
    def flush(self):
        ''' commits data to file'''
        self.dataFile.flush()
 
    def close(self):
        '''close file in a neat manner '''
        print('Closing data file')
        self.dataFile.close()
 
def printMessage(msg):
    ''' function to print all incoming messages from TWS '''
    print('[msg]:', msg)
 
def createContract(symbol,secType='STK',exchange='SMART',currency='USD'):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= secType
    c.m_exchange = exchange
    c.m_currency = currency
 
    return c
 
def getParser():
    """ create command line parser """ 
    parser = argparse.ArgumentParser(description='Log ticks for a set of stocks')
    parser.add_argument("--settings",help = 'ini file containing settings', default='settings.yml')
    
    return parser

    
#--------------main script------------------
 
if __name__ == '__main__':
 
    #-----------parse command line arguments    
      
    parser = getParser()
    args = parser.parse_args()
 
    settings = yaml.load(open(args.settings,'r'))
    
    symbols = list(settings['subscriptions'].keys())
   
    print('Logging ticks for:',symbols)
    
 
    #---create subscriptions  dictionary. Keys are subscription ids   
    subscriptions = {}
    idx = 1 # subscription index
    for symbol in symbols:
        d = settings['subscriptions'][symbol]
        subscriptions[idx] = createContract(symbol,d['secType'],d['exchange'],d['currency'])
        idx+=1
 
    tws = ibConnection()
    logger = TickLogger(tws,subscriptions,settings['dataRoot'])
 
    # print all messages to the screen if verbose option is chosen
    tws.enableLogging() # show debugging output from ibpy
 
    tws.connect()
 
    #-------subscribe to data
    for subId, c in subscriptions.items():
        tws.reqMktData(subId,c,"",False)
 
    #------start a loop that must be interrupted with Ctrl-C
    print('Press Ctr-C to stop loop')
 
    try:
        while True:
            time.sleep(2) # wait a little
            logger.flush() # commit data to file
 
    except KeyboardInterrupt:
        print('Interrupted with Ctrl-c')   
 
    logger.close()             
    tws.disconnect()
    print('All done')