# -*- coding: utf-8 -*-
"""
set of tools for working with VIX futures

@author: Jev Kuznetsov
Licence: GPL v2
"""

import datetime as dt
from pandas.core import datetools 


class Future(object):
    ''' vix future class '''
    def __init__(self,year,month):
        self.year = year
        self.month = month
        self.expiration = self._calculateExpirationDate()
     
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
        
    def __repr__(self):
        s = 'Vix future [%i-%i] exp: %s' % (self.year, self.month, self.expiration.strftime("%B, %d %Y (%A)"))
        return s



if __name__ == '__main__':
    print 'testing vix futures'
    
    f = Future(2013,1)
    print f
    
    
    
