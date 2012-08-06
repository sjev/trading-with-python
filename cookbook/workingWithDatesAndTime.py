# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 17:45:02 2011

@author: jev
"""

import time
import datetime as dt
from pandas import *
from pandas.core import datetools 





# basic functions
print 'Epoch start: %s' % time.asctime(time.gmtime(0))
print 'Seconds from epoch: %.2f' % time.time()

today = dt.date.today()
print type(today)
print 'Today is %s' % today.strftime('%Y.%m.%d')

# parse datetime
d = dt.datetime.strptime('20120803  21:59:59',"%Y%m%d %H:%M:%S")




# time deltas
someDate = dt.date(2011,8,1)
delta = today - someDate
print 'Delta :', delta

# calculate difference in dates
delta = dt.timedelta(days=20)
print 'Today-delta=', today-delta


t = dt.datetime(*time.strptime('3/30/2004',"%m/%d/%Y")[0:5])
# the '*' operator unpacks the tuple, producing the argument list.
print t


# print every 3d wednesday of the month
for month in xrange(1,13):
    t = dt.date(2012,month,1)+datetools.relativedelta(months=1)
    
    
    offset = datetools.Week(weekday=4)
    if t.weekday()<>4:
        t_new = t+3*offset
    else:
        t_new = t+2*offset    
    
    t_new = t_new-datetools.relativedelta(days=30)
    print t_new.strftime("%B, %d %Y (%A)")

#rng = DateRange(t, t+datetools.YearEnd())
#print rng

# create a range of times
start = dt.datetime(2012,8,1)+datetools.relativedelta(hours=9,minutes=30)
end = dt.datetime(2012,8,1)+datetools.relativedelta(hours=22)

rng = date_range(start,end,freq='30min')
for r in rng: print r.strftime("%Y%m%d %H:%M:%S")