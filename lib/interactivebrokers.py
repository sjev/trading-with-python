'''
Copyright: Jev Kuznetsov
Licence: BSD

Interface to interactive brokers together with gui widgets

'''
import sys
#import os
from time import sleep
from PyQt4.QtCore import (SIGNAL,SLOT)
from PyQt4.QtGui import (QApplication,QFileDialog,QDialog,QVBoxLayout,QHBoxLayout,QDialogButtonBox,
                         QTableView, QPushButton,QWidget,QLabel,QLineEdit,QGridLayout,QHeaderView)

import ib
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from ib.ext.Order import Order

import tradingWithPython.lib.logger as logger
from tradingWithPython.lib.qtpandas import DataFrameModel, TableView
from tradingWithPython.lib.eventSystem import Sender
import numpy as np

import pandas
from pandas import DataFrame, Index
from datetime import datetime
import os
import datetime as dt
import time

priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 
timeFormat = "%Y%m%d %H:%M:%S"
dateFormat = "%Y%m%d"

def createContract(symbol, secType='STK', exchange='SMART',currency='USD'):
    ''' contract factory function '''
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = secType
    contract.m_exchange = exchange
    contract.m_currency = currency
    
    return contract

def _str2datetime(s):
    """ convert string to datetime """
    return datetime.strptime( s,'%Y%m%d')


def readActivityFlex(fName):
    """
    parse trade log in a csv file produced by IB 'Activity Flex Query'
    the file should contain these columns:
    ['Symbol','TradeDate','Quantity','TradePrice','IBCommission']    
    
    Returns:
        A DataFrame with parsed trade data
    
    """
    import csv    
    
    rows = []
    
    with open(fName,'rb') as f:
        reader = csv.reader(f)
        for row in reader:
            rows.append(row)
            
    header = ['TradeDate','Symbol','Quantity','TradePrice','IBCommission']
    
    types =dict(zip(header,[ _str2datetime,str , int, float, float]))
    idx = dict(zip(header,[rows[0].index(h) for h in header ] ))
    data = dict(zip(header,[[] for h in header]))
    
    for row in rows[1:]:
        print row
        for col in header:
            val = types[col](row[idx[col]])
            data[col].append(val)
            
    return DataFrame(data)[header].sort(column = 'TradeDate')



class Subscriptions(DataFrameModel, Sender):
    ''' a data table containing price & subscription data '''
    def __init__(self, tws=None):
        
        super(Subscriptions,self).__init__()
        self.df = DataFrame() # this property holds the data in a table format
      
        self._nextId = 1
        self._id2symbol = {} # id-> symbol lookup dict
        self._header = ['id','position','bid','ask','last'] # columns of the _data table
        
        # register callbacks
        if tws is not None:
            tws.register(self.priceHandler,message.TickPrice)
            tws.register(self.accountHandler,message.UpdatePortfolio)
            
            
        
    def add(self,symbol, subId = None):
        ''' 
        Add  a subscription to data table
        return : subscription id 
        
        '''
        if subId is None:
            subId = self._nextId
        
        data = dict(zip(self._header,[subId,0,np.nan,np.nan,np.nan]))
        row = DataFrame(data, index = Index([symbol]))
 
        self.df = self.df.append(row[self._header]) # append data and set correct column order
        
        self._nextId = subId+1        
        self._rebuildIndex()
        
        self.emit(SIGNAL("layoutChanged()"))
         
        return subId
    
    def priceHandler(self,msg):
        ''' handler function for price updates. register this with ibConnection class '''
        
        if priceTicks[msg.field] not in self._header: # do nothing for ticks that are not in _data table
            return
        
        self.df[priceTicks[msg.field]][self._id2symbol[msg.tickerId]]=msg.price
        
        #notify viewer
        col = self._header.index(priceTicks[msg.field])
        row = self.df.index.tolist().index(self._id2symbol[msg.tickerId])
        
        idx = self.createIndex(row,col)
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),idx, idx)
    
    def accountHandler(self,msg):
        if msg.contract.m_symbol in self.df.index.tolist():
            self.df['position'][msg.contract.m_symbol]=msg.position
    
    def _rebuildIndex(self):
        ''' udate lookup dictionary id-> symbol '''
        symbols = self.df.index.tolist()
        ids = self.df['id'].values.tolist()
        self._id2symbol = dict(zip(ids,symbols))
        
    
    def __repr__(self):
        return str(self.df)
 
    

class Broker(object):
    ''' 
    Broker class acts as a wrapper around ibConnection
    from ibPy. It tracks current subscriptions and provides
    data models to viewiers .
    '''
    def __init__(self, name='broker'):
        ''' initialize broker class
        @param dbFile: sqlite database file. will be created if it does not exist
        '''
        self.name = name
        self.log = logger.getLogger(self.name)        
        
        self.log.debug('Initializing broker. Pandas version={0}'.format(pandas.__version__))
        self.contracts = {} # a dict to keep track of subscribed contracts
        
        self.tws =  ibConnection() # tws interface
        self.nextValidOrderId = None
                
        self.dataModel = Subscriptions(self.tws) # data container
        
        self.tws.registerAll(self.defaultHandler) 
        #self.tws.register(self.debugHandler,message.TickPrice)
        self.tws.register(self.nextValidIdHandler,'NextValidId')
        self.log.debug('Connecting to tws')
        self.tws.connect()  
        
        self.tws.reqAccountUpdates(True,'')
        
    def subscribeStk(self,symbol, secType='STK', exchange='SMART',currency='USD'):
        '''  subscribe to stock data '''
        self.log.debug('Subscribing to '+symbol)        
#        if symbol in self.data.symbols:
#            print 'Already subscribed to {0}'.format(symbol)
#            return
        
        c = Contract()
        c.m_symbol = symbol
        c.m_secType = secType
        c.m_exchange = exchange
        c.m_currency = currency
        
        subId = self.dataModel.add(symbol)
        self.tws.reqMktData(subId,c,'',False)
        
        self.contracts[symbol]=c
        
        return subId
    
    @property
    def data(self):
        return self.dataModel.df
    
    
    def placeOrder(self,symbol,shares,limit=None,exchange='SMART', transmit=0):
        ''' place an order on already subscribed contract '''
        
        
        if symbol not in self.contracts.keys():
            self.log.error("Can't place order, not subscribed to %s" % symbol)
            return
        
        action = {-1:'SELL',1:'BUY'}
        
        o= Order()
        o.m_orderId = self.getOrderId()
        o.m_action = action[cmp(shares,0)]
        o.m_totalQuantity = abs(shares)
        o.m_transmit = transmit
        
        if limit is not None:
            o.m_orderType = 'LMT'
            o.m_lmtPrice = limit
        
        self.log.debug('Placing %s order for %i %s (id=%i)' % (o.m_action,o.m_totalQuantity,symbol,o.m_orderId))
        
            
        self.tws.placeOrder(o.m_orderId,self.contracts[symbol],o)   
            
            
            
    def getOrderId(self):
        self.nextValidOrderId+=1
        return self.nextValidOrderId-1        
    
    def unsubscribeStk(self,symbol):
        self.log.debug('Function not implemented')
    
    def disconnect(self):
        self.tws.disconnect()
       
    def __del__(self):
        '''destructor, clean up '''
        print 'Broker is cleaning up after itself.'
        self.tws.disconnect()
    
    def debugHandler(self,msg):
        print msg

    def defaultHandler(self,msg):
        ''' default message handler '''
        #print msg.typeName
        if msg.typeName == 'Error':
            self.log.error(msg)
       

    def nextValidIdHandler(self,msg):
        self.nextValidOrderId = msg.orderId
        self.log.debug( 'Next valid order id:{0}'.format(self.nextValidOrderId))
    
    def saveData(self, fname):
        ''' save current dataframe to csv '''
        self.log.debug("Saving data to {0}".format(fname))
        self.dataModel.df.to_csv(fname)

#    def __getattr__(self, name):
#        """ x.__getattr__('name') <==> x.name
#        an easy way to call ibConnection methods
#        @return named attribute from instance tws
#        """
#        return getattr(self.tws, name)



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
    
        
class Downloader(object):
    def __init__(self,debug=False):
        self._log = logger.getLogger('DLD')        
        self._log.debug('Initializing data dwonloader. Pandas version={0}, ibpy version:{1}'.format(pandas.__version__,ib.version))

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
        
    
    def requestData(self,contract,endDateTime,durationStr='1800 S',barSizeSetting='1 secs',whatToShow='TRADES',useRTH=1,formatDate=1):  
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


class TimeKeeper(object):
    def __init__(self):
        self._log = logger.getLogger('TK') 
        dataDir = os.path.expanduser('~')+'/twpData'
        
        if not os.path.exists(dataDir):
            os.mkdir(dataDir)

        self._timeFormat = "%Y%m%d %H:%M:%S"
        self.dataFile = os.path.normpath(os.path.join(dataDir,'requests.txt'))
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



#---------------test functions-----------------

def dummyHandler(msg):
    print msg

def testConnection():
    ''' a simple test to check working of streaming prices etc '''
    tws = ibConnection()
    tws.registerAll(dummyHandler)

    tws.connect()
    
    c = createContract('SPY')
    tws.reqMktData(1,c,'',False)
    sleep(3)
    
    print 'testConnection done.'



def testSubscriptions():
    s = Subscriptions()
    s.add('SPY')
    #s.add('XLE')
    
    print s

def testBroker():
    b = Broker()
    sleep(2)
    b.subscribeStk('SPY')
    b.subscribeStk('XLE')
    b.subscribeStk('GOOG')
    
    b.placeOrder('ABC', 125, 55.1)
    sleep(3)
    return b
        
#---------------------GUI stuff--------------------------------------------
class AddSubscriptionDlg(QDialog):
    def __init__(self,parent=None):
        super(AddSubscriptionDlg,self).__init__(parent)
        symbolLabel = QLabel('Symbol')
        self.symbolEdit = QLineEdit()
        secTypeLabel = QLabel('secType')
        self.secTypeEdit = QLineEdit('STK')
        exchangeLabel = QLabel('exchange')
        self.exchangeEdit = QLineEdit('SMART')
        currencyLabel = QLabel('currency')
        self.currencyEdit = QLineEdit('USD')
        
        buttonBox = QDialogButtonBox(QDialogButtonBox.Ok|
                                     QDialogButtonBox.Cancel)
        
        lay = QGridLayout()
        lay.addWidget(symbolLabel,0,0)
        lay.addWidget(self.symbolEdit,0,1)
        lay.addWidget(secTypeLabel,1,0)
        lay.addWidget(self.secTypeEdit,1,1)
        lay.addWidget(exchangeLabel,2,0)
        lay.addWidget(self.exchangeEdit,2,1)
        lay.addWidget(currencyLabel,3,0)
        lay.addWidget(self.currencyEdit,3,1)
        
        lay.addWidget(buttonBox,4,0,1,2)
        self.setLayout(lay)

        self.connect(buttonBox, SIGNAL("accepted()"),
                     self, SLOT("accept()"))
        self.connect(buttonBox, SIGNAL("rejected()"),
                     self, SLOT("reject()"))
        self.setWindowTitle("Add subscription")

class BrokerWidget(QWidget):
    def __init__(self,broker,parent = None ):
        super(BrokerWidget,self).__init__(parent)
        
        self.broker = broker
        
        self.dataTable = TableView()
        self.dataTable.setModel(self.broker.dataModel)
        self.dataTable.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        #self.dataTable.resizeColumnsToContents()
        dataLabel = QLabel('Price Data')
        dataLabel.setBuddy(self.dataTable)
        
        dataLayout = QVBoxLayout()
        
        dataLayout.addWidget(dataLabel)
        dataLayout.addWidget(self.dataTable)
        
        
        addButton = QPushButton("&Add Symbol")
        saveDataButton = QPushButton("&Save Data")
        #deleteButton = QPushButton("&Delete")
        
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(saveDataButton)
        buttonLayout.addStretch()
        
        layout = QHBoxLayout()
        layout.addLayout(dataLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        
        self.connect(addButton,SIGNAL('clicked()'),self.addSubscription)
        self.connect(saveDataButton,SIGNAL('clicked()'),self.saveData)
        #self.connect(deleteButton,SIGNAL('clicked()'),self.deleteSubscription)
        
    def addSubscription(self):
        dialog = AddSubscriptionDlg(self)
        if dialog.exec_():
            self.broker.subscribeStk(str(dialog.symbolEdit.text()),str( dialog.secTypeEdit.text()),
                                     str(dialog.exchangeEdit.text()),str(dialog.currencyEdit.text()))
    
    def saveData(self):
        ''' save data to a .csv file '''
        fname =unicode(QFileDialog.getSaveFileName( self, caption="Save data to csv",filter = '*.csv'))
        if fname:
            self.broker.saveData(fname)
        
        
#    def deleteSubscription(self):
#        pass


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.resize(640,480)
        self.setWindowTitle('Broker test')
        
        self.broker = Broker()
       
        self.broker.subscribeStk('SPY')
        self.broker.subscribeStk('XLE')
        self.broker.subscribeStk('GOOG')
        
        brokerWidget = BrokerWidget(self.broker,self)
        lay = QVBoxLayout()
        lay.addWidget(brokerWidget)
        self.setLayout(lay)

def startGui():
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()

if __name__ == "__main__":
    import ib
    print 'iby version:' , ib.version 
    testConnection()
    #testBroker()
    #testSubscriptions()
    print message.messageTypeNames()
    #startGui()
    print 'All done'
    
    