# -*- coding: utf-8 -*-

# Author: Jev Kuznetsov <jev.kuznetsov@gmail.com>
# License: BSD


"""

.. ipython:: python
    :suppress:
        
    import pandas as pd
    np.set_printoptions(precision=2, suppress=True)
    pd.options.display.max_rows= 6


Yahoo Finance 
====================


This module enables easy access to data provided by Yahoo Finance.

.. note::
    
    This service may stop without notice, Yahoo does not seem to like people accessing their
    data automatically. Breaking the service already happened in early 2017. This module includes 
    a workaround that works ... for now. 


Getting historic data
-----------------------

The module is usually imported as follows:

.. ipython:: python

   from tradingWithPython import yahooFinance as yf

Singe symbol
---------------------
   
Then, to get raw yahoo finance data for a symbol use :func:`~lib.yahooFinance.getSymbolData`

.. ipython:: python

   df = yf.getSymbolData("SPY")
   df.head()
   
We can also normalize OHLC with the *adj_close* data column. After normalization,
the *close* column will be equal to *adj_close* , so the latter is omitted from the result.

.. ipython:: python

    df = yf.getSymbolData("SPY",adjust=True)
    df.head()
    
Multiple symbols
-------------------------

:func:`~lib.yahooFinance.getHistoricData` will accept one ore more symbols and download them
while displaying a progress bar.

.. ipython:: python
    
    symbols = ['XLE','USO','SPY']
    data = yf.getHistoricData(symbols)
    
The data will be a multi-index DataFrame:

.. ipython:: python

    data.columns

To select  a symbol, simply use

.. ipython:: python
    
    data['SPY']
    

Or with cross-section (see `Advanced indexing <https://pandas.pydata.org/pandas-docs/stable/advanced.html>`_)
    
.. ipython:: python

    data.xs('close',level=1,axis=1)
    

    

   
Functions
==========

.. autofunction:: tradingWithPython.lib.yahooFinance.getSymbolData
.. autofunction:: tradingWithPython.lib.yahooFinance.getHistoricData

"""



import numpy as np

import requests # interaction with the web
import os  #  file system operations
import yaml # human-friendly data format
import re  # regular expressions
import pandas as pd # pandas... the best time series library out there
import datetime as dt # date and time functions
import io
from time import sleep

from tradingWithPython.lib.extra import ProgressBar

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



#def getQuote(symbols): has been disabled by Yahoo :-(
 

def getHistoricData(symbols, delay=0.5, **options):
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
    adjust : bool
        T/[F] adjust data based on adj_close

    Returns
    ---------
    DataFrame, multi-index

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
            sleep(delay)

        return pd.concat(data,axis=1, names=['symbol','ohlcv'])

def getSymbolData(symbol, sDate=(2000,1,1), adjust=False, verbose=True, dumpDest=None):
    """
    get data from Yahoo finance and return pandas dataframe

    Parameters
    -----------
    symbol : str
        Yahoo finanance symbol
    sDate : tuple , default (2000,1,1)
        start date (y,m,d)
    adjust : bool , default False
        use adjusted close values to correct OHLC. adj_close will be ommited
    verbose : bool , default True
        print output
    dumpDest : str, default None
        dump raw data for debugging

    Returns
    ---------
        DataFrame

    """

    period1 = int(dt.datetime(*sDate).timestamp()) # convert to seconds since epoch
    period2 = int(dt.datetime.now().timestamp())

    params = (symbol, period1, period2, _token['crumb'])

    url = "https://query1.finance.yahoo.com/v7/finance/download/{0}?period1={1}&period2={2}&interval=1d&events=history&crumb={3}".format(*params)

    data = requests.get(url, cookies={'B':_token['cookie']})
    data.raise_for_status() # raise error in case of bad request

    if dumpDest is not None:
        fName = symbol+'_dump.csv'
        with open(os.path.join(dumpDest, fName),'w') as fid:
            fid.write(data.text)

    buf = io.StringIO(data.text) # create a buffer
    df = pd.read_csv(buf,index_col=0,parse_dates=True, na_values=['null']) # convert to pandas DataFrame

    # rename columns
    newNames = [c.lower().replace(' ','_') for c in df.columns]
    renames = dict(zip(df.columns,newNames))
    df = df.rename(columns=renames)

    if verbose:
        print(('Got %i days of data' % len(df)))

    if adjust:
        return _adjust(df,removeOrig=True).round(2)
    else:
        return df.round(2)

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


#-------------- get token
_token = loadToken() # get token from disk or yahoo

#--------------tests------------
# to be executed with pytest


def test_getToken():
    ''' download token '''
    print('getting token')
    getToken()


def test_initToken():
    ''' remove and get token '''
    dataDir = os.path.expanduser('~')+'/twpData'
    dataFile = dataFile = os.path.join(dataDir,'yahoo_cookie.yml')

    if os.path.exists(dataFile):
        os.remove(dataFile)

    loadToken()

    assert os.path.exists(dataFile)

def test_download():

    vxx = getSymbolData('SPY')

    assert len(vxx) > 4000
