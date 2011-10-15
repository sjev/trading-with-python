#-------------------------------------------------------------------------------
# Name:        download CBOE futures
# Purpose:     get VIX futures data from CBOE and save to user directory
#
#
# Created:     15-10-2011
# Copyright:   (c) Jev Kuznetsov 2011
# Licence:     GPL v2
#-------------------------------------------------------------------------------
#!/usr/bin/env python



from urllib import urlretrieve
import os

m_codes = ['F','G','H','J','K','M','N','Q','U','V','X','Z'] #month codes of the futures
dataDir = os.getenv("USERPROFILE")+'\\twpData\\vixFutures' # data directory

def saveVixFutureData(year,month, path):
    ''' Get future from CBOE and save to file '''
    fName = "CFE_{0}{1}_VX.csv".format(m_codes[month],str(year)[-2:])
    urlStr = "http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/{0}".format(fName)

    try:
        urlretrieve(urlStr,path+'\\'+fName)
    except Exception as e:
        print e



if __name__ == '__main__':

    if not os.path.exists(dataDir):
        os.makedirs(dataDir)

    for year in range(2004,2012):
        for month in range(12):
            print 'Getting data for {0}/{1}'.format(year,month)
            saveVixFutureData(year,month,dataDir)

    print 'Data was saved to {0}'.format(dataDir)