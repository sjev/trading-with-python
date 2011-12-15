# -*- coding: utf-8 -*-
"""
Created on Wed Dec 14 19:47:02 2011

@author: jev
"""


from PyQt4.QtGui import *
from PyQt4.QtCore import *

from guiqwt.plot import CurveDialog
from guiqwt.builder import make
import sys

import numpy as np  

class MainForm(QDialog):
    def __init__(self,parent=None):
        super(MainForm,self).__init__(parent)
        self.resize(200,200)
        
        but = QPushButton()
        but.setText('Create plot')
        self.connect(but,SIGNAL('clicked()'),self.testFcn)
        
        lay = QVBoxLayout()
        lay.addWidget(but)
        self.setLayout(lay)
        
    def testFcn(self):
        x = np.linspace(0, 100, 1000)
       
        y = (np.random.rand(len(x))-0.5).cumsum()
    
        curve = make.curve(x, y, "ab", "b")
        range = make.range(0, 5)
        
        disp2 = make.computations(range, "TL",
                                  [(curve, "min=%.5f", lambda x,y: y.min()),
                                   (curve, "max=%.5f", lambda x,y: y.max()),
                                   (curve, "avg=%.5f", lambda x,y: y.mean())])
        legend = make.legend("TR")
        items = [ curve, range, disp2, legend]
        
        win = CurveDialog(edit=False, toolbar=True, parent=self)
        plot = win.get_plot()
        for item in items:
            plot.add_item(item)
        win.show()
        
        
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainForm()
    form.show()
    app.exec_()
