# -*- coding: utf-8 -*-
"""
Created on Fri Dec 09 18:41:08 2011

@author: jev
"""



import sqlite3 as db
#import sys, os
 

class Symbols(object):
    ''' class for managing a group of spreads through sqlite '''
    def __init__(self,fName='spreads.db'):
        self.con = db.connect(fName)
        self.cur = self.con.cursor()
         
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
    
    def printTable(self,table):
        
        q = "SELECT * FROM "+table # insecure, but ? does not work here
        self.cur.execute(q)
        print '-'*10+table+"-"*10
        for row in self.cur:
            print row 
   
    def _testFcn(self):
        self.sql("insert into tbl_symbols ")         
    
    def showTables(self):
        self.cur.execute("select name from sqlite_master where type='table' ")
        res = self.cur.fetchall()
        for row in res:
            print row[0]
    
    def __del__(self):
        self.con.close()




        
if __name__=='__main__':
    g = Symbols()
    g.initDb()
    g.showTables()
    g.addSymbol('SPY')
    g.addSymbol('XYZ')
    g.printTable('tbl_symbols')
    