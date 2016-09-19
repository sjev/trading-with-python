# -*- coding: utf-8 -*-
"""

@author: Jev Kuznetsov
"""

import tradingWithPython as twp
 
#---check for correct version
print ('twp version', twp.__version__)
 
from tradingWithPython.lib.interactiveBrokers import histData, createContract
 
dl = histData.Downloader(debug=True) # historic data downloader class
 
contract = createContract('SPY') # create contract using defaults (STK,SMART,USD)
data = dl.requestData(contract,"20130508 16:00:00 EST") # request 30-second data bars up till now
 
data.to_csv('SPY.csv') # write data to csv
 
print ('Done')
