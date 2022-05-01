# -*- coding: utf-8 -*-
"""
set of tools for working with VIX futures

@author: Jev Kuznetsov
Licence: GPL v2
"""

import datetime as dt
from pandas import *
import os
import urllib.request, urllib.error, urllib.parse

# from csvDatabase import HistDataCsv

m_codes = dict(
    list(
        zip(
            list(range(1, 13)),
            ["F", "G", "H", "J", "K", "M", "N", "Q", "U", "V", "X", "Z"],
        )
    )
)  # month codes of the futures
monthToCode = dict(list(zip(list(range(1, len(m_codes) + 1)), m_codes)))


def getCboeData(year, month):
    """download data from cboe"""
    fName = "CFE_{0}{1}_VX.csv".format(m_codes[month], str(year)[-2:])
    urlStr = "http://cfe.cboe.com/Publish/ScheduledTask/MktData/datahouse/{0}".format(
        fName
    )

    try:
        lines = urllib.request.urlopen(urlStr).readlines()
    except Exception as e:
        s = "Failed to download:\n{0}".format(e)
        print(s)

    # first column is date, second is future , skip these
    header = lines[0].strip().split(",")[2:]

    dates = []
    data = [[] for i in range(len(header))]

    for line in lines[1:]:
        fields = line.strip().split(",")
        dates.append(datetime.strptime(fields[0], "%m/%d/%Y"))
        for i, field in enumerate(fields[2:]):
            data[i].append(float(field))

    data = dict(list(zip(header, data)))

    df = DataFrame(data=data, index=Index(dates))

    return df


class Future(object):
    """vix future class"""

    def __init__(self, year, month):
        self.year = year
        self.month = month
        self.expiration = self._calculateExpirationDate()
        self.cboeData = None  # daily cboe data
        self.intradayDb = None  # intraday database (csv)

    def _calculateExpirationDate(self):
        """calculate expiration date of the future, (not 100% reliable)"""
        t = dt.date(self.year, self.month, 1) + datetools.relativedelta(months=1)
        offset = datetools.Week(weekday=4)
        if t.weekday() != 4:
            t_new = t + 3 * offset
        else:
            t_new = t + 2 * offset

        t_new = t_new - datetools.relativedelta(days=30)
        return t_new

    def getCboeData(self, dataDir=None, forceUpdate=False):
        """download interday CBOE data
        specify dataDir to save data to csv.
        data will not be downloaded if csv file is already present.
        This can be overridden with setting forceUpdate to True
        """

        if dataDir is not None:
            fileFound = os.path.exists(self._csvFilename(dataDir))

            if forceUpdate or not fileFound:
                self.cboeData = getCboeData(self.year, self.month)
                self.to_csv(dataDir)
            else:
                self.cboeData = DataFrame.from_csv(self._csvFilename(dataDir))

        else:
            self.cboeData = getCboeData(self.year, self.month)

        return self.cboeData

    def updateIntradayDb(self, dbDir):
        # self.intradayDb =
        pass

    def to_csv(self, dataDir):
        """save to csv in given dir. Filename is automatically generated"""
        self.cboeData.to_csv(self._csvFilename(dataDir))

    @property
    def dates(self):
        """trading days derived from cboe data"""
        if self.cboeData is not None:
            dates = [d.date() for d in self.cboeData.index]
        else:
            dates = None

        return dates

    def _csvFilename(self, dataDir):
        fName = "VIX_future_%i_%i.csv" % (self.year, self.month)
        return os.path.join(dataDir, fName)

    def __repr__(self):
        s = "Vix future [%i-%i (%s)] exp: %s\n" % (
            self.year,
            self.month,
            monthToCode[self.month],
            self.expiration.strftime("%B, %d %Y (%A)"),
        )
        s += (
            "Cboe data: %i days" % len(self.cboeData)
            if self.cboeData is not None
            else "No data downloaded yet"
        )
        return s


if __name__ == "__main__":
    print("testing vix futures")

    year = 2012
    month = 12

    f = Future(year, month)
    f.getCboeData()
    print(f)
