import tradingWithPython as twp
 
#---check for correct version
print 'twp version', twp.__version__
assert twp.__version__ >= '0.0.6', 'Your twp distribution is too old, please update'
 
from tradingWithPython.lib.interactiveBrokers import histData, createContract


dl = histData.Downloader(debug=True) # historic data downloader class
 
contract = createContract('SPY') # create contract using defaults (STK,SMART,USD)
data = dl.requestData(contract,"20130508 16:00:00 EST") # request 30-second data bars up till now
 
data.to_csv('SPY.csv') # write data to csv
 
print 'Done'