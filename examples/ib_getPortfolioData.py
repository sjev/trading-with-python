#Get Available Funds
from time import sleep
from ib.opt import ibConnection
from tradingWithPython.lib.interactiveBrokers.handlers import Account, Portfolio
 

#--------------main script------------------
tws = ibConnection() # create connection object
tws.enableLogging()

# create handler classes. Each will subscribe to the relevant events
# account updates will be handled by Account class (acct)  and portfolio updates byt the Portfolio class (port) 
port = Portfolio(tws)
acct = Account(tws)
#log = Logger(tws)

tws.connect() # connect to API
#sleep(3) # wait for connection to come up
tws.reqAccountUpdates(True, '') # request account & portfolio updates. Parameters (subscibe,acctCode)

#-------wait for data, stop after timeout
print('Waiting for data')

timeout = 10 # timout in seconds
t= 0 # time counter
while (not acct.dataReady) & (t < timeout):
    print('.', end=' ')
    sleep(1)
    t+=1
  
assert t<timeout, 'Timeout occured while waiting for data'  
  
acct.to_csv('accountData.csv')  
port.to_csv('portfolio.csv')            
            
print('done')
   
tws.disconnect()
