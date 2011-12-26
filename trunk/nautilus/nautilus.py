'''
Created on 26 dec. 2011
Copyright: Jev Kuznetsov
License: BSD
'''



from PyQt4.QtCore import *
from PyQt4.QtGui import *

from ib.ext.Contract import Contract
from ib.opt import ibConnection
from ib.ext.Order import Order

import tradingWithPython.lib.logger as logger
from tradingWithPython.lib.eventSystem import Sender, ExampleListener
import tradingWithPython.lib.qtpandas as qtpandas
import numpy as np

import pandas


priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 


class PriceListener(qtpandas.DataFrameModel):
    def __init__(self):
        super(PriceListener,self).__init__()
        self._header = ['position','bid','ask','last']
        
    def addSymbol(self,symbol):
        data = dict(zip(self._header,[0,np.nan,np.nan,np.nan]))
        row = pandas.DataFrame(data, index = pandas.Index([symbol]))
        self.df = self.df.append(row[self._header]) # append data and set correct column order
    
        
    def priceHandler(self,sender,event,msg=None):
       
        if msg['symbol'] not in self.df.index:
            self.addSymbol(msg['symbol'])
        
        if msg['type'] in self._header:
            self.df.ix[msg['symbol'],msg['type']] = msg['price']
            self.signalUpdate()
            #print self.df
    


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
        #translate to meaningful messages
        message = {'symbol':self._id2symbol[msg.tickerId],
                   'price':msg.price,
                   'type':priceTicks[msg.field]}
        self.dispatch('price',message)


#-----------------GUI elements-------------------------

class TableView(QTableView):
    """ extended table view """
    def __init__(self,name='TableView1', parent=None):
        super(TableView,self).__init__(parent)
        self.name = name
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        
    def contextMenuEvent(self, event):
        menu = QMenu(self)

        Action = menu.addAction("print selected rows")
        Action.triggered.connect(self.printName)

        menu.exec_(event.globalPos())

    def printName(self):
        print "Action triggered from " + self.name
        
        print 'Selected :'
        for idx in self.selectionModel().selectedRows():
            print self.model().df.ix[idx.row(),:]



class Form(QDialog):
    def __init__(self,parent=None):
        super(Form,self).__init__(parent)
        
        self.broker = Broker()
        self.price = PriceListener()
        
        self.broker.connect()
        
        symbols = ['SPY','XLE','QQQ','VXX','XIV']
        for symbol in symbols:
            self.broker.subscribeStk(symbol)
        
        self.broker.register(self.price.priceHandler, 'price')
        
        
        widget = TableView(parent=self)
        widget.setModel(self.price)
        widget.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        
        layout = QVBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)

    def __del__(self):
        print 'Disconnecting.'
        self.broker.disconnect() 

if __name__=="__main__":
    print "Running nautilus"
    
    import sys
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()
    print "All done."