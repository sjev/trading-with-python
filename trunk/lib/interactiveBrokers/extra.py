'''
Created on May 8, 2013
Copyright: Jev Kuznetsov
License: BSD

convenience functions for interactiveBrokers module

'''
from ib.ext.Contract import Contract

def createContract(symbol):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= "STK"
    c.m_exchange = "SMART"
    c.m_currency = "USD"
    
    return c