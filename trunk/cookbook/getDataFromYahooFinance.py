# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 18:37:23 2011

@author: jev
"""

from urllib2 import urlopen

sDate = (2011,1,1)
eDate = (2011,10,1)


symbol = 'SPY'

urlStr = 'http://ichart.finance.yahoo.com/table.csv?s={0}&a={1}&b={2}&c={3}&d={4}&e={5}&f={6}'.\
    format(symbol.upper(),sDate[1]-1,sDate[2],sDate[0],eDate[1]-1,eDate[2],eDate[0])
    
print 'Downloading from ', urlStr

ll = urlopen(urlStr).readlines()

print ll