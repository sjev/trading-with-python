'''
Created on 4 aug. 2012
Copyright: Jev Kuznetsov
License: BSD

a module for downloading historic data from IB

'''
import ib
import pandas
from ib.ext.Contract import Contract
from ib.opt import ibConnection, message
from time import sleep
import tradingWithPython.lib.logger as logger


class Downloader(object):
    def __init__(self):
     self.log = logger.getLogger('DLD')        
     self.log.debug('Initializing data dwonloader. Pandas version={0}, ibpy version:{1}'.format(pandas.__version__,ib.version))
     

if __name__=='__main__':
    dl = Downloader()
    
    