# -*- coding: utf-8 -*-
"""
toolset working with yahoo finance data

@author: Jev Kuznetsov
Licence: GPL v2
"""


from datetime import datetime, date
import urllib2
from pandas import DataFrame, Index
import numpy as np

def getHistoricData(symbol, sDate=(2010,1,1),eDate=date.today().timetuple()[0:3]):
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



if __name__=='__main__':
    print 'Testing twp toolset'
    data = getHistoricData('SPY')
    print data