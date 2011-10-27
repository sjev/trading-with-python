#! /usr/bin/env python
# -*- coding: utf-8 -*-

from ib.ext.Contract import Contract
from ib.ext.ExecutionFilter import ExecutionFilter
from ib.opt import ibConnection, message
from time import sleep

# print all messages from TWS
def watcher(msg):
    print msg

def dummyHandler(msg):
    pass

# show Bid and Ask quotes
def my_BidAsk(msg):
    print 'bid_ask'
    print msg
    
    if msg.field == 1:
        print '%s: bid: %s' % (contractTuple[0],
                        msg.price)
    elif msg.field == 2:
        print '%s: ask: %s' % (contractTuple[0],  msg.price)
        
def my_BidAsk2(msg):
    print 'Handler 2'
    print msg
   
    
def portfolioHandler(msg):
    print msg
    print msg.contract.m_symbol

def makeStkContract(contractTuple):
    newContract = Contract()
    newContract.m_symbol = contractTuple[0]
    newContract.m_secType = contractTuple[1]
    newContract.m_exchange = contractTuple[2]
    newContract.m_currency = contractTuple[3]
   
    print 'Contract Values:%s,%s,%s,%s:' % contractTuple
    return newContract

def testMarketData():
    tickId = 1

    # Note: Option quotes will give an error if they aren't shown in TWS
    contractTuple = ('SPY', 'STK', 'SMART', 'USD')
  
    stkContract = makeStkContract(contractTuple)
    print '* * * * REQUESTING MARKET DATA * * * *'
    con.reqMktData(tickId, stkContract, '', False)
    sleep(3)
    print '* * * * CANCELING MARKET DATA * * * *'
    con.cancelMktData(tickId)

def testExecutions():
    print 'testing executions'
    f = ExecutionFilter()
    #f.m_clientId = 101
    f.m_time = '20110901-00:00:00'
    f.m_symbol = 'SPY'
    f.m_secType = 'STK'
    f.m_exchange = 'SMART'
    #f.m_side = 'BUY'
    
    con.reqExecutions(f)
   
    
    sleep(2)

def testAccountUpdates():
    con.reqAccountUpdates(True,'')

if __name__ == '__main__':
    
    
    con = ibConnection()
    con.registerAll(dummyHandler)
    con.register(portfolioHandler,message.UpdatePortfolio)
   
    con.connect()
    
    
    
    sleep(1)
    #testMarketData()
    #testExecutions()
    testAccountUpdates()
 
    con.disconnect()
    sleep(2)
    print 'All done!'
