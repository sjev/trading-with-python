# -*- coding: utf-8 -*-
"""
toolset working with cboe data

@author: Jev Kuznetsov
Licence: GPL v2
"""

from datetime import datetime, date
import urllib2
from pandas import DataFrame, Index
import numpy as np



def getHistoricData(symbol):
    ''' get historic data from CBOE
        symbol: VIX or VXV
        return dataframe
    '''
    urls = {'VIX':'http://www.cboe.com/publish/ScheduledTask/MktData/datahouse/vixcurrent.csv', \
            'VXV':'http://www.cboe.com/publish/scheduledtask/mktdata/datahouse/vxvdailyprices.csv' }
    
    urlStr = urls[symbol]
    
    try:
        lines = urllib2.urlopen(urlStr).readlines()
    except Exception, e:
        s = "Failed to download:\n{0}".format(e);
        print s
        
    header = ['open','high','low','close']   
    dates = []
    data = [[] for i in range(len(header))]
     
    for line in lines[1:]:
        fields = line.rstrip().split(',')
        dates.append(datetime.strptime( fields[0],'%m/%d/%Y'))
        for i,field in enumerate(fields[1:]):
            data[i].append(float(field))
        
    
    
    return DataFrame(dict(zip(header,data)),index=Index(dates)).sort()
    
if __name__ == '__main__':
    vix = getHistoricData('VIX')
    vxv = getHistoricData('VXV')
    vix.plot()
    vxv.plot()