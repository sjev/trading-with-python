# -*- coding: utf-8 -*-
"""
test file for mean calculation
"""

from __future__ import division
import numpy as np

def mean(data):
    
    s = np.zeros(data.shape[1])
    
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            s[col]+=data[row,col]
            
    for i in range(s.shape[0]):
        s[i] = s[i]/data.shape[0]
        
    
    return s
        
    
