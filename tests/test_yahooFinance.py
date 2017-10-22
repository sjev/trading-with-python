#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests for yahooFinance module

@author: jev
"""

import tradingWithPython.lib.yahooFinance as yf

symbols = ['SPY','XLE','VXX']


def test_quote():
    quote = yf.getQuote(symbols)
    print(quote)
    
    assert quote.shape == (3,8)