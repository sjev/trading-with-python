'''
Created on 26 dec. 2011
Copyright: Jev Kuznetsov
License: BSD
'''

from time import sleep

from ib.ext.Contract import Contract
from ib.opt import ibConnection
from ib.ext.Order import Order

import tradingWithPython.lib.logger as logger
from tradingWithPython.lib.qtpandas import DataFrameModel, TableView
from tradingWithPython.lib.eventSystem import Sender, ExampleListener
import numpy as np

import pandas
from wx.tools.Editra.src.ed_vim import Ex

priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 


class Broker(Sender):
    def __init__(self, name = "broker"):
        super(Broker,self).__init__()
        
        self.name = name
        self.log = logger.getLogger(self.name)        
        
        self.log.debug('Initializing broker. Pandas version={0}'.format(pandas.__version__))
        self.contracts = {} # a dict to keep track of subscribed contracts
        self._id2symbol = {} # id-> symbol dict
        self.tws = None
        self._nextId = 1 # tws subscription id
        self.nextValidOrderId = None
                
        
        
    def connect(self):
        """ connect to tws """
        self.tws =  ibConnection() # tws interface
        self.tws.registerAll(self._defaultHandler) 
        self.tws.register(self._nextValidIdHandler,'NextValidId')
        self.log.debug('Connecting to tws')
        self.tws.connect()  
        
        self.tws.reqAccountUpdates(True,'')
        self.tws.register(self._priceHandler,'TickPrice')
    
    def subscribeStk(self,symbol, secType='STK', exchange='SMART',currency='USD'):
        '''  subscribe to stock data '''
        self.log.debug('Subscribing to '+symbol)             
        c = Contract()
        c.m_symbol = symbol
        c.m_secType = secType
        c.m_exchange = exchange
        c.m_currency = currency
        
        subId = self._nextId
        self._nextId += 1
        
        self.tws.reqMktData(subId,c,'',False)
        self._id2symbol[subId] = c.m_symbol
        self.contracts[symbol]=c
        
    
    def disconnect(self):
        self.tws.disconnect()
    #------event handlers--------------------    

    def _defaultHandler(self,msg):
        ''' default message handler '''
        #print msg.typeName
        if msg.typeName == 'Error':
            self.log.error(msg)
        

    def _nextValidIdHandler(self,msg):
        self.nextValidOrderId = msg.orderId
        self.log.debug( 'Next valid order id:{0}'.format(self.nextValidOrderId))

    def _priceHandler(self,msg):
        print msg
        #translate to meaningful messages
        message = {'symbol':self._id2symbol[msg.tickerId],
                   'price':msg.price,
                   'type':priceTicks[msg.field]}
        self.dispatch('price',message)
        

if __name__=="__main__":
    print "Running nautilus"
    
    broker = Broker()
    l = ExampleListener('listener')
    broker.register(l.method, 'price')
    
    broker.connect()
    broker.subscribeStk('SPY')
    
    sleep(3)
    broker.disconnect()
    print "All done."