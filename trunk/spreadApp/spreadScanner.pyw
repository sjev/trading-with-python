'''
Created on 12 dec. 2011
Copyright: Jev Kuznetsov
License: BSD
'''

import sys, os

__version__ = "0.1.0"

from PyQt4.QtCore import (Qt, SIGNAL)
from PyQt4.QtGui import *
import platform

import widgets.ui_symbolChooser
from tradingWithPython.lib.yahooFinance import getScreenerSymbols
import qrc_resources
from tradingWithPython import readBiggerScreener
from tradingWithPython.lib.qtpandas import DataFrameWidget, DataFrameModel
from tradingWithPython.lib.widgets import PlotWindow
from tradingWithPython.lib.classes import Spread
from tradingWithPython.lib.functions import returns

from widgets.spread import SpreadWidget

import numpy as np
import matplotlib.pyplot as plt
from pandas import DataFrame,Index,Series

#---------globals
dataFile = 'yahooData.csv'
dataStartDate = (2010,1,1)
#--------classes

class SymbolChooser(QWidget,widgets.ui_symbolChooser.Ui_Form):
    ''' symbol chooser widget '''
    def __init__(self,parent=None):
        super(SymbolChooser,self).__init__(parent)
        self.setupUi(self)
    
    def symbols(self):
        symbols = []
        for i in range(self.listSymbols.count()):
            symbols.append(str(self.listSymbols.item(i).text()))
        return symbols


       

class SpreadViewModel(DataFrameModel):
    """ modified version of the model to hack around sorting issue"""
    def __init__(self,parent=None):
        super(SpreadViewModel,self).__init__(parent=None)
        
    def sort(self,nCol,order):  
        
        self.layoutAboutToBeChanged.emit()
        
        col = self.df[self.df.columns[nCol]].values.tolist()
        
        #create indexed list, sort, rebuild complete data frame 8(
        di = [(d,i) for i,d in enumerate(col)]
        
        if order == Qt.AscendingOrder:
            idx = [i for d,i in sorted(di)]
        elif order == Qt.DescendingOrder:
            idx = [i for d,i in sorted(di,reverse=True)]
            
        data = self.df.values[idx,:]
        cols = self.df.columns
        # rebuild the whole thing
        self.df = DataFrame(data=data, columns=cols, index = Index(range(len(idx))))
          
        self.layoutChanged.emit()
        
        


class SpreadView(QTableView):
    """ extended table view """
    def __init__(self,name='TableView1', parent=None):
        super(SpreadView,self).__init__(parent)
        self.name = name
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
    
          
    def contextMenuEvent(self, event):
        menu = QMenu(self)
       
        Action = menu.addAction("Show spread")
        Action.triggered.connect(self.showSpread)

        menu.exec_(event.globalPos())

    def showSpread(self):
        """ open a spread window """
        for idx in self.selectionModel().selectedRows():
            row = self.selectionModel().model().df.ix[idx.row(),:]
            symbols = [row['StockA'],row['StockB']]
            spread = Spread(symbols)
            spread.setShares(Series({row['StockA']:1,row['StockB']:-row['Price Ratio']}))
            spreadWindow = SpreadWindow(self)
            spreadWindow.setSpread(spread)
            
            spreadWindow.show()
            

class SpreadWindow(QMainWindow):
    def __init__(self,parent=None):
        super(SpreadWindow,self).__init__(parent)
        self.resize(640,600)
        self.setWindowTitle('Spread test')
        
        self.widget = SpreadWidget(self)
        self.setCentralWidget(self.widget)
        
        self.spread = None
        
    def setSpread(self,spread):
        
        self.spread = spread
        self.setWindowTitle(spread.name)
        self.widget.setSpread(self.spread)

class BiggerSpreads(QWidget):
    """ class for working with spreads from screener """
    def __init__(self, parent=None):
        super(QWidget,self).__init__(parent)
        self.name = 'bigger spreads'
        
        self.df = DataFrame() # main data container
        self.dataModel = SpreadViewModel()
        self.dataModel.setDataFrame(self.df)
        
        self.dataTable = SpreadView()
        self.dataTable.setSortingEnabled(True)   
        
        self.dataTable.setModel(self.dataModel)
        self.dataModel.signalUpdate()
        
                 
        layout = QVBoxLayout()
        layout.addWidget(self.dataTable)
        self.setLayout(layout)     
    
    def loadSpreads(self,fName):
        self.df = readBiggerScreener(fName)
        self.dataModel.setDataFrame(self.df)
        #self.dataTable.resizeColumnsToContents()      
        self.dataTable.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        self.setWindowTitle('Spread Detective [alpha]')
        
        # general vars
        self.filename = None
        self.actions = {} # actions list
        
        #fill central area
        self.dataTable = BiggerSpreads()
        self.setCentralWidget(self.dataTable)
        
        #create actions
        self.actions['loadScreener'] = self.createAction("Load symbols",self.loadScreenerSymbols,icon="fileopen")
        self.actions['helpAbout'] = self.createAction("About",self.helpAbout)
        #self.actions['test'] = self.createAction("Test",self._testFcn)
        
        #set app menu
        self.createMenu()
        self.createToolbars()
        
        #quick init
        self._quickInit()
        self.resize(800,600)
   
    def _quickInit(self):
        testFile = 'CointPairs_test.csv'
        if os.path.exists(testFile):
            self.dataTable.loadSpreads(testFile)
        
    def createMenu(self):
        menu = self.menuBar()
        menu.addMenu("File").addAction(self.actions['loadScreener'])
        menu.addMenu("Help").addAction(self.actions['helpAbout'])
    
    def createToolbars(self):
        t = self.addToolBar("File")
        t.setObjectName("FileToolBar")  
        t.addAction(self.actions['loadScreener']) 
        
    def loadScreenerSymbols(self, fName = None):
        ' load symbols from yahoo screener csv'
        
        if fName is None:
            formats = ['*.csv']
            path = (os.path.dirname(self.filename)
                   if self.filename is not None else ".")
            
            fName = unicode(QFileDialog.getOpenFileName(self,"Open screener results",path,
                                                        "CSV files ({0})".format(" ".join(formats))))
        
        if fName:
            self.dataTable.loadSpreads(fName)
    
    def plotHistData(self):
        ''' plot internal historic data '''
        plt = PlotWindow(self)
        plt.plot(self.dataTable.histData.df)
        plt.show()        
    
    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/{0}.png".format(icon)))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action
    
    
    def helpAbout(self):
        QMessageBox.about(self, "Spread Detective - About",
                """<b>Spread Detective</b> v {0}
                <p>Copyright &copy; 2011 Jev Kuznetsov. 
                All rights reserved.
                <p>
                Copyright &copy; 2008-2011 AQR Capital Management, LLC All rights reserved.
                <p>
                Copyright &copy; 2011 Wes McKinney and pandas developers All rights reserved.
                
                <p>
                
                THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS
                "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
                LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
                A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
                OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
                SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
                LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
                DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
                THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
                (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
                OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
                
                
                <p>Python {1} """.format(__version__, platform.python_version()))

    
    
    def _testFcn(self):
        print 'test function'
        self.dataTable.dataModel.signalUpdate()
        
               
    
def main():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


main()
        