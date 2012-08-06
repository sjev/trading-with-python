# -*- coding: utf-8 -*-
"""
used to check timing constraints 

@author: jev
"""


import os
import datetime as dt
import tradingWithPython.lib.logger as logger

class TimeKeeper(object):
    def __init__(self):
        self._log = logger.getLogger('TK') 
        dataDir = os.path.expanduser('~')+'/twpData'
        
        if not os.path.exists(dataDir):
            os.mkdir(dataDir)

        self._timeFormat = "%Y%m%d %H:%M:%S"
        self.dataFile = os.path.normpath(os.path.join(dataDir,'requests.txt'))
        self._log.debug('Data file: {0}'.format(self.dataFile))
        
    def addRequest(self):
        ''' adds a timestamp of current request'''
        with open(self.dataFile,'a') as f:
            f.write(dt.datetime.now().strftime(self._timeFormat)+'\n')
            

    def nrRequests(self,timeSpan=600):
        ''' return number of requests in past timespan (s) '''
        delta = dt.timedelta(seconds=timeSpan)
        now = dt.datetime.now()
        requests = 0
        
        with open(self.dataFile,'r') as f:
            lines = f.readlines()
            
        for line in lines:
            if now-dt.datetime.strptime(line.strip(),self._timeFormat) < delta:
                requests+=1
    
        if requests==0: # erase all contents if no requests are relevant
            open(self.dataFile,'w').close() 
            
        self._log.debug('past requests: {0}'.format(requests))
        return requests

if __name__=='__main__':
    print 'testing timeKeeper'
    
    tk = TimeKeeper()
    tk.addRequest()
    print tk.nrRequests()