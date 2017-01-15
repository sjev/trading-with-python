# -*- coding: utf-8 -*-
"""
Common handlers for ibpy

Created on Thu Mar 19 22:34:20 2015

@author: Jev Kuznetsov
License: BSD

"""
import pandas as pd
from ib.ext.Order import Order


class Logger(object):
    """ class for logging and displaying icoming messages """
    def __init__(self,tws):
        tws.registerAll(self.handler)

    def handler(self,msg):
        print(msg)
    
class Account(object):
    """ class for holding account data """
    def __init__(self,tws):
        self.tws = tws
        
        self.tws.register(self._handler, 'UpdateAccountValue')
        self.tws.register(self._timeHandler,'UpdateAccountTime')
        
        self.lastUpdate = None # timestamp of the last update
        self._data = {} # internal data structure, {key: (value,currency)}
        self.dataReady = False # for checking if data has been received
        
        
    def _handler(self,msg):
        """ handles all incoming values """
        self._data[msg.key] = (msg.value, msg.currency)
        
    def _timeHandler(self,msg):
        """ triggered when a new update comes in """
        self.lastUpdate = msg.timeStamp
        self.dataReady = True
            
        
        
    def data(self):
        """ return account data as a pandas DataFrame """
        df = pd.DataFrame(self._data).T
        df.columns = ['value','currency']
        
        return df
        
    def to_csv(self,fName):
        """ save data to csv """
        assert self.dataReady , "No data received yet "
        self.data().to_csv(fName)
        
class Portfolio(object):
    """ class for keeping track of portfolio data """
    def __init__(self,tws):
        self.tws = tws
        
        self.tws.register(self._handler, 'UpdatePortfolio')
        self._data = {} # internal data dictionary
        
        self._header = ('symbol','position','marketPrice','marketValue','averageCost')
    
    def _handler(self,msg):
        
        conId = msg.contract.m_conId # unique contract identifier
        self._data[conId] = [msg.contract.m_symbol] # init with symbol
        for h in self._header[1:]: # set the rest
            self._data[conId].append(getattr(msg,h))
            
        
    def data(self):
        """ return internal data as a pandas DataFrame """
        
        df = pd.DataFrame(self._data).T # convert from dictionary to a  DataFrame, transpose
        df.columns = self._header        
        
        return df
        
    def to_csv(self,fName):
        self.data().to_csv(fName)
        
        
class Orders(object):
    """ class for working with orders """
    def __init__(self,tws):
        self.tws = tws
        
        # init variables
        self._data = {} # internal orders dictionary orderIds are dict keys
        self.nextValidOrderId = None
        self.endReceived = False # will be set on OpenOrderEnd event
        
        # register handlers
        self.tws.register(self._h_orderStauts, 'OrderStatus')
        self.tws.register(self._h_nextValidId, 'NextValidId')
        self.tws.register(self._h_openOrder, 'OpenOrder')
        self.tws.register(self._h_openOrderEnd, 'OpenOrderEnd')
        
    
    #----------order placement
    def placeOrder(self,contract, shares,limit = None, transmit=0):
        ''' 
        create order object 
     
        Parameters
        -----------
        
        shares: number of shares to buy or sell. Negative for sell order.  
        limit : price limit, None for MKT order
        transmit: transmit immideatelly from tws
        
        Returns: 
        -----------
        orderId : The order Id. You must specify a unique value. 
                  When the order status returns, it will be identified by this tag. 
                  This tag is also used when canceling the order.
     
        
        '''
     
        action = {-1:'SELL',1:'BUY'}  
        
        
        orderId = self.nextValidOrderId
        self.nextValidOrderId += 1 # increment  
        
        o = Order()
        o.m_orderId = orderId
        o.m_action = action[cmp(shares,0)]
        o.m_totalQuantity = abs(shares)
        o.m_transmit = transmit
     
        if limit is not None:
            o.m_orderType = 'LMT'
            o.m_lmtPrice = limit
        else:
            o.m_orderType = 'MKT'
     
        # place order
        self.tws.placeOrder(orderId, contract, o) # place order     
     
     
        return orderId
    
    # ----------data retrieval
    def data(self):
        """ get open order data as a pandas DataFrame """
        df = pd.DataFrame(self._data).T
        cols = ['symbol','orderId','filled','remaining','lastFillPrice','avgFillPrice']        
        
        return df[cols]

    #-----------handlers    
    def _h_orderStauts(self,msg):
        """ status handler """
        for k,v in list(msg.items()):
            self._data[msg.orderId][k] =  v
    
    def _h_openOrder(self,msg):
        """ openOrder message handler """
        self._data[msg.orderId] = {'symbol': msg.contract.m_symbol}
        
    def _h_nextValidId(self,msg):
        """ next valid id handler """
        self.nextValidOrderId = msg.orderId        
        
    def _h_openOrderEnd(self,msg):
        """ called at the end of sending orders """
        self.endReceived = True
        
    