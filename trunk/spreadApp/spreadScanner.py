'''
Created on 12 dec. 2011
Copyright: Jev Kuznetsov
License: BSD
'''

import sys, os

__version__ = "0.0.5"

from PyQt4.QtCore import (Qt, SIGNAL)
from PyQt4.QtGui import *

import widgets.ui_symbolChooser
from tradingWithPython.lib.yahooFinance import getScreenerSymbols
import qrc_resources
from tradingWithPython import readBiggerScreener
from tradingWithPython.lib.qtpandas import DataFrameWidget, DataFrameModel
from tradingWithPython.lib.yahooFinance import HistData
from tradingWithPython.lib.widgets import PlotWindow
from tradingWithPython.lib.classes import Spread
from tradingWithPython.lib.functions import returns

import matplotlib.pyplot as plt
from pandas import DataFrame,Index

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

class DataTable(DataFrameWidget):
    ''' main data table '''
    def __init__(self,parent=None):
        super(DataTable,self).__init__(parent)
        self.histData = HistData(dataFile)
        self.histData.startDate = dataStartDate
        self.symbols = []
        self.reference = 'SPY'
        self.fitColumns()
        self.dataModel.setFormat({'last':'%.2f','micro':'%.2f','macro':'%.2f','corr':'%.2f'})
        
    def setSymbols(self,symbols,reference='SPY'):
        self.symbols = symbols
        self.reference = reference
        self.getData(self.symbols+[self.reference])
        
        df = DataFrame(index=['last','micro','macro'])
        for symbol in self.symbols:
            sp = Spread(symbols =[symbol,self.reference], histClose=self.histData.df[[symbol,self.reference]])
            
            df[sp.name] = sp.calculateStatistics()
            
        self.df = df.T
        
        self.setDataFrame(self.df)   
        
    def getData(self,symbols ):
        ''' process spreads, update data if needed '''
        self.histData.loadSymbols(symbols)
    
    def testFcn(self):
        self.df = readBiggerScreener('CointPairs.csv')
        self.setDataFrame(self.df)
       

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

        Action = menu.addAction("print selected rows")
        Action.triggered.connect(self.printName)

        menu.exec_(event.globalPos())

    def printName(self):
        print "Action triggered from " + self.name
        
        print 'Selected rows:'
        for idx in self.selectionModel().selectedRows():
            print idx.row()



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
        
        # general vars
        self.filename = None
        self.actions = {} # actions list
        
        # build symbols dock
#        dock = QDockWidget("Symbols",self)
#        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
#        self.symbolChooser =SymbolChooser()
#        dock.setWidget(self.symbolChooser)
#        self.addDockWidget(Qt.LeftDockWidgetArea, dock)
#       
        #fill central area
        #self.dataTable = DataTable()
        self.dataTable = BiggerSpreads()
        self.setCentralWidget(self.dataTable)
        
        #create actions
        self.actions['loadScreener'] = self.createAction("Load symbols",self.loadScreenerSymbols,icon="fileopen")
        self.actions['plotHistData'] = self.createAction("Plot price",self.plotHistData)
        self.actions['test'] = self.createAction("Test",self._testFcn)

        
        #set app menu
        self.createMenu()
        self.createToolbars()
        
        
        #quick init
        self._quickInit()
       
        self.resize(800,600)
   
    def _quickInit(self):
        #self.loadScreenerSymbols('test_set.csv')
        
        #symbols = ['IWM','XLE','XLF']
        #self.dataTable.setSymbols(symbols)
        
        self.dataTable.loadSpreads('CointPairs.csv')
        #self.dataTable.testFcn()
        
    def createMenu(self):
        menu = self.menuBar()
        menu.addMenu("File").addAction(self.actions['loadScreener'])
    
    def createToolbars(self):
        t = self.addToolBar("File")
        t.setObjectName("FileToolBar")  
        t.addAction(self.actions['loadScreener']) 
        t.addAction(self.actions['plotHistData'])
        t.addAction(self.actions['test'])
        
    def loadScreenerSymbols(self, fName = None):
        ' load symbols from yahoo screener csv'
        
        if fName is None:
            formats = ['*.csv']
            path = (os.path.dirname(self.filename)
                   if self.filename is not None else ".")
            
            fName = unicode(QFileDialog.getOpenFileName(self,"Open yahoo screener file",path,
                                                        "CSV files ({0})".format(" ".join(formats))))
        
        if fName:
            symbols = getScreenerSymbols(fName)
            self.symbolChooser.listSymbols.clear()
            self.symbolChooser.listSymbols.addItems(symbols)
            self.filename = fName
    
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
    
    def _testFcn(self):
        print 'test function'
        self.dataTable.dataModel.signalUpdate()
        
               
    
def main():
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()


main()
        