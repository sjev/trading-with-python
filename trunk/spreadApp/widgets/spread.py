'''
Created on 30 dec. 2011
Copyright: Jev Kuznetsov
License: BSD
'''

#from PyQt4.QtCore import (SIGNAL,SLOT)
from PyQt4.QtGui import *

import tradingWithPython.lib.yahooFinance as yahooFinance
from tradingWithPython.lib.widgets import MatplotlibWidget
from tradingWithPython.lib.qtpandas import DataFrameWidget
#from pandas import DataFrame
from tradingWithPython import Spread
import numpy as np


class SpreadWidget(QWidget):
    def __init__(self,parent=None):
        super(SpreadWidget,self).__init__(parent)
        
      
        lay = QVBoxLayout()
        self.spreadPlot = MatplotlibWidget(self)
        self.spreadTable = DataFrameWidget(self)
         
        lay.addWidget(self.spreadPlot)
        lay.addWidget(self.spreadTable)
        self.setLayout(lay)
        
    def setSpread(self,spread):
        """ show spread in the widget """
        self.spread = spread
        
        #self.parent.setWindowTitle(self.spread.name)
        x = np.asarray(self.spread.value.index)
        y = self.spread.value
        
        self.spreadPlot.plot(x,y,'r-')
        self.spreadPlot.fig.autofmt_xdate()
        self.spreadPlot.update()
        
        
        #fill table
        cols =self.spread.params.columns
        fmt = dict(zip(cols,['%.2f']*len(cols)))
        self.spreadTable.setFormat(fmt)
        self.spreadTable.setDataFrame(self.spread.params)
        self.spreadTable.fitColumns()



#-----------------------------test functions--------------------------
class Test(QWidget):
    def __init__(self,parent=None):
        super(Test,self).__init__(parent)
        #self.parent = parent
        tv = DataFrameWidget(self)
        lay = QVBoxLayout(self)
        lay.addWidget(tv)
        self.setLayout(lay)
    def setSpread(self,spread):
        pass
        self.spread = spread
        
        #self.parent.setWindowTitle(self.spread.name)

class Form(QMainWindow):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.resize(640,600)
        self.setWindowTitle('Spread test')
        
        self.widget = SpreadWidget(self)
        #self.widget = Test(self)
        self.setCentralWidget(self.widget)
        
        self.initSpread()
        
    
    def initSpread(self):
        symbols = ['SPY','IWM']
        y = yahooFinance.HistData('temp.csv')
        y.startDate = (2007,1,1)
        df = y.loadSymbols(symbols,forceDownload=False)
        self.spread = Spread(symbols, bet=100, histClose=df)
        
        #self.spread =Spread(symbols)
        self.widget.setSpread(self.spread)
       
        
def startGui():
    
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()

if __name__ == "__main__":
    import sys
    
   
    
    startGui()
    print 'All done'
    