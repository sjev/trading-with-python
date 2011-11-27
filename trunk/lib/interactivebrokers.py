'''
Copyright 2011  Jev Kuznetsov
Distributed under the terms of the GNU General Public License v2

Interface to interactive brokers together with gui widgets

'''
import sys
#import os
from time import sleep
from PyQt4.QtCore import (QAbstractTableModel,Qt,QVariant,QModelIndex, SIGNAL,SLOT,QString)
from PyQt4.QtGui import (QApplication,QMessageBox,QDialog,QVBoxLayout,QHBoxLayout,QDialogButtonBox,
                         QTableView, QPushButton,QWidget,QLabel,QLineEdit,QGridLayout)

from ib.ext.Contract import Contract
from ib.opt import ibConnection, message

import tradingWithPython.lib.logger as logger
import numpy as np

from pandas import DataFrame, Index

priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 

def createContract(symbol, secType='STK', exchange='SMART',currency='USD'):
    ''' contract factory function '''
    contract = Contract()
    contract.m_symbol = symbol
    contract.m_secType = secType
    contract.m_exchange = exchange
    contract.m_currency = currency
    
    return contract

class Subscriptions(QAbstractTableModel):
    ''' a data table containing price & subscription data '''
    def __init__(self):
        
        super(Subscriptions,self).__init__()
        self._data = DataFrame() # this property holds the data in a table format
      
        self._nextId = 1
        self._id2symbol = {} # id-> symbol lookup dict
        self._header = ['id','bid','ask','last'] # columns of the _data table
        
        
    def add(self,symbol, subId = None):
        ''' 
        Add  a subscription to data table
        return : subscription id 
        
        '''
        if subId is None:
            subId = self._nextId
        
        data = dict(zip(self._header,[subId,np.nan,np.nan,np.nan]))
        row = DataFrame(data, index = Index([symbol]))
 
        self._data = self._data.append(row[self._header]) # append data and set correct column order
        
        self._nextId = subId+1        
        self._rebuildIndex()
        
        self.emit(SIGNAL("layoutChanged()"))
         
        return subId
    
    def priceHandler(self,msg):
        ''' handler function for price updates. register this with ibConnection class '''
        
        if priceTicks[msg.field] not in self._header: # do nothing for ticks that are not in _data table
            return
        
        self._data[priceTicks[msg.field]][self._id2symbol[msg.tickerId]]=msg.price
        
        #notify viewer
        col = self._header.index(priceTicks[msg.field])
        row = self._data.index.tolist().index(self._id2symbol[msg.tickerId])
        
        idx = self.createIndex(row,col)
        self.emit(SIGNAL("dataChanged(QModelIndex,QModelIndex)"),idx, idx)
       
    
    def _rebuildIndex(self):
        ''' udate lookup dictionary id-> symbol '''
        symbols = self._data.index.tolist()
        ids = self._data['id'].values.tolist()
        self._id2symbol = dict(zip(ids,symbols))
        
    
    def __repr__(self):
        return str(self._data)
    
    #------------- table display functions -----------------     
    def headerData(self,section,orientation,role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        
        
        if orientation == Qt.Horizontal:
            
            try:
                return (self._header)[section]
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                #return self._data.index.tolist()
                return self._data.index.tolist()[section]
            except (IndexError, ):
                return QVariant()
            
    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        
        if (not index.isValid() or not (0 <= index.row() < len(self._data))):
            return QVariant()
        
        return QVariant(str(self._data.ix[index.row(),index.column()]))
      
    def rowCount(self, index=QModelIndex()):
        return self._data.shape[0]
    
    def columnCount(self, index=QModelIndex()):
        return self._data.shape[1]
    

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
        
        self.data = Subscriptions() # data container
        self.tws =  ibConnection() # tws interface
        self.nextValidOrderId = None
                
        
        
        #self.tws.registerAll(self.defaultHandler) 
        self.tws.register(self.data.priceHandler,message.TickPrice)
        self.tws.register(self.nextValidIdHandler,message.NextValidId)
        self.log.debug('Connecting to tws')
        self.tws.connect()  
        
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
        
        subId = self.data.add(symbol)
        
        self.tws.reqMktData(subId,c,'',False)
        
        return subId
    
    def unsubscribeStk(self,symbol):
        subId = self.data.symbol2id[symbol]
        print 'Unsubscribing {0}({1})'.format(symbol,subId)
        sleep(0.5)
        self.tws.cancelMktData(subId)
        self.data.removeSubscription(symbol)
    
    def getContract(self,symbol):
        return self.data.getContract(symbol)
    
    def symbolId(self,symbol):
        ''' reverse symbol lookup
        @param symbol: contract symbol
        @return: symbol id
        '''
        return self.data.symbol2id[symbol]
   
    
    def __getattr__(self, name):
        """ x.__getattr__('name') <==> x.name
        an easy way to call ibConnection methods
        @return named attribute from instance tws
        """
        return getattr(self.tws, name)
       
    def __del__(self):
        '''destructor, clean up '''
        print 'Broker is cleaning up after itself.'
        self.tws.disconnect()

    def defaultHandler(self,msg):
        ''' default message handler '''
        self.log.debug(msg)
        

    def nextValidIdHandler(self,msg):
        self.nextValidOrderId = msg.orderId
        self.log.debug( 'Next valid order id:{0}'.format(self.nextValidOrderId))

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
    b.subscribeStk('SPY')
    b.subscribeStk('XLE')
    b.subscribeStk('QQQ')
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
        super(BrokerWidget,self).__init__()
        
        self.broker = broker
        
        self.dataTable = QTableView()
        self.dataTable.setModel(self.broker.data)
        dataLabel = QLabel('Price Data')
        dataLabel.setBuddy(self.dataTable)
        
        dataLayout = QVBoxLayout()
        
        dataLayout.addWidget(dataLabel)
        dataLayout.addWidget(self.dataTable)
        
        
        addButton = QPushButton("&Add")
        deleteButton = QPushButton("&Delete")
        
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(addButton)
        #buttonLayout.addWidget(deleteButton)
        buttonLayout.addStretch()
        
        layout = QHBoxLayout()
        layout.addLayout(dataLayout)
        layout.addLayout(buttonLayout)
        self.setLayout(layout)
        
        self.connect(addButton,SIGNAL('clicked()'),self.addSubscription)
        self.connect(deleteButton,SIGNAL('clicked()'),self.deleteSubscription)
        
    def addSubscription(self):
        dialog = AddSubscriptionDlg(self)
        if dialog.exec_():
            self.broker.subscribeStk(str(dialog.symbolEdit.text()),str( dialog.secTypeEdit.text()),
                                     str(dialog.exchangeEdit.text()),str(dialog.currencyEdit.text()))
        
    def deleteSubscription(self):
        pass


class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.resize(640,480)
        self.setWindowTitle('Broker test')
        
        self.broker = Broker()
       
        self.broker.subscribeStk('SPY')
        self.broker.subscribeStk('XLE')
        self.broker.subscribeStk('QQQ')
        
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
    
    #testConnection()
    #testBroker()
    #testSubscriptions()
    
    startGui()
    print 'All done'
    
    