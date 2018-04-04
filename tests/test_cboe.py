#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test cboe download

@author: jev
"""

import tradingWithPython.lib.cboe as cboe

def test_histData():
    """ test automatic download of csv data from CBOE """
    
    data = cboe.getHistoricData()
    