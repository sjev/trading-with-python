# -*- coding: utf-8 -*-
"""
set of tools for working with VIX futures

@author: Jev Kuznetsov
Licence: GPL v2
"""

import datetime as dt
from pandas import *
from pandas.core import datetools 
import urllib2
#from csvDatabase import HistDataCsv

m_codes = dict(zip(range(1,13),['F','G','H','J','K','M','N','Q','U','V','X','Z'])) #month codes of the futures
monthToCode = dict(zip(range(1,len(m_codes)+1),m_codes))


def getCboeData(year,month):
    ''' download data from cboe '''
    fName = "CFE_{0}{1}_VX.csv".format(m_codes[month],str(year)[-2:])
    urlStr =  "http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/{0}".format(fName)

    try:
        lines = urllib2.urlopen(urlStr).readlines()
    except Exception, e:
        s = "Failed to download:\n{0}".format(e);
        print s
        
    # first column is date, second is future , skip these
    header = lines[0].strip().split(',')[2:]
    
    dates = []    
    data = [[] for i in range(len(header))]
    
    
    
    for line in lines[1:]:
        fields = line.strip().split(',')
        dates.append(datetime.strptime( fields[0],'%m/%d/%Y'))
        for i,field in enumerate(fields[2:]):
            data[i].append(float(field))
        
    data = dict(zip(header,data))   
    
    df = DataFrame(data=data, index=Index(dates))
   
    return df
    
class Future(object):
    ''' vix future class '''
    def __init__(self,year,month):
        self.year = year
        self.month = month
        self.expiration = self._calculateExpirationDate()
        self.cboeData = None # daily cboe data
        self.intradayDb = None # intraday database (csv)
     
    def _calculateExpirationDate(self):
        ''' calculate expiration date of the future, (not 100% reliable) '''
        t = dt.date(self.year,self.month,1)+datetools.relativedelta(months=1)
        offset = datetools.Week(weekday=4)
        if t.weekday()<>4:
            t_new = t+3*offset
        else:
            t_new = t+2*offset    
        
        t_new = t_new-datetools.relativedelta(days=30)
        return t_new
    

    def getCboeData(self):
        ''' download interday CBOE data '''
        self.cboeData = getCboeData(self.year, self.month)
        return self.cboeData
    
    def updateIntradayDb(self,dbDir):
        #self.intradayDb = 
        pass
    
    @property
    def dates(self):
        ''' trading days derived from cboe data '''
        if self.cboeData is not None:
            dates = [d.date() for d in self.cboeData.index]
        else:
            dates = None
            
        return dates
    
    def __repr__(self):
        s = 'Vix future [%i-%i (%s)] exp: %s\n' % (self.year, self.month,monthToCode[self.month], self.expiration.strftime("%B, %d %Y (%A)"))
        s+= 'Cboe data: %i days'% len(self.cboeData) if self.cboeData is not None else  'No data downloaded yet'
        return s



if __name__ == '__main__':
    print 'testing vix futures'
    
    year = 2012
    month = 12
        
    
    f = Future(year,month)
    f.getCboeData()
    print f
    
    