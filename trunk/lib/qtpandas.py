'''
Easy integration of DataFrame into pyqt framework

@author: jev
'''
from PyQt4.QtCore import (QAbstractTableModel,Qt,QVariant,QModelIndex, SIGNAL,SLOT,QString)
from PyQt4.QtGui import (QApplication,QMessageBox,QDialog,QVBoxLayout,QHBoxLayout,QDialogButtonBox,
                         QTableView, QPushButton,QWidget,QLabel,QLineEdit,QGridLayout)


from pandas import DataFrame, Index



class DataFrameModel(QAbstractTableModel):
    ''' data model for a DataFrame class '''
    def __init__(self, dataFrame):
        super(DataFrameModel,self).__init__()
        self.df = dataFrame
         
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
                return self.df.index.tolist()[section]
            except (IndexError, ):
                return QVariant()
            
    def data(self, index, role=Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return QVariant()
        
        if (not index.isValid() or not (0 <= index.row() < len(self.df))):
            return QVariant()
        
        return QVariant(str(self.df.ix[index.row(),index.column()]))
      
    def rowCount(self, index=QModelIndex()):
        return self.df.shape[0]
    
    def columnCount(self, index=QModelIndex()):
        return self.df.shape[1] 


class DataFrameWidget(QWidget):
    ''' a simple widget for using DataFrames in a gui '''
    def __init__(self,dataFrame, parent=None):
        super(DataFrameWidget,self).__init__(parent)
        
        self.dataModel = DataFrameModel(dataFrame)
        
        self.dataTable = QTableView()
        self.dataTable.setModel(self.dataModel)
        
        layout = QVBoxLayout()
        layout.addWidget(self.dataTable)
        self.setLayout(layout)
        
        
#-----------------stand alone test code

class Form(QDialog):
    def __init__(self,parent=None):
        super(Form,self).__init__(parent)
        self.resize(640,480)
        
        data = {'int':[1,2,3],'float':[1.5,2.5,3.5],'string':['a','b','c'],'nan':[np.nan,np.nan,np.nan]}
        df = DataFrame(data, index=Index(['AAA','BBB','CCC']))[['int','float','string','nan']]
        
        layout = QVBoxLayout()
        layout.addWidget(DataFrameWidget(df))
        self.setLayout(layout)
        
if __name__=='__main__':
    import sys
    import numpy as np
    
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()
    

        
        

        