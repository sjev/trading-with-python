#-------------------------------------------------------------------------------
# Name:        BATS
# Purpose:     get data from BATS exchange
#
# Author:      jev
#
# Created:     17/08/2013
# Copyright:   (c) Jev Kuznetsov 2013
# Licence:     BSD
#-------------------------------------------------------------------------------

import urllib
import re
import pandas as pd
import datetime as dt
import zipfile
import StringIO
from extra import ProgressBar
import os
import yahooFinance as yf
from string import Template
import numpy as np

def fileName2date( fName):
    '''convert filename to date'''
    name = os.path.splitext(fName)[0]
    m = re.findall('\d+',name)[0]
    return dt.datetime.strptime(m,'%Y%m%d').date()

def date2fileName(date):
    return 'BATSshvol%s.txt.zip' % date.strftime('%Y%m%d')

def downloadUrl(date):
    s = Template('http://www.batstrading.com/market_data/shortsales/$year/$month/$fName-dl?mkt=bzx')
    url = s.substitute(fName=date2fileName(date), year=date.year, month='%02d' % date.month)
    return url

class BATS_Data(object):
    def __init__(self, dataDir):
        ''' create class. dataDir: directory to which files are downloaded '''
        self.dataDir = dataDir

        self.shortRatio = None
        self._checkDates()


    def _checkDates(self):
        ''' update list of available dataset dates'''
        self.dates = []
        for fName in os.listdir(self.dataDir):
                self.dates.append(fileName2date(fName))

    def _missingDates(self):
        ''' check for missing dates based on spy data'''
        print 'Getting yahoo data to determine business dates... ',
        spy = yf.getHistoricData('SPY',sDate = (2010,1,1))
        busDates = [d.date() for d in spy.index ]

        print 'Date range: ', busDates[0] ,'-', busDates[-1]
        missing = []
        for d in busDates:
            if d not in self.dates:
                missing.append(d)

        return missing

    def updateDb(self):

        print 'Updating database'
        missing = self._missingDates()

        for i, date in enumerate(missing):
            source = downloadUrl(date)

            dest = os.path.join(self.dataDir,date2fileName(date))
            if not os.path.exists(dest):
                print 'Downloading [%i/%i]' %(i,len(missing)), source
                urllib.urlretrieve(source, dest)
            else:
                print 'x',
        print 'Update done.'
        self._checkDates()

    def loadDate(self,date):
        fName = os.path.join(self.dataDir, date2fileName(date))
        zipped = zipfile.ZipFile(fName) # open zip file
        lines = zipped.read(zipped.namelist()[0]) # read first file from to lines
        buf = StringIO.StringIO(lines) # create buffer
        df = pd.read_csv(buf,sep='|',index_col=1,parse_dates=False,dtype={'Date':object,'Short Volume':np.float32,'Total Volume':np.float32})
        s = df['Short Volume']/df['Total Volume']
        s.name = dt.datetime.strptime(df['Date'][-1],'%Y%m%d')

        return s

    def loadData(self):
        ''' load data from zip files '''
        data = []

        pb = ProgressBar(len(self.dates)-1)

        for idx, date in enumerate(self.dates):
            data.append(self.loadDate(date))
            pb.animate(idx)

        self.shortRatio = pd.DataFrame(data)
        return self.shortRatio

