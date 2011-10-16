# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 18:37:23 2011

@author: jev
"""


from urllib import urlretrieve
from urllib2 import urlopen
from pandas import Index, DataFrame
from datetime import datetime

sDate = (2011,1,1)
eDate = (2011,10,1)

symbol = 'SPY'

fName = symbol+'.csv'

try:    # try to load saved csv file, otherwise get from the net
    fid = open(fName)
    lines = fid.readlines()
    fid.close()
    print 'Loaded from ' , fName
except Exception as e:
    print e
    urlStr = 'http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}&d={4}&e={5}&f={6}'.\
    format(symbol.upper(),sDate[1]-1,sDate[2],sDate[0],eDate[1]-1,eDate[2],eDate[0])
    print 'Downloading from ', urlStr
    urlretrieve(urlStr,symbol+'.csv')
    lines = urlopen(urlStr).readlines()


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




