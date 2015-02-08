# -*- coding: utf-8 -*-

# Author: Jev Kuznetsov <jev.kuznetsov@gmail.com>
# License: BSD


"""
Toolset working with yahoo finance data

This module includes functions for easy access to YahooFinance data

Functions
----------
- `getHistoricData`  get historic data for a single symbol
- `getQuote` get current quote for a symbol
- `getScreenerSymbols` load symbols from a yahoo stock screener file

Classes
---------
- `HistData` a class for working with multiple symbols



"""


from datetime import datetime, date
import urllib2
from pandas import DataFrame, Index, HDFStore, WidePanel
import numpy as np
import os
from extra import ProgressBar



def parseStr(s):
    ''' convert string to a float or string '''
    f = s.strip()
    if f[0] == '"':
        return f.strip('"')
    elif f=='N/A':
        return np.nan
    
    else:
        try: # try float conversion
            prefixes = {'M':1e6, 'B': 1e9} 
            prefix = f[-1]
            
            if prefix in prefixes: # do we have a Billion/Million character?
                return float(f[:-1])*prefixes[prefix]
            else:                       # no, convert to float directly
                return float(f)
        except ValueError: # failed, return original string
            return s

class HistData(object):
    ''' a class for working with yahoo finance data '''
    def __init__(self, autoAdjust=True):
       
        self.startDate = (2008,1,1)
        self.autoAdjust=autoAdjust
        self.wp = WidePanel()
        
        
    def load(self,dataFile):
        """load data from HDF"""
        if os.path.exists(dataFile):
            store = HDFStore(dataFile)
            symbols = [str(s).strip('/') for s in store.keys() ]   
            data = dict(zip(symbols,[store[symbol] for symbol in symbols]))
            self.wp = WidePanel(data)
            store.close()
        else:
            raise IOError('Data file does not exist')
            
        
    def save(self,dataFile):
        """ save data to HDF"""
        print 'Saving data to', dataFile
        store = HDFStore(dataFile)
        for symbol in self.wp.items:
            store[symbol] = self.wp[symbol]
            
        store.close()
                    
            
            
    def downloadData(self,symbols='all'):
        ''' get data from yahoo  '''
        
        if symbols == 'all':
            symbols = self.symbols
        
        #store = HDFStore(self.dataFile)        
        p = ProgressBar(len(symbols))
        
        for idx,symbol in enumerate(symbols):
            
            try:            
                df = getSymbolData(symbol,sDate=self.startDate,verbose=False)
                if self.autoAdjust:
                    df =  _adjust(df,removeOrig=True)
                
                if len(self.symbols)==0:
                    self.wp = WidePanel({symbol:df})
                else:
                    self.wp[symbol] = df
            
            except Exception,e:
                print e 
            p.animate(idx+1)
    
    def getDataFrame(self,field='close'):
        ''' return a slice on wide panel for a given field '''
        return self.wp.minor_xs(field)
         
    
    @property
    def symbols(self):
        return self.wp.items.tolist()        
           
  
    def __repr__(self):
        return str(self.wp)


def getQuote(symbols):
    ''' get current yahoo quote, return a DataFrame  '''
    # for codes see: http://www.gummy-stuff.org/Yahoo-data.htm
    if not isinstance(symbols,list):
        symbols = [symbols]
    
    
    header =               ['symbol','last','change_pct','PE','time','short_ratio','prev_close','eps','market_cap']    
    request = str.join('', ['s',     'l1',     'p2'  ,   'r', 't1',     's7',        'p',       'e'     , 'j1'])
    
    
    data = dict(zip(header,[[] for i in range(len(header))]))
    
    urlStr = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (str.join('+',symbols), request)
    
    try:
        lines = urllib2.urlopen(urlStr).readlines()
    except Exception, e:
        s = "Failed to download:\n{0}".format(e);
        print s
    
    for line in lines:
        fields = line.strip().split(',')
        #print fields, len(fields)
        for i,field in enumerate(fields):
            data[header[i]].append( parseStr(field))
            
    idx = data.pop('symbol')
    
    
    return DataFrame(data,index=idx)

def _historicDataUrll(symbol, sDate=(1990,1,1),eDate=date.today().timetuple()[0:3]):
    """ 
    generate url

    symbol: Yahoo finanance symbol
    sDate: start date (y,m,d)
    eDate: end date (y,m,d)
    """

    urlStr = 'http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}&d={4}&e={5}&f={6}'.\
    format(symbol.upper(),sDate[1]-1,sDate[2],sDate[0],eDate[1]-1,eDate[2],eDate[0])
    
    return urlStr

def getHistoricData(symbols, **options):
    ''' 
    get data from Yahoo finance and return pandas dataframe
    Will get OHLCV data frame if sinle symbol is provided. 
    If many symbols are provided, it will return a wide panel
    
    Parameters
    ------------
    symbols: Yahoo finanance symbol or a list of symbols
    sDate: start date (y,m,d)
    eDate: end date (y,m,d)
    adjust : T/[F] adjust data based on adj_close
    
    '''
    
    assert isinstance(symbols,(list,str)), 'Input must be a string symbol or a list of symbols'
    
    if isinstance(symbols,str):
        return getSymbolData(symbols,**options)
    else:
        data = {}
        print 'Downloading data:'
        p = ProgressBar(len(symbols))
        for idx,symbol in enumerate(symbols):
            p.animate(idx+1)
            data[symbol] = getSymbolData(symbol,verbose=False,**options)
        
        return WidePanel(data)

def getSymbolData(symbol, sDate=(1990,1,1),eDate=date.today().timetuple()[0:3], adjust=False, verbose=True):
    """ 
    get data from Yahoo finance and return pandas dataframe

    symbol: Yahoo finanance symbol
    sDate: start date (y,m,d)
    eDate: end date (y,m,d)
    """

    urlStr = 'http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}&d={4}&e={5}&f={6}'.\
    format(symbol.upper(),sDate[1]-1,sDate[2],sDate[0],eDate[1]-1,eDate[2],eDate[0])

    
    try:
        lines = urllib2.urlopen(urlStr).readlines()
    except Exception, e:
        s = "Failed to download:\n{0}".format(e);
        print s
        return None

    dates = []
    data = [[] for i in range(6)]
    #high
    
    # header : Date,Open,High,Low,Close,Volume,Adj Close
    for line in lines[1:]:
        #print line
        fields = line.rstrip().split(',')
        dates.append(datetime.strptime( fields[0],'%Y-%m-%d'))
        for i,field in enumerate(fields[1:]):
            data[i].append(float(field))
       
    idx = Index(dates)
    data = dict(zip(['open','high','low','close','volume','adj_close'],data))
    
    # create a pandas dataframe structure   
    df = DataFrame(data,index=idx).sort()
    
    if verbose:
        print 'Got %i days of data' % len(df)
    
    if adjust:
        return _adjust(df,removeOrig=True)
    else:
        return df

def _adjust(df, removeOrig=False):
    ''' 
  _adjustust hist data based on adj_close field 
    '''
    c = df['close']/df['adj_close']
    
    df['adj_open'] = df['open']/c
    df['adj_high'] = df['high']/c
    df['adj_low'] = df['low']/c
 
    if removeOrig:
        df=df.drop(['open','close','high','low'],axis=1)
        renames = dict(zip(['adj_open','adj_close','adj_high','adj_low'],['open','close','high','low']))
        df=df.rename(columns=renames)
    
    return df
    
def getScreenerSymbols(fileName):
    ''' read symbols from a .csv saved by yahoo stock screener '''
    
    with open(fileName,'r') as fid:
        lines = fid.readlines()

    symbols = []   
    for line in lines[3:]:
        fields = line.strip().split(',')
        field = fields[0].strip()
        if len(field) > 0:
            symbols.append(field) 
    return symbols

