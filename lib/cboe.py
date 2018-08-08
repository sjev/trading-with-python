# -*- coding: utf-8 -*-
"""
toolset working with cboe data

@author: Jev Kuznetsov
Licence: BSD
"""
from datetime import datetime
import urllib.request, urllib.error, urllib.parse
from pandas.tseries import offsets 
import numpy as np
import pandas as pd
import os
from urllib import request

def _loadExpirationDates():
    """ load expiration dates from file """
    path = os.path.split(__file__)[0]
    fName=os.path.join(path,'data','vix_expiration.txt')
    with open(fName,'r') as fid:
        lines = fid.readlines()
    
    dates = []
    for line in lines:
        if line[0] != '#':
            s = line.strip().strip('*').strip()
            dates.append(pd.Timestamp.strptime(s,"%d %B %Y"))

    # repack to {(year,month):timestamp}
    yearmonth = [(d.year,d.month) for d in dates]

    return dict(zip(yearmonth,dates))


def monthCode(month):
    """ 
    perform month->code and back conversion
    
    Input: either month nr (int) or month code (str)
    Returns: code or month nr
    
    """
    codes = ('F','G','H','J','K','M','N','Q','U','V','X','Z')
    
    if isinstance(month,int):
        return codes[month-1]
    elif isinstance(month,str):
        return codes.index(month)+1
    else:
        raise ValueError('Function accepts int or str')
    
    
def vixExpiration(year,month,precise=True):
    """
    expriration date of a VX future. 
    precise option loads data from file, but is limited
    """
    
    if not precise:
        t = datetime(year,month,1)+offsets.relativedelta(months=1)
        offset = offsets.Week(weekday=4)
        if t.weekday()!=4:
            t_new = t+3*offset
        else:
            t_new = t+2*offset    
        
        t_exp = t_new-offsets.relativedelta(days=30)
    else:
        t_exp =  vixExpirations[(year,month)]
        
    return t_exp

def getPutCallRatio():
    """ download current Put/Call ratio"""
    urlStr = 'http://www.cboe.com/publish/ScheduledTask/MktData/datahouse/totalpc.csv'

    try:
        data = urllib.request.urlopen(urlStr)
    except Exception as e:
        s = "Failed to download:\n{0}".format(e);
        print(s)
       
    headerLine = 2
    
    return pd.read_csv(data,header=headerLine,index_col=0,parse_dates=True)
        
    

def getHistoricData(symbols =  ['VIX','VIX3M','VXMT','VVIX']):
    ''' get historic data from CBOE
       
        return dataframe
    '''
    if not isinstance(symbols,list):
        symbols = [symbols]
    
    urls = {'VIX':'http://www.cboe.com/publish/ScheduledTask/MktData/datahouse/vixcurrent.csv',
            'VXV':'http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vix3mdailyprices.csv', # VXV has been replaced by VIX3M
            'VXMT':'http://www.cboe.com/publish/ScheduledTask/MktData/datahouse/vxmtdailyprices.csv',
            'VVIX':'http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/VVIXtimeseries.csv',
            'VIX3M':'http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vix3mdailyprices.csv'}
    
    startLines = {'VIX':1,'VXV':2,'VIX3M':2,'VXMT':2,'VVIX':1}
    cols = {'VIX':'VIX Close','VXV':'CLOSE','VXMT':'Close','VVIX':'VVIX','VIX3M':'CLOSE'}
    
    data = {}
  
    for symbol in symbols:
        urlStr = urls[symbol]
        print('Downloading %s from %s' % (symbol,urlStr))
        
        data[symbol] = pd.read_csv(urllib.request.urlopen(urlStr), header=startLines[symbol],index_col=0,parse_dates=True)[cols[symbol]]
    
    
    return pd.DataFrame(data)
    
def parseFutureCsv(stream):
    """ 
    parse cboe future csv data
    input : string object
    output: DataFrame
    """
    lines = stream.readlines()
    for iLine in range(3):
        if lines[iLine].split()[0] == b'Trade':
            break
    # create stream from bytes
    from io import BytesIO
    stream = BytesIO(b''.join(lines[iLine:]))
    data = pd.read_csv(stream,index_col=0)
    
    return data

#---------------------classes--------------------------------------------
class VixFuture(object):
    """
    Class for easy handling of futures data.
    """    
    
    def __init__(self,year,month,data=None):
        self.year = year
        self.month = month
        self.data = data
    
    @property
    def expirationDate(self):
        return vixExpiration(self.year,self.month)
    
    @classmethod
    def from_file(cls,fName):
        """ load cboe csv file """
        
        data = parseFutureCsv(open(fName,'rb'))
        
        s = fName.stem.split('_')[1]
        year = 2000+int(s[-2:]) 
        month = monthCode(s[0])
        return cls(year,month,data)
        
    def getData(self):
        """ download data from cboe """
        print('getting data')   
        fName = "CFE_{0}{1}_VX.csv".format(monthCode(self.month),str(self.year)[-2:])
        urlStr = "http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/{0}".format(fName)
        
        # some files have a disclaimer on the first line, so some extra code 
        # is needed here
        
        # find first line with header
        url = request.urlopen(urlStr)
        self.data = parseFutureCsv(url)
        
        return self.data
    
    def _parseData(self, stream):
        """ load data from stream. used by getData and from_file """
        
        
        
       
    def __getattr__(self,attr):
        if attr in self.data.keys():
            return self.data[attr]
        else:
            raise AttributeError('Unknown attribute '+attr)
            
    def __dir__(self):
        return self.data.keys()
    
    def __repr__(self):
        return 'VX future [%i-%i %s] Exprires: %s' % (self.year,self.month,monthCode(self.month),
                                                        self.expirationDate)
#-------------------test functions---------------------------------------
def testDownload():
    vix = getHistoricData('VIX')
    vxv = getHistoricData('VXV')
    vix.plot()
    vxv.plot()       

def testExpiration():
    for month in range(1,13):
        d = vixExpiration(2011,month)
        print(d.strftime("%B, %d %Y (%A)"))    
        
        
# variables
vixExpirations = _loadExpirationDates()


if __name__ == '__main__':
    
    #testExpiration()
    v = VixFuture(2011,11)
    print(v)
    
    print(v.daysLeft(datetime(2011,11,10)))
        
    