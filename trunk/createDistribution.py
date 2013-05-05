# -*- coding: utf-8 -*-


import os, shutil

# <codecell>

sourceDir = 'lib'
targetDir = 'dist\\tradingWithPython'

if not os.path.exists(targetDir): os.makedirs(targetDir)

includes = ['__init__','cboe','csvDatabase','functions','yahooFinance','extra']

for root, dirs, files in os.walk(sourceDir):
    for f in files:
        base,ext = os.path.splitext(f)

        if (ext =='.py') and (base in includes): 
            s = os.path.join(root, f)
            d = os.path.join(targetDir, f)
            print s, '->', d
            shutil.copyfile(s,d)
        

