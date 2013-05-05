'''
Created on May 5, 2013
Copyright: Jev Kuznetsov
License: BSD

Demonstration of how to stream quotes from IB

'''

from time import sleep
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message



def debug_tick_handler(msg):
    """ tick handler that prints out all data """
    print '[DBG]:', msg

def price_tick_handler(msg):
    """ handle price ticks """
    priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 
    
    print priceTicks[msg.field], '=' , msg.price

#--------------main script------------------

tws = ibConnection()
#tws.registerAll(debug_tick_handler)
tws.register(price_tick_handler, message.TickPrice)
tws.connect()

#-------create contract and subscribe to data
c = Contract()
c.m_symbol = "SPY"
c.m_secType= "STK"
c.m_exchange = "SMART"
c.m_currency = "USD"

tws.reqMktData(1,c,"",False)

#-------start endless loop
print 'Press Ctr-C to stop loop'
try:
    while True:
        sleep(1)
            
except KeyboardInterrupt:
    print 'All done'
            
tws.disconnect()