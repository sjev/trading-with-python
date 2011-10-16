# -*- coding: utf-8 -*-
"""
toolset working with yahoo finance data

@author: Jev Kuznetsov
Licence: GPL v2
"""


from datetime import date
import urllib2
import pandas
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
        fh = urllib2.urlopen(urlStr)
    except Exception, e:
        s = "Failed to download:\n{0}".format(e);
        print s

    #----------------parse csv data

    h = fh.next().rstrip().split(',')    # split functionality is amazing
    header = dict(zip(h,range(len(h)))) #create header dictionary


    data = [[] for i in range(len(header))] # init data list

    for line in fh:
        line = line.rstrip()
        fields = line.strip('"').split(',')
        for i,val in enumerate(fields):
            try:
                d = float(val)
            except (ValueError,):
                d = val
            data[i].append(d)

    # convert to numpy array
    cols = ['Open','High','Low','Close','Adj Close']

    a = np.array([data[header[h]] for h in cols]).transpose()

    #columns=[header[i] for i in idx]
    df = pandas.DataFrame(a,data[0],columns=[x.lower() for x in cols]).sort_index()

    return df



if __name__=='__main__':
    print 'Testing twp toolset'
    data = getHistoricData('SPY')
    print data