# -*- coding: utf-8 -*-
"""
  
Copyright: Jev Kuznetsov
License: BSD
  
Demonstration of how to stream quotes from IB.
This script will subscribe to SPY and stream quotes to the sreen for 10 seconds.
  
"""

from time import sleep
from ib.ext.Contract import Contract
from ib.opt import ibConnection


def price_tick_handler(msg):
    """function to handle price ticks"""
    print(msg)


# --------------main script------------------
import ib

print(("ibpy version:", ib.__version__))
tws = ibConnection()  # create connection object
tws.enableLogging()  # show debugging output from ibpy
tws.register(price_tick_handler, "tickPrice")  # register handler
tws.connect()  # connect to API

# -------create contract and subscribe to data
c = Contract()
c.m_symbol = "SPY"
c.m_secType = "STK"
c.m_exchange = "SMART"
c.m_currency = "USD"

tws.reqMktData(1, c, "", False)  # request market data

# -------print data for a couple of seconds, then close
sleep(10)

print("All done")

tws.disconnect()
