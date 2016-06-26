'''
Created on May 8, 2013
Copyright: Jev Kuznetsov
License: BSD

convenience functions for interactiveBrokers module

'''
from ib.ext.Contract import Contract
from ib.ext.Order import Order

priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 
timeFormat = "%Y%m%d %H:%M:%S"
dateFormat = "%Y%m%d"


def createContract(symbol,secType='STK',exchange='SMART',currency='USD'):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= secType
    c.m_exchange = exchange
    c.m_currency = currency
    
    return c

def createOrder(orderId,shares,orderType='MKT', limit = None, transmit=0):
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
    o.m_orderType = orderType
    
    if limit is not None:
        o.m_lmtPrice = limit
    
    return o    