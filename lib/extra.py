'''
Created on Apr 28, 2013
Copyright: Jev Kuznetsov
License: BSD
'''

import sys
import os
import pandas as pd

class ProgressBar:
    def __init__(self, iterations):
        self.iterations = iterations
        self.prog_bar = '[]'
        self.fill_char = '*'
        self.width = 50
        self.__update_amount(0)

    def animate(self, iteration):
        print('\r', self, end='')
        sys.stdout.flush()
        self.update_iteration(iteration + 1)

    def update_iteration(self, elapsed_iter):
        self.__update_amount((elapsed_iter / float(self.iterations)) * 100.0)
        self.prog_bar += '  %d of %s complete' % (elapsed_iter, self.iterations)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) // 2) - len(str(percent_done))
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])

    def __str__(self):
        return str(self.prog_bar)
    
def getSpyHoldings(dataDir):
    ''' get SPY holdings from the net, uses temp data storage to save xls file '''

    import urllib.request, urllib.parse, urllib.error
    
    dest = os.path.join(dataDir,"spy_holdings.xls")
    
    if os.path.exists(dest):
        print('File found, skipping download')
    else:
        print('saving to', dest)
        urllib.request.urlretrieve ("https://www.spdrs.com/site-content/xls/SPY_All_Holdings.xls?fund=SPY&docname=All+Holdings&onyx_code1=1286&onyx_code2=1700",
                             dest) # download xls file and save it to data directory
        
    # parse
    import xlrd # module for excel file reading
    wb = xlrd.open_workbook(dest) # open xls file, create a workbook
    sh = wb.sheet_by_index(0) # select first sheet
    
    
    data = {'name':[], 'symbol':[], 'weight':[],'sector':[]}
    for rowNr  in range(5,505): # cycle through the rows
        v = sh.row_values(rowNr) # get all row values
        data['name'].append(v[0])
        data['symbol'].append(v[1]) # symbol is in the second column, append it to the list
        data['weight'].append(float(v[2]))
        data['sector'].append(v[3])
      
    return  pd.DataFrame(data)    
    
def setNotebookStyle():
    """ 
    
    set notebook output styles 

    for pandas options see `docs <http://pandas.pydata.org/pandas-docs/stable/options.html?highlight=max_rows#list-of-options>`_
    
    
    """
    import matplotlib.pyplot as plt
    plt.style.use('ggplot')

    # bigger fitures
    import matplotlib
    matplotlib.rcParams['figure.figsize'] = [12, 8]

    import pandas as pd
    pd.options.display.max_rows = 10
    
    pd.options.display.precision = 2 # two-digit precision, otherwise some tables will
                                 # not fit on the screen

