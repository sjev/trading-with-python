# -*- coding: utf-8 -*-
"""

This script downloads historic data for single or multiple securities through the
Interactive brokers API.

* the tool is run from the command line (see parameters below)
* configuration is done in ``settings.yml``. Here a list of security definitions is kept
    together with data destination folder
* the data is saved as ``.csv`` files in a directory structure.


Running script
----------------

.. argparse::
	:module: getData
	:func: getParser
	:prog: getData




"""


from tradingWithPython.lib.csvDatabase import HistDataCsv
from  tradingWithPython.lib.interactiveBrokers.helpers import createContract
from tradingWithPython.lib.interactiveBrokers.histData import Downloader
import tradingWithPython.lib.yahooFinance as yf
from tradingWithPython.lib import logger
import logging
import argparse

import pandas as pd
import os
import time
import datetime
import yaml

log =logger.getLogger('main',logFile='downloader.log',consoleLevel=logging.DEBUG)




def errorLogger(msg):
    if msg.typeName == 'error':
        log.error(str(msg))

def str2time(s):
    return datetime.datetime.strptime(s,"%Y%m%d %H:%M:%S")
        
def time2str(ts):
    return ts.strftime("%Y%m%d %H:%M:%S")
    
def lastTradingDate():
    """ determine last historic data date by downloading from yahoo finance"""
    data = yf.getHistoricData('SPY',sDate=(2016,1,1))
    return data.index[-1]

def getTradingDates():
    ''' get list of trading dates from yahoo, one year back'''
    startDate = (datetime.date.today() - datetime.timedelta(days=365)).timetuple()[:3]
    df =  yf.getHistoricData('SPY',sDate=startDate)
    dates = [d.date() for d in df.index]
    return dates



def getData(contract, db):
    """ get historic data for one date, return as DataFrame """
    
    halfYearAgo = datetime.date.today()- pd.DateOffset(months=6, days=-1)
    dataRange = db.dateRange # get data range in the database
    
    end = SETTINGS['end'] if SETTINGS['end'] is not None else lastTradingDate()

    log.debug('endDateTime:'+time2str(end))
    
    stopAt = max(halfYearAgo, dataRange[1]) # end of data download
    
    while (end > stopAt) :  
        log.info('Requesting block with end time %s' % end)
        data = DL.requestData(contract,end,durationStr='7200 S',barSizeSetting='5 secs',whatToShow='TRADES')
        
        db.saveData(data)
        # set new end time of the data block
        end = data.index[0]

   
    
def testDownload():
    """ used for testing """
    
    contract = createContract('VXX')
       
    #date = datetime.date(2016,10,6)
    
    
    
    end = SETTINGS['lastTradingDate']
    
    data = DL.requestData(contract,end,durationStr='6 M',barSizeSetting='1 day',whatToShow='TRADES')
    data.to_csv('temp/testDownload.csv')
  
    
def download(settings):
    """ download all symbols """
    
    #---------get subdirectories

    dataDir = settings['dataRoot']
    log.info('Data root is '+dataDir)
    
    subscriptions = settings['subscriptions']
    
    symbols = settings['getSymbols']

    #----------create objects
    contracts = {}
    csvData = {}
    
    for symbol in symbols:
        contracts[symbol] = createContract(symbol,
                                            secType = subscriptions[symbol]['secType'],
                                            exchange = subscriptions[symbol]['exchange'])
        csvData[symbol] = HistDataCsv(symbol,dataDir,autoCreateDir=True)
    
    #-----------download---------
    for symbol in symbols:
        try:
            getData(contracts[symbol],csvData[symbol])
        except:
            log.exception('Download failed')

def getParser():
    """ create command line parser """
    parser = argparse.ArgumentParser(description='Download historic data')
    parser.add_argument("--symbols",help = 'symbols separated by coma: SPY,VXX',default='all')
    parser.add_argument("--end", help= "timestamp from where to start download.\
                         Defaults to last trading date", default=None)

    return parser

if __name__ == "__main__":
    
    parser = getParser()
           
    args = vars(parser.parse_args())
    print(args)
    # load settings, using global var here
    SETTINGS = yaml.load(open('settings.yml','r'))
    SETTINGS['getSymbols'] = SETTINGS['subscriptions'].keys() if args['symbols']=='all' else args['symbols'].split(',')
    
    SETTINGS['end'] =  args['end'] 
    
    print(SETTINGS)
    
    DL = Downloader(debug=False) # downloader class
    DL.tws.registerAll(errorLogger)
    time.sleep(2)
    
    
    download(SETTINGS)
    
    #testDownload()
    
    print('All done.')