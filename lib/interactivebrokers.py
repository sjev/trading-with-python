'''
Copyright 2011  Jev Kuznetsov
Distributed under the terms of the GNU General Public License v2

Interface to interactive brokers together with gui widgets

'''
#import sys
#import os
from time import sleep
#from PyQt4.QtCore import (QAbstractTableModel,Qt,QVariant,QModelIndex, SIGNAL,SLOT,QString)
#from PyQt4.QtGui import (QApplication,QMessageBox,QDialog,QVBoxLayout,QHBoxLayout,QDialogButtonBox,
#                         QTableView, QPushButton,QWidget,QLabel,QLineEdit,QGridLayout)

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

class Subscriptions(object):
    ''' a data table containing price & subscription data '''
    def __init__(self):
        
        self.data = DataFrame() # this property holds the data in a table format
        self._nextId = 1
        self._id2symbol = {} # id-> symbol lookup dict
        
    def add(self,symbol, subId = None):
        ''' 
        Add subscription to data table 
        
        Parameters
        ------------
        symbol    :    stock symbol, 'SPY' for example
        subId    :    (optional) force subscription id 
        
        Returns
        -----------
        id :        subscription id to be used with data request from IB
        
        '''
        if subId is None:
            subId = self._nextId
        
        header = ['id','bid','ask','last']
        data = dict(zip(header,[subId,np.nan,np.nan,np.nan]))
        row = DataFrame(data, index = Index([symbol]))
 
        self.data = self.data.append(row[header])
        
        self._nextId = subId+1        
        self._rebuildIndex()
        return subId
    
    def priceHandler(self,msg):
        ''' handler function for price updates. register this with ibConnection class '''
        try:
            self.data[priceTicks[msg.field]][self._id2symbol[msg.tickerId]]=msg.price
        except KeyError:
            return
            
        print self
        
        
        
    
    def _rebuildIndex(self):
        ''' udate lookup dictionary id-> symbol '''
        symbols = self.data.index.tolist()
        ids = self.data['id'].values.tolist()
        self._id2symbol = dict(zip(ids,symbols))
        
    
    def __repr__(self):
        return str(self.data)
    


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
                
        
        
        self.tws.registerAll(self.defaultHandler) 
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
        
        id = self.data.add(symbol)
        
        self.tws.reqMktData(id,c,'',False)
        
        return id
    
    def unsubscribeStk(self,symbol):
        id = self.data.symbol2id[symbol]
        print 'Unsubscribing {0}({1})'.format(symbol,id)
        sleep(0.5)
        self.tws.cancelMktData(id)
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
    s.add('AAA')
    s.add('BBB')
    print s

def testBroker():
    b = Broker()
    b.subscribeStk('SPY')
    sleep(3)
    return b
        


if __name__ == "__main__":
    
    #testConnection()
    testBroker()
    
    #testSubscriptions()

    print 'All done'
    
    