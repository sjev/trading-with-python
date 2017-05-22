# -*- coding: utf-8 -*-

# Author: Jev Kuznetsov <jev.kuznetsov@gmail.com>
# License: BSD


"""
Toolset working with yahoo finance data
Module includes functions for easy access to YahooFinance data

"""



import urllib.request
from pandas import DataFrame, Index, HDFStore, Panel
import numpy as np
import os

import requests # interaction with the web
import os  #  file system operations
import yaml # human-friendly data format
import re  # regular expressions
import pandas as pd # pandas... the best time series library out there
import datetime as dt # date and time functions
import io 

from .extra import ProgressBar

dateTimeFormat = "%Y%m%d %H:%M:%S"

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
        self.wp = Panel()
        
        
    def load(self,dataFile):
        """load data from HDF"""
        if os.path.exists(dataFile):
            store = HDFStore(dataFile)
            symbols = [str(s).strip('/') for s in list(store.keys()) ]   
            data = dict(list(zip(symbols,[store[symbol] for symbol in symbols])))
            self.wp = Panel(data)
            store.close()
        else:
            raise IOError('Data file does not exist')
            
        
    def save(self,dataFile):
        """ save data to HDF"""
        print(('Saving data to', dataFile))
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
                    self.wp = Panel({symbol:df})
                else:
                    self.wp[symbol] = df
            
            except Exception as e:
                print(e) 
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
    """ 
    get current yahoo quote
    
    Parameters
    -----------
    symbols : list of str
        list of ticker symbols
        
    Returns
    -----------
    DataFrame , data is row-wise


    """
    
    # for codes see: http://www.gummy-stuff.org/Yahoo-data.htm
    if not isinstance(symbols,list):
        symbols = [symbols]
    
    
    header =               ['symbol','last','change_pct','PE','time','short_ratio','prev_close','eps','market_cap']    
    request = str.join('', ['s',     'l1',     'p2'  ,   'r', 't1',     's7',        'p',       'e'     , 'j1'])
    
    
    data = dict(list(zip(header,[[] for i in range(len(header))])))
    
    urlStr = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (str.join('+',symbols), request)
    
    try:
        lines = urllib.request.urlopen(urlStr).readlines()
    except Exception as e:
        s = "Failed to download:\n{0}".format(e);
        print(s)
    
    for line in lines:
        fields = line.decode().strip().split(',')
        #print fields, len(fields)
        for i,field in enumerate(fields):
            data[header[i]].append( parseStr(field))
            
    idx = data.pop('symbol')
    
    
    return DataFrame(data,index=idx)

def _historicDataUrll(symbol, sDate=(1990,1,1),eDate=dt.date.today().timetuple()[0:3]):
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
    symbols : str or list  
        Yahoo finanance symbol or a list of symbols
    sDate : tuple  (optional)
        start date (y,m,d)
    eDate : tuple  (optional)
        end date (y,m,d) 
    adjust : bool
        T/[F] adjust data based on adj_close
    
    Returns
    ---------
    Panel
    
    '''
    
    assert isinstance(symbols,(list,str)), 'Input must be a string symbol or a list of symbols'
    
    if isinstance(symbols,str):
        return getSymbolData(symbols,**options)
    else:
        data = {}
        print('Downloading data:')
        p = ProgressBar(len(symbols))
        for idx,symbol in enumerate(symbols):
            p.animate(idx+1)
            data[symbol] = getSymbolData(symbol,verbose=False,**options)
        
        return Panel(data)

def getSymbolData(symbol, sDate=(1990,1,1), eDate=None, adjust=False, verbose=True):
    """ 
    get data from Yahoo finance and return pandas dataframe

    Parameters
    -----------
    symbol : str
        Yahoo finanance symbol
    sDate : tuple , optional
        start date (y,m,d), defaults to 1 jan 1990
    eDate : tuple , optional
        end date (y,m,d), defaults to current date
    adjust : bool , optional
        use adjusted close values to correct OHLC. adj_close will be ommited
    verbose : bool , optional
        print output
            
    Returns
    ---------
        DataFrame
            
    """

    
    if eDate is None: eDate = dt.date.today().timetuple()[0:3]
    

    urlStr = 'http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}&d={4}&e={5}&f={6}'.\
    format(symbol.upper(),sDate[1]-1,sDate[2],sDate[0],eDate[1]-1,eDate[2],eDate[0])

    
    try:
        lines = urllib.request.urlopen(urlStr).readlines()
    except Exception as e:
        s = "Failed to download:\n{0}".format(e);
        print(s)
        return None

    dates = []
    data = [[] for i in range(6)]
    #high
    # header : Date,Open,High,Low,Close,Volume,Adj Close
    for line in lines[1:]:
        #print line
        fields = line.decode().rstrip().split(',')
        dates.append(dt.datetime.strptime( fields[0],'%Y-%m-%d'))
        for i,field in enumerate(fields[1:]):
            data[i].append(float(field))
       
    idx = Index(dates)
    data = dict(list(zip(['open','high','low','close','volume','adj_close'],data)))
    
    # create a pandas dataframe structure   
    df = DataFrame(data,index=idx).sort_index()
    
    if verbose:
        print(('Got %i days of data' % len(df)))
    
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
        renames = dict(list(zip(['adj_open','adj_close','adj_high','adj_low'],['open','close','high','low'])))
        df=df.rename(columns=renames)
    
    return df
    

def loadToken():
    """ 
    get cookie and crumb from APPL page or disk. 
    force = overwrite disk data
    """
    refreshDays = 30 # refreh cookie every x days
    
    # set destinatioin file
    dataDir = os.path.expanduser('~')+'/twpData'
    dataFile = dataFile = os.path.join(dataDir,'yahoo_cookie.yml')
    
    try : # load file from disk
        
        data = yaml.load(open(dataFile,'r'))
    
        age = (dt.datetime.now()- dt.datetime.strptime(  data['timestamp'], dateTimeFormat) ).days
                      
        assert age < refreshDays, 'cookie too old'
            
                         
    except (AssertionError,FileNotFoundError):     # file not found
        
        if not os.path.exists(dataDir):
            os.mkdir(dataDir)
        
        data = getToken(dataFile)
        
               
        
    
    return data


def getToken(fName = None):
    """ get cookie and crumb from yahoo """
    
    url = 'https://uk.finance.yahoo.com/quote/AAPL/history' # url for a ticker symbol, with a download link
    r = requests.get(url)  # download page
    
    txt = r.text # extract html
    
    cookie = r.cookies['B'] # the cooke we're looking for is named 'B'
    
    pattern = re.compile('.*"CrumbStore":\{"crumb":"(?P<crumb>[^"]+)"\}')
    
    for line in txt.splitlines():
        m = pattern.match(line)
        if m is not None:
            crumb = m.groupdict()['crumb']   
    
    assert r.status_code == 200 # check for succesful download
            
    # save to disk
    data = {'crumb': crumb, 'cookie':cookie, 'timestamp':dt.datetime.now().strftime(dateTimeFormat)}

    if fName  is not None: # save to file
        with open(fName,'w') as fid:
            yaml.dump(data,fid)
    
    return data

#--------------tests------------
# to be executed with pytest

def use_method():
    tst.test()


class testClass:
    def __init__(self):
        print('creating class')
        pass
    
    def test(self):
        print('foo')


def test_getToken():
    ''' download token '''
    result = getToken()   
    
    
def test_initToken():
    ''' remove and get token '''
    dataDir = os.path.expanduser('~')+'/twpData'
    dataFile = dataFile = os.path.join(dataDir,'yahoo_cookie.yml')
    
    if os.path.exists(dataFile):
        os.remove(dataFile)
    
    loadToken()
    
    assert os.path.exists(dataFile)
    
 
    
#tst = testClass()