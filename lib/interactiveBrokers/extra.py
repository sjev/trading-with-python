'''
Created on May 8, 2013
Copyright: Jev Kuznetsov
License: BSD

convenience functions for interactiveBrokers module

'''
from ib.ext.Contract import Contract


priceTicks = {1:'bid',2:'ask',4:'last',6:'high',7:'low',9:'close', 14:'open'} 
timeFormat = "%Y%m%d %H:%M:%S"
dateFormat = "%Y%m%d"


def createContract(symbol):
    ''' create contract object '''
    c = Contract()
    c.m_symbol = symbol
    c.m_secType= "STK"
    c.m_exchange = "SMART"
    c.m_currency = "USD"
    
    return c