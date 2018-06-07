#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
basic functions and classes tests

@author: jev
"""

import tradingWithPython.lib.functions as functions
import numpy as np
import pandas as pd


def test_extractFuture():
    
    L = 100 # signal length
    p = pd.Series(np.arange(L))
    s = np.zeros(L, dtype=np.int)
    for idx in range(10,L,20):
        s[idx:idx+10] = 1
        
    s = pd.Series(s)
    triggers  = np.where(pd.Series(s).diff() == 1)[0]
    
    fut = functions.extractFuture(p,s, n=10)
    print('Future matrix:')
    print(fut)
    assert fut.shape == (10,5)
    assert (fut.columns == triggers).all()
    assert (fut.iloc[:,0] == 10+np.arange(10)).all()
    
    fut = functions.extractFuture(p,s, n=20)
    print('Future matrix:')
    print(fut)
    assert fut.shape == (20,5)