# -*- coding: utf-8 -*-
"""
example on how to run a console script until interrupted by keyboard

@author: jev
"""


from time import sleep
counter = 0

print 'Press Ctr-C to stop loop'

try:
        while True:
            print counter
            counter += 1
            sleep(1)
            
except KeyboardInterrupt:
    print 'All done'
            
