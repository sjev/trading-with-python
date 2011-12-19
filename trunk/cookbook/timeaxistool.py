#!/usr/bin/env python

#############################################################################
##
## This file was adapted from Taurus, a Tango User Interface Library
## 
## http://www.tango-controls.org/static/taurus/latest/doc/html/index.html
##
## Copyright 2011 CELLS / ALBA Synchrotron, Bellaterra, Spain
## 
## Taurus is free software: you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation, either version 3 of the License, or
## (at your option) any later version.
## 
## Taurus is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
## 
## You should have received a copy of the GNU Lesser General Public License
## along with Taurus.  If not, see <http://www.gnu.org/licenses/>.
##
#############################################################################

"""Extension of :mod:`guiqwt.tools`"""



__docformat__ = 'restructuredtext'


from PyQt4 import Qt,Qwt5
from guiqwt.tools import CommandTool, QActionGroup, add_actions
from guiqwt.signals import SIG_ITEMS_CHANGED
from scales import DateTimeScaleEngine
from guiqwt.builder import make
from tradingWithPython.lib.yahooFinance import getHistoricData
import numpy as np
import time

df = getHistoricData('SPY',(2010,1,1))
x = df['adj_close'].index.tolist()
y = df['adj_close'].values


t = [time.mktime(el.timetuple()) for el in x]


          
class TimeAxisTool(CommandTool):
    """
    A tool that allows the user to change the type of scales to/from time mode.
    When a scale is in time mode, the values are interpreted as timestamps 
    (seconds since epoch)
    """
    def __init__(self, manager):
        super(TimeAxisTool, self).__init__(manager, "Time Scale",
                                            tip=None, toolbar_id=None)
        self.action.setEnabled(True)
                                 
    def create_action_menu(self, manager):
        """Create and return menu for the tool's action"""
        menu = Qt.QMenu()
        group = QActionGroup(manager.get_main())
        y_x = manager.create_action("y(x)", toggled=self.set_scale_y_x)
        y_t = manager.create_action("y(t)", toggled=self.set_scale_y_t)
        t_x = manager.create_action("t(x)", toggled=self.set_scale_t_x)
        t_t = manager.create_action("t(t)", toggled=self.set_scale_t_t)
        self.scale_menu = {(False, False): y_x, (False, True): y_t,
                           (True, False): t_x, (True, True): t_t}
        for obj in (group, menu):
           add_actions(obj, (y_x, y_t, t_x, t_t))
        return menu
    
    def _getAxesUseTime(self, item):
        """
        Returns a tuple (xIsTime, yIsTime) where xIsTime is True if the item's x
        axis uses a TimeScale. yIsTime is True if the item's y axis uses a Time
        Scale. Otherwise they are False.
        """
        plot = item.plot()
        if plot is None:
            return (False,False)
        xEngine = plot.axisScaleEngine(item.xAxis())
        yEngine = plot.axisScaleEngine(item.yAxis())
        return isinstance(xEngine, DateTimeScaleEngine), isinstance(yEngine, DateTimeScaleEngine)
         
    def update_status(self, plot):
        item = plot.get_active_item()
        active_scale = (False, False)
        if item is not None:
            active_scale = self._getAxesUseTime(item)
        for scale_type, scale_action in self.scale_menu.items():
            if item is None:
                scale_action.setEnabled(True)
            else:
                scale_action.setEnabled(True)
                if active_scale == scale_type:
                    scale_action.setChecked(True)
                else:
                    scale_action.setChecked(False)
                    
    def _setPlotTimeScales(self, xIsTime, yIsTime):
        plot = self.get_active_plot()
        if plot is not None:
            for axis,isTime in zip(plot.get_active_axes(), (xIsTime, yIsTime)):
                if isTime:
                    DateTimeScaleEngine.enableInAxis(plot, axis, rotation=-45)
                else:
                    DateTimeScaleEngine.disableInAxis(plot, axis)
            plot.replot()
            
        
    def set_scale_y_x(self, checked):
        if not checked:
            return
        self._setPlotTimeScales(False, False)
        
    def set_scale_t_x(self, checked):
        if not checked:
            return
        self._setPlotTimeScales(False, True)
    
    def set_scale_y_t(self, checked):
        if not checked:
            return
        self._setPlotTimeScales(True, False)
    
    def set_scale_t_t(self, checked):
        if not checked:
            return
        self._setPlotTimeScales(True, True)



def testTool(tool):
    from guiqwt.plot import CurveDialog
    import sys
    
    app = Qt.QApplication([])
    win = CurveDialog(edit=False, toolbar=True)
    
    x = np.arange(len(y))
    curve = make.curve(t, y, "ab", "b")
    plot=win.get_plot()
    plot.add_item(curve)
    
    win.add_tool(tool)
    
    win.show()
    win.exec_()
    
        
def test_timeAxis():
    testTool(TimeAxisTool)

if __name__ == "__main__":
    test_timeAxis()    