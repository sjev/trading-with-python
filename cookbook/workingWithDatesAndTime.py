# -*- coding: utf-8 -*-
"""
Created on Sun Oct 16 17:45:02 2011

@author: jev
"""

import time
import datetime


# basic functions
print 'Epoch start: %s' % time.asctime(time.gmtime(0))
print 'Seconds from epoch: %.2f' % time.time()

today = datetime.date.today()
print type(today)
print 'Today is %s' % today.strftime('%Y.%m.%d')


# create from string


# time deltas
someDate = datetime.date(2011,8,1)
delta = today - someDate
print 'Delta :', delta

# calculate difference in dates
delta = datetime.timedelta(days=20)
print 'Today-delta=', today-delta

