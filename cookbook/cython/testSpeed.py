# -*- coding: utf-8 -*-
"""
Created on Wed Jan 25 20:43:49 2012

@author: jev
"""


import numpy as np
import mean_py
import mean_c
import time

a = np.random.rand(128,100000).astype(np.float32)

start = time.clock()
#m1 = a.sum(axis=1)
#m1 = m1/a.shape[0]
m1 = a.mean(axis=0)
print 'Done in %.3f s' % (time.clock()-start)
print m1.shape

start = time.clock()
m2 = mean_c.mean(a)
print 'Done in %.3f s' % (time.clock()-start)
print m2.shape
#clf()
#plot(m1,'b-x')
#plot(m2,'r-o')
#plot(a.mean(axis=0),'g')