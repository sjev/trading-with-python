# -*- coding: utf-8 -*-
"""
toolset working with yahoo finance data

Copyright: Jev Kuznetsov
Licence: BSD

"""


from datetime import datetime, date
import urllib2
from pandas import DataFrame, Index, HDFStore, WidePanel
import numpy as np


class HistData(object):
    ''' a class for working with yahoo finance data '''
    def __init__(self, dataFile,autoAdjust=True):
       
        self.dataFile = dataFile
        self.startDate = (2008,1,1)
        self.autoAdjust=autoAdjust
        self._load()
        
    def _load(self):
        """load data from HDF"""
        store = HDFStore(self.dataFile)
        symbols = store.keys()    
        data = dict(zip(symbols,[store[symbol] for symbol in symbols]))
        self.wp = WidePanel(data)
        store.close()
        
    def save(self):
        """ save data to HDF"""
        print 'Saving data to', self.dataFile
        store = HDFStore(self.dataFile)
        for symbol in self.wp.items:
            store[symbol] = self.wp[symbol]
            
        store.close()
                    
            
            
    def downloadData(self,symbols):
        ''' get data from yahoo  '''
        
        store = HDFStore(self.dataFile)        
        
        for idx,symbol in enumerate(symbols):
            print 'Downloading %s [%i/%i]' % (symbol,idx+1,len(symbols))
            try:            
                df = getHistoricData(symbol,self.startDate)
                print 'Got %i samples' % len(df)            
                if self.autoAdjust:
                   df =  adjust(df,removeOrig=True)
                
                if len(self.symbols)==0:
                    self.wp = WidePanel({symbol:df})
                else:
                    self.wp[symbol] = df
            
            except Exception,e:
                print e 
            
            else:
                store[symbol] = self.wp[symbol]
                store.flush()
            
        store.close()
             
    def loadSymbols(self,symbols,field='close'): 
        ''' load file from HDF5, update if needed '''
        
       
        # check symbols
        missing = []
        for symbol in symbols:
            if symbol not in self.symbols:
                missing.append(symbol)
        if len(missing)>0:
            print "Missing: {0}".format(missing)
            self.downloadData(missing)

        return self.wp
                    
      
            
    
    @property
    def symbols(self):
        return self.wp.items.tolist()        
           
  
    def __repr__(self):
        return str(self.symbols)

#    def __del__(self):
#        self._save()
#       

def getQuote(symbols):
    ''' get current yahoo quote
    
    
    , return a DataFrame  '''
    
    if not isinstance(symbols,list):
        raise TypeError, "symbols must be a list"
    # for codes see: http://www.gummy-stuff.org/Yahoo-data.htm
    codes = {'symbol':'s','last':'l1','change_pct':'p2','PE':'r','time':'t1','short_ratio':'s7'}
    request = str.join('',codes.values())
    header = codes.keys()
    
    data = dict(zip(codes.keys(),[[] for i in range(len(codes))]))
    
    urlStr = 'http://finance.yahoo.com/d/quotes.csv?s=%s&f=%s' % (str.join('+',symbols), request)
    
    try:
        lines = urllib2.urlopen(urlStr).readlines()
    except Exception, e:
        s = "Failed to download:\n{0}".format(e);
        print s

    for line in lines:
        fields = line.strip().split(',')
        #print fields
        for i,field in enumerate(fields):
            if field[0] == '"':
                data[header[i]].append( field.strip('"'))
            else:
                try:
                    data[header[i]].append(float(field))
                except ValueError:
                    data[header[i]].append(np.nan)

    idx = data.pop('symbol')
    
    return DataFrame(data,index=idx)
    

def getHistoricData(symbol, sDate=(1990,1,1),eDate=date.today().timetuple()[0:3]):
    """ get data from Yahoo finance and return pandas dataframe

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

    dates = []
    data = [[] for i in range(6)]
    #high
    
    # header : Date,Open,High,Low,Close,Volume,Adj Close
    for line in lines[1:]:
        fields = line.rstrip().split(',')
        dates.append(datetime.strptime( fields[0],'%Y-%m-%d'))
        for i,field in enumerate(fields[1:]):
            data[i].append(float(field))
       
    idx = Index(dates)
    data = dict(zip(['open','high','low','close','volume','adj_close'],data))
    
    # create a pandas dataframe structure   
    df = DataFrame(data,index=idx).sort()
    
    return df

def adjust(df, removeOrig=False):
    ''' adjust hist data based on adj_close field '''
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

#-------------------test functioins
def testHistData():
   
    h = HistData('C:/temp/histData.csv')
    symbols = ['SPY','USO']
    
    df = h.loadSymbols(symbols,forceDownload = True)
    print df.tail()


if __name__=='__main__':
    print 'Testing twp toolset'
    #data = getHistoricData('SPY')
    #print data
    testHistData()
   
    #print getQuote(['SPY','VXX','GOOG','AAPL'])