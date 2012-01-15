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


# create from string


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
    t = dt.date(2010,month,1)
    offset = datetools.Week(weekday=2)
   
    if t.weekday()<>2:
        t_new = t+3*offset
    else:
        t_new = t+2*offset    
    
    print t_new.strftime("%B, %d %Y (%A)")

#rng = DateRange(t, t+datetools.YearEnd())
#print rng