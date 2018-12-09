#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Calendar functions

based on examples from here: https://stackoverflow.com/questions/33094297/create-trading-holiday-calendar-with-pandas
and pandas docs: https://pandas.pydata.org/pandas-docs/stable/timeseries.html?highlight=abstractholidaycalendar

@author: jev
"""

import numpy as np

from pandas.tseries.holiday import AbstractHolidayCalendar, Holiday, nearest_workday, \
    USMartinLutherKingJr, USPresidentsDay, GoodFriday, USMemorialDay, \
    USLaborDay, USThanksgivingDay


class USTradingCalendar(AbstractHolidayCalendar):
    rules = [
        Holiday('NewYearsDay', month=1, day=1, observance=nearest_workday),
        USMartinLutherKingJr,
        USPresidentsDay,
        GoodFriday,
        USMemorialDay,
        Holiday('USIndependenceDay', month=7, day=4, observance=nearest_workday),
        USLaborDay,
        USThanksgivingDay,
        Holiday('Christmas', month=12, day=25, observance=nearest_workday)
    ]


holidays = [d.date() for d in USTradingCalendar().holidays().to_pydatetime()]

def busday_count(startTs,endTs):
    """ calculate number of business days between two timestamsp """
    return np.busday_count(startTs.date(),endTs.date(),holidays=holidays)
    
