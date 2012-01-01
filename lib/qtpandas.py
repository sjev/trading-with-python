'''
Easy integration of DataFrame into pyqt framework

Copyright: Jev Kuznetsov
Licence: BSD

'''
from PyQt4.QtCore import (QAbstractTableModel,Qt,QVariant,QModelIndex,SIGNAL)
from PyQt4.QtGui import (QApplication,QDialog,QVBoxLayout, QTableView, 
                         QWidget,QTableWidget, QHeaderView, QFont,QMenu,QAbstractItemView)

from pandas import DataFrame, Index




class DataFrameModel(QAbstractTableModel):
    ''' data model for a DataFrame class '''
    def __init__(self,parent=None):
        super(DataFrameModel,self).__init__(parent)
        self.df = DataFrame()
        self.columnFormat = {} # format columns 
    
    def setFormat(self,fmt):
        """ 
        set string formatting for the output 
        example : format = {'close':"%.2f"}
        """
        
        self.columnFormat = fmt
         
    def setDataFrame(self,dataFrame):
        self.df = dataFrame
        self.signalUpdate()
    
    def signalUpdate(self):
        ''' tell viewers to update their data (this is full update, not efficient)'''
        self.layoutChanged.emit()
    
    def __repr__(self):
        return str(self.df) 
  
    #------------- table display functions -----------------     
    def headerData(self,section,orientation,role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
          
        if orientation == Qt.Horizontal:
            try:
                return self.df.columns.tolist()[section]
            except (IndexError, ):
                return QVariant()
        elif orientation == Qt.Vertical:
            try:
                #return self.df.index.tolist()
                return str(self.df.index.tolist()[section])
            except (IndexError, ):
                return QVariant()
            
    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        
        if not index.isValid():
            return QVariant()
        
        col = self.df.ix[:,index.column()] # get a column slice first to get the right data type
        elm = col[index.row()]
        #elm = self.df.ix[index.row(),index.column()]
        
        if self.df.columns[index.column()] in self.columnFormat.keys():
            return QVariant(self.columnFormat[self.df.columns[index.column()]] % elm )
        else:
            return QVariant(str(elm))
    
    def sort(self,nCol,order):  
        
        self.layoutAboutToBeChanged.emit()
        if order == Qt.AscendingOrder:
            self.df = self.df.sort(column=self.df.columns[nCol], ascending=True)
        elif order == Qt.DescendingOrder:
            self.df = self.df.sort(column=self.df.columns[nCol], ascending=False)          
          
        self.layoutChanged.emit()
        
       
      
    def rowCount(self, index=QModelIndex()):
        return self.df.shape[0]
    
    def columnCount(self, index=QModelIndex()):
        return self.df.shape[1] 


class TableView(QTableView):
    """ extended table view """
    def __init__(self,name='TableView1', parent=None):
        super(TableView,self).__init__(parent)
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


class DataFrameWidget(QWidget):
    ''' a simple widget for using DataFrames in a gui '''
    def __init__(self,name='DataFrameTable1', parent=None):
        super(DataFrameWidget,self).__init__(parent)
        self.name = name
        
        self.dataModel = DataFrameModel()
        self.dataModel.setDataFrame(DataFrame())
        
        self.dataTable = QTableView()
        self.dataTable.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.dataTable.setSortingEnabled(True)
        
        self.dataTable.setModel(self.dataModel)
        self.dataModel.signalUpdate()
        
        #self.dataTable.setFont(QFont("Courier New", 8)) 
                
        layout = QVBoxLayout()
        layout.addWidget(self.dataTable)
        self.setLayout(layout)
    
    
    
    def setFormat(self,fmt):
        """ set non-default string formatting for a column """
        for colName, f in fmt.iteritems():
            self.dataModel.columnFormat[colName]=f
    
    def fitColumns(self):
        self.dataTable.horizontalHeader().setResizeMode(QHeaderView.Stretch)
        
    def setDataFrame(self,df):
        self.dataModel.setDataFrame(df)
            
    
    def resizeColumnsToContents(self):
        self.dataTable.resizeColumnsToContents()    
        
#-----------------stand alone test code

def testDf():
    ''' creates test dataframe '''
    data = {'int':[1,2,3],'float':[1./3,2.5,3.5],'string':['a','b','c'],'nan':[np.nan,np.nan,np.nan]}
    return DataFrame(data, index=Index(['AAA','BBB','CCC']))[['int','float','string','nan']]


class Form(QDialog):
    def __init__(self,parent=None):
        super(Form,self).__init__(parent)
         
        df = testDf() # make up some data
        widget = DataFrameWidget(parent=self)
        widget.setDataFrame(df)
        #widget.resizeColumnsToContents()
        widget.fitColumns()
        widget.setFormat({'float': '%.2f'})
        
                     
        layout = QVBoxLayout()
        layout.addWidget(widget)
        self.setLayout(layout)
        
if __name__=='__main__':
    import sys
    import numpy as np
    
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()
    

        
        

        