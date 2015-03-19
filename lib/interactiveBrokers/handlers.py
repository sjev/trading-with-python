# -*- coding: utf-8 -*-
"""
Common handlers for ibpy

Created on Thu Mar 19 22:34:20 2015

@author: Jev Kuznetsov
License: BSD

"""
import pandas as pd


class Logger(object):
    """ class for logging and displaying icoming messages """
    def __init__(self,tws):
        tws.registerAll(self.handler)

    def handler(self,msg):
        print msg
    
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
        self.data().to_csv(fName,header = True, mode='wb')
        
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