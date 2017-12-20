#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests for yahooFinance module

@author: jev
"""

import tradingWithPython.lib.yahooFinance as yf

symbols = ['COP','SPY','VXX']

import os
if not os.path.exists('debug'):
    os.mkdir('debug')

def test_token():
    
    data = yf.getToken()
    


def test_histData():

    # one symbol
    hData = yf.getHistoricData(symbols[0], dumpDest='debug')
    hData.pct_change() # try a calculation. Will result in an error if data is rotten.
    
    
    assert hData.shape[1] == 6 
    assert hData.shape[0] > 100
       
    hData = yf.getHistoricData(symbols)
   

