#Get Available Funds
from time import sleep
from ib.opt import ibConnection
from tradingWithPython_dev.lib.interactiveBrokers.handlers import Orders
from tradingWithPython.lib.interactiveBrokers.extra import createContract


#--------------main script------------------
tws = ibConnection() # create connection object
tws.enableLogging()

# create handler classes. Each will subscribe to the relevant events
orders = Orders(tws)

tws.connect() # connect to API
sleep(2)

#tws.reqOpenOrders()
tws.reqAllOpenOrders()

# ----place an order
#contract = createContract('XLE')
#orders.placeOrder(contract,50,limit=10)


#-------wait for data
sleep(1)
print 40*'-'            
print orders.data()
print 'done'
 
tws.disconnect()
