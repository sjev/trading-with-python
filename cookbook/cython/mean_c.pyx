# -*- coding: utf-8 -*-
"""
test file for mean calculation
"""

#cython: boundscheck=False
#cython: wraparound=False

from __future__ import division
import numpy as np

cimport numpy as np
ctypedef np.float32_t dtype_t

def mean(np.ndarray[dtype_t, ndim=2] data):
    
    
    cdef unsigned int row, col, i
    cdef dtype_t val    
    
    cdef np.ndarray[dtype_t,ndim=1] s = np.zeros(data.shape[1], dtype=np.float32)
    
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            s[col]+=data[row,col]
            
    for row in xrange(s.shape[0]):
        s[row] = s[row]/data.shape[0]
        
    return s
    
        
    
