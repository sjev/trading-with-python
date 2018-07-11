#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Check versions of installed modules
@author: jev
"""

""" print versions of most important modules """
import imp

modules = ['conda','numpy','tradingWithPython','pandas','ibapi','ib']




from distutils.sysconfig import get_python_lib
print('Python library locations: ',get_python_lib())

def getModuleInfo(module):
    try:
        result = imp.find_module(name)
        pkg = imp.load_module(name,*result)
        return {'version':pkg.__version__,
                'location':pkg.__file__}
        
    except ImportError as e:
        print(e)
        return None
        
with open('sysinfo.txt','w') as fid:    
    
    for name in modules:
        s = 5*'-'+name+5*'-'
        print(s)
        fid.write(s + '\n')
        
        res = getModuleInfo(name)
        print(res)
        fid.write(str(res)+'\n')