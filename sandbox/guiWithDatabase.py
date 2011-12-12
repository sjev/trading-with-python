
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
from future_builtins import *

import os
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtSql import (QSqlDatabase, QSqlQuery, QSqlRelation,
        QSqlRelationalDelegate, QSqlRelationalTableModel, QSqlTableModel)



import sqlite3 as db

dbName = 'test.db'


def initDb():
    '''reset database '''
    con = db.connect(dbName)
    cur = con.cursor()
    
    cur.execute("DROP TABLE IF EXISTS tbl_symbols")
    cur.execute("""CREATE TABLE tbl_symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT, 
                    secType TEXT DEFAULT 'STK',
                    currency TEXT DEFAULT 'USD',
                    exchange TEXT DEFAULT 'SMART',
                    active BOOLEAN DEFAULT 1)""")
    
    
    symbols = ('AAA','BBB','CCC')
    for symbol in symbols:
        cur.execute("INSERT INTO tbl_symbols (symbol) VALUES(?) ",(symbol,))
    
    con.commit()
    

#-----------------
class MainForm(QDialog):
    def __init__(self):
        super(MainForm, self).__init__()
        
        self.model = QSqlTableModel(self)
        self.model.setTable('tbl_symbols')
        self.model.select()
        
        self.view = QTableView()
        self.view.setModel(self.model)
        self.view.horizontalHeader().setResizeMode(QHeaderView.Stretch)

        addButton = QPushButton("&Add")
        deleteButton = QPushButton("&Delete")
        
        buttonLayout = QVBoxLayout()
        buttonLayout.addWidget(addButton)
        buttonLayout.addWidget(deleteButton)
        buttonLayout.addStretch()
        
        lay = QHBoxLayout()
        lay.addWidget(self.view)
        lay.addLayout(buttonLayout)
        self.setLayout(lay)
        
        self.connect(addButton, SIGNAL("clicked()"), self.addRecord)
        self.connect(deleteButton, SIGNAL("clicked()"), self.deleteRecord)
     
     
    def addRecord(self):
        row = self.model.rowCount()
        self.model.insertRow(row)
        index = self.model.index(row, 1)
        self.view.setCurrentIndex(index)
        self.view.edit(index)
    
    def deleteRecord(self):
        index = self.view.currentIndex()
        if not index.isValid():
            return
        #QSqlDatabase.database().transaction()
        record = self.model.record(index.row())
        self.model.removeRow(index.row())
        self.model.submitAll()    
        
def main():
    app = QApplication(sys.argv)
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(dbName)
    if not db.open():
        QMessageBox.warning(None, "Asset Manager",
            QString("Database Error: %1")
            .arg(db.lastError().text()))
        sys.exit(1)

    form = MainForm()
    form.show()
    app.exec_()
    del form
    del db
#initDb()
main()