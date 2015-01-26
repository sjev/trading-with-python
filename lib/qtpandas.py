'''
Easy integration of DataFrame into pyqt framework

Copyright: Jev Kuznetsov
Licence: BSD

'''
from PyQt4.QtCore import (QAbstractTableModel,Qt,QVariant,QModelIndex,SIGNAL)
from PyQt4.QtGui import (QApplication,QDialog,QVBoxLayout, QHBoxLayout, QTableView, QPushButton,
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

    def setData(self,index,value, role=Qt.EditRole):
          
        if index.isValid():
            row,column = index.row(), index.column()
            dtype = self.df.dtypes.tolist()[column] # get column dtype        
            
            if np.issubdtype(dtype,np.float):
                val,ok = value.toFloat()
            elif np.issubdtype(dtype,np.int):
                val,ok = value.toInt()
            else:
                val = value.toString()
                ok = True
            
            if ok:
                self.df.iloc[row,column] = val
                return True                
            
        return False
  
    def flags(self, index):
        if not index.isValid():
            return Qt.ItemIsEnabled
        return Qt.ItemFlags(
                QAbstractTableModel.flags(self, index)|
                Qt.ItemIsEditable)  
  
    def appendRow(self, index, data=0):
        self.df.loc[index,:] = data
        self.signalUpdate()
      
    def deleteRow(self, index):
        idx = self.df.index[index]
        #self.beginRemoveRows(QModelIndex(), index,index)
        #self.df = self.df.drop(idx,axis=0)
        #self.endRemoveRows()
        #self.signalUpdate()
  
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
            self.df = self.df.sort(columns=self.df.columns[nCol], ascending=True)
        elif order == Qt.DescendingOrder:
            self.df = self.df.sort(columns=self.df.columns[nCol], ascending=False)          
          
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

        Action = menu.addAction("delete row")
        Action.triggered.connect(self.deleteRow)

        menu.exec_(event.globalPos())

    def deleteRow(self):
        print "Action triggered from " + self.name
        
        print 'Selected rows:'
        for idx in self.selectionModel().selectedRows():
            print idx.row()
           # self.model.deleteRow(idx.row())
            


class DataFrameWidget(QWidget):
    ''' a simple widget for using DataFrames in a gui '''
    def __init__(self,name='DataFrameTable1', parent=None):
        super(DataFrameWidget,self).__init__(parent)
        self.name = name
        
        self.dataModel = DataFrameModel()
        self.dataModel.setDataFrame(DataFrame())
        
        self.dataTable = QTableView()
        #self.dataTable.setSelectionBehavior(QAbstractItemView.SelectRows)
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
        
    def insertRow(self,index, data=None):
        self.dataModel.appendRow(index,data)
        
#-----------------stand alone test code

def testDf():
    ''' creates test dataframe '''
    data = {'int':[1,2,3],'float':[1./3,2.5,3.5],'string':['a','b','c'],'nan':[np.nan,np.nan,np.nan]}
    return DataFrame(data, index=Index(['AAA','BBB','CCC']))[['int','float','string','nan']]


class Form(QDialog):
    def __init__(self,parent=None):
        super(Form,self).__init__(parent)
         
        df = testDf() # make up some data
        self.table = DataFrameWidget(parent=self)
        self.table.setDataFrame(df)
        #self.table.resizeColumnsToContents()
        self.table.fitColumns()
        self.table.setFormat({'float': '%.2f'})
        
        
        #buttons
       #but_add = QPushButton('Add')
        but_test = QPushButton('Test')
        but_test.clicked.connect(self.testFcn)
        hbox = QHBoxLayout()
        #hbox.addself.table(but_add)
        hbox.addWidget(but_test)                
                     
        layout = QVBoxLayout()
        layout.addWidget(self.table)
        layout.addLayout(hbox)
        
        self.setLayout(layout)
        
    def testFcn(self):
        print 'test function'
        self.table.insertRow('foo')
        
if __name__=='__main__':
    import sys
    import numpy as np
    
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()
    

        
        

        