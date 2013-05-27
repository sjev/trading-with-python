# -*- coding: utf-8 -*-
"""
Demonstrate order submission with ibpy
"""

from time import sleep

from ib.ext.Contract import Contract
from ib.opt import ibConnection
from ib.ext.Order import Order

def createContract(symbol):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= "STK"
    c.m_exchange = "SMART"
    c.m_currency = "USD"
    
    return c
    
def createOrder(orderId,shares,limit = None, transmit=0):
    ''' 
    create order object 
    
    Parameters
    -----------
    orderId : The order Id. You must specify a unique value. 
              When the order status returns, it will be identified by this tag. 
              This tag is also used when canceling the order.

    shares: number of shares to buy or sell. Negative for sell order.  
    limit : price limit, None for MKT order
    transmit: transmit immideatelly from tws
    '''

    action = {-1:'SELL',1:'BUY'}    
    
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
    
    return o    

class MessageHandler(object):
    ''' class for handling incoming messages '''
    
    def __init__(self,tws):
        ''' create class, provide ibConnection object as parameter '''
        self.nextValidOrderId = None
        
        tws.registerAll(self.debugHandler)
        tws.register(self.nextValidIdHandler,'NextValidId')
        
        
    def nextValidIdHandler(self,msg):
        ''' handles NextValidId messages '''
        self.nextValidOrderId = msg.orderId

    def debugHandler(self,msg):
        """ function to print messages """
        print msg
        
        

#-----------Main script-----------------

tws = ibConnection() # create connection object
handler = MessageHandler(tws) # message handling class

tws.connect() # connect to API

sleep(1) # wait for nextOrderId to come in

orderId = handler.nextValidOrderId # numeric order id, must be unique.
print 'Placing order with id ', orderId

contract = createContract('SPY')
order = createOrder(orderId,shares=5, transmit=0) # create order


tws.placeOrder(orderId, contract, order) # place order

sleep(5)

print 'Cancelling order '
tws.cancelOrder(orderId) # cancel it.

print 'All done'
            
tws.disconnect()