# -*- coding: utf-8 -*-
"""

"""



import sqlite3 as lite
import sys
from PyQt4.QtCore import (QAbstractTableModel,Qt,QVariant,QModelIndex, SIGNAL)
from PyQt4.QtGui import (QApplication,QDialog,QVBoxLayout, QTableView, QWidget, QHeaderView)


#import sys, os

def initDb(dbName):
    '''reset database '''
    print 'Resetting ' , dbName
    con = lite.connect(dbName)
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



class SqliteTableModel(QAbstractTableModel):
    ''' base class for interfacing to sqlite db'''
    def __init__(self,dbConnection,tableName,parent=None):
        super(SqliteTableModel,self).__init__(parent)
        self._con = dbConnection
        self._table = tableName
        self._data = []
        self._header = []
        self._reload()
  
        
        
    def _reload(self):
        ' reload all data'
        q = "SELECT * FROM %s " % self._table
        cur = self._con.cursor()
        cur.execute(q)
        
        self._data = []
        for row in cur:
            self._data.append([])
            curr = self._data[-1]
            for elm in row:
                curr.append(elm)
        
        cur.execute("PRAGMA table_info(%s)" % self._table)
        for c in cur:
            self._header.append(c[1])    
                
    def __repr__(self):
        return str(self._header)+'\n'+str.join('\n',[ str(row) for row in self._data])

    
    

class Symbols(QAbstractTableModel):
    ''' class for managing a group of spreads through sqlite '''
    def __init__(self,dbConnection,tableName):
        
        self.tblName = tableName # name of the database table
        self.con = dbConnection
        
        self.cur = self.con.cursor()
        self.data = []
         
    def sql(self,query):
        cur = self.con.cursor()
        cur.execute(query)
        return cur.fetchall()
        
    
    def initDb(self):
        self.cur.execute("DROP TABLE IF EXISTS tbl_symbols")
        self.cur.execute("""CREATE TABLE tbl_symbols (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT, 
                    secType TEXT DEFAULT 'STK',
                    currency TEXT DEFAULT 'USD',
                    exchange TEXT DEFAULT 'SMART',
                    active BOOLEAN DEFAULT 1)""")
        
        
        self.con.commit()
        
   
    def addSymbol(self, symbol):
        t = (symbol,)
        self.cur.execute("INSERT INTO tbl_symbols (symbol) VALUES(?) ",t)   
    
    
    def load(self):
        ''' reload full table from db '''
        q = "SELECT * FROM tbl_symbols "
        self.cur.execute(q)
        
        self.data = []
        for row in self.cur:
            self.data.append([])
            curr = self.data[-1]
            for elm in row:
                curr.append(elm)
                
    
    
    def printTable(self):
        self.load()
        print '-'*10
        print self.data
   
    def _testFcn(self):
        self.sql("insert into tbl_symbols ")         
    
    def showTables(self):
        self.cur.execute("select name from sqlite_master where type='table' ")
        res = self.cur.fetchall()
        for row in res:
            print row[0]
    
    def __del__(self):
        self.con.close()


#----------------test code
class Form(QDialog):
    def __init__(self, parent=None):
        super(Form, self).__init__(parent)
        self.resize(640,480)
        self.setWindowTitle('Model test')
       
        model = SqliteTableModel(con,'tbl_symbols')
        table = QTableView()
        table.setModel(model)
        
        lay = QVBoxLayout()
        lay.addWidget(table)
        self.setLayout(lay)

def startGui():
    app = QApplication(sys.argv)
    form = Form()
    form.show()
    app.exec_()

def testModel():
    ' simple model test, without gui'
    m  = SqliteTableModel(con,'tbl_symbols')
    print m
        
if __name__=='__main__':
    
    dbName = 'testDb'
    
    #initDb(dbName)
    con = lite.connect(dbName)
    cur = con.cursor()
    cur.execute("select name from sqlite_master where type='table' ")
    
    for row in cur:
        print row[0]

    
    testModel()
    #startGui()
    
   
    