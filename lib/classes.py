"""
worker classes

@author: Jev Kuznetsov
Licence: GPL v2
"""

import os
import twp.lib.logger as logger



class Symbol:
    ''' Symbol class, the foundation of Trading With Python library,
    This class acts as an interface to Yahoo data, Interactive Brokers etc '''
    def __init__(self,symbol):
        self.symbol = symbol
        self.log = logger.getLogger(self.symbol)
        self.log.debug('class created.')
        
        self.dataDir = os.getenv("USERPROFILE")+'\\twpData\\symbols\\'+self.symbol
        self.log.debug('Data dir:'+self.dataDir)        
        
        
        
if __name__=='__main__':
    spy = Symbol('SPY')
    iwm = Symbol('IWM')
