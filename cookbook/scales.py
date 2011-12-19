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

"""
scales.py: Custom scales
"""
__all__=["DateTimeScaleEngine", "DeltaTimeScaleEngine", "FixedLabelsScaleEngine", 
         "FancyScaleDraw", "TaurusTimeScaleDraw", "DeltaTimeScaleDraw", 
         "FixedLabelsScaleDraw"]

import numpy
from datetime import datetime, timedelta
from time import mktime
from PyQt4 import Qt, Qwt5

    
def _getDefaultAxisLabelsAlignment(axis, rotation):
    '''return a "smart" alignment for the axis labels depending on the axis
    and the label rotation

    :param axis: (Qwt5.QwtPlot.Axis) the axis
    :param rotation: (float) The rotation (in degrees, clockwise-positive)

    :return: (Qt.Alignment) an alignment
    '''
    if axis == Qwt5.QwtPlot.xBottom:
        if rotation == 0 : return Qt.Qt.AlignHCenter|Qt.Qt.AlignBottom
        elif rotation < 0: return Qt.Qt.AlignLeft|Qt.Qt.AlignBottom
        else:              return Qt.Qt.AlignRight|Qt.Qt.AlignBottom
    elif axis == Qwt5.QwtPlot.yLeft:
        if rotation == 0 : return Qt.Qt.AlignLeft|Qt.Qt.AlignVCenter
        elif rotation < 0: return Qt.Qt.AlignLeft|Qt.Qt.AlignBottom
        else:              return Qt.Qt.AlignLeft|Qt.Qt.AlignTop
    elif axis == Qwt5.QwtPlot.yRight:
        if rotation == 0 : return Qt.Qt.AlignRight|Qt.Qt.AlignVCenter
        elif rotation < 0: return Qt.Qt.AlignRight|Qt.Qt.AlignTop
        else:              return Qt.Qt.AlignRight|Qt.Qt.AlignBottom
    elif axis == Qwt5.QwtPlot.xTop:
        if rotation == 0 : return Qt.Qt.AlignHCenter|Qt.Qt.AlignTop
        elif rotation < 0: return Qt.Qt.AlignLeft|Qt.Qt.AlignTop
        else:              return Qt.Qt.AlignRight|Qt.Qt.AlignTop

class FancyScaleDraw(Qwt5.QwtScaleDraw):
    
        '''This is a scaleDraw with a tuneable palette and label formats'''
        def __init__(self, format = None, palette = None):
            Qwt5.QwtScaleDraw.__init__(self)
            self._labelFormat = format
            self._palette = palette
            
        def setPalette(self, palette):
            '''pass a QPalette or None to use default'''
            self._palette = palette
            
        def getPalette(self):
            return self._palette
            
        def setLabelFormat(self, format):
            '''pass a format string (e.g. "%g") or None to use default (it uses the locale)'''
            self._labelFormat = format
            self.invalidateCache() #to force repainting of the labels
        
        def getLabelFormat(self):
            '''pass a format string (e.g. "%g") or None to use default (it uses the locale)'''
            return self._labelFormat
        
        def label(self, val):
            if str(self._labelFormat) == "": return Qwt5.QwtText()
            if self._labelFormat is None:
                return Qwt5.QwtScaleDraw.label(self, val)
            else:
                return Qwt5.QwtText(self._labelFormat%val)
        
        def draw(self, painter, palette):
            if self._palette is None:
                Qwt5.QwtScaleDraw.draw(self, painter, palette)
            else:
                Qwt5.QwtScaleDraw.draw(self, painter, self._palette)
        

class DateTimeScaleEngine(Qwt5.QwtLinearScaleEngine):
    def __init__(self, scaleDraw=None):
        Qwt5.QwtLinearScaleEngine.__init__(self)
        self.setScaleDraw(scaleDraw)
        
    def setScaleDraw(self, scaleDraw):
        self._scaleDraw = scaleDraw
        
    def scaleDraw(self):
        return self._scaleDraw
        
    def divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize):
        ''' Reimplements Qwt5.QwtLinearScaleEngine.divideScale
        
        **Important**: The stepSize parameter is **ignored**.
        
        :return: (Qwt5.QwtScaleDiv) a scale division whose ticks are aligned with
                 the natural time units '''
        
        #if stepSize != 0:
        #    scaleDiv = Qwt5.QwtLinearScaleEngine.divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize)
        #    scaleDiv.datetimeLabelFormat = "%Y/%m/%d %H:%M%S.%f"
        #    return scaleDiv
            
        interval = Qwt5.QwtDoubleInterval(x1, x2).normalized()
        if interval.width() <= 0:
            return Qwt5.QwtScaleDiv()
            
        dt1=datetime.fromtimestamp(interval.minValue())
        dt2=datetime.fromtimestamp(interval.maxValue())
        
        if dt1.year<1900 or dt2.year>9999 : #limits in time.mktime and datetime
            return Qwt5.QwtScaleDiv()
        
        majticks = []
        medticks = []
        minticks = []
        
        dx=interval.width()
        
        if dx > 63072001: # = 3600s*24*(365+366) = 2 years (counting a leap year)
            format = "%Y"
            for y in range(dt1.year+1,dt2.year):
                dt = datetime(year=y, month=1, day=1)
                majticks.append(mktime(dt.timetuple()))
        
        elif dx > 5270400: # = 3600s*24*61 = 61 days
            format = "%Y %b"
            d = timedelta(days=31)
            dt = dt1.replace(day=1, hour=0, minute=0, second=0, microsecond=0)+d 
            while(dt<dt2):
                dt = dt.replace(day=1) #make sure that we are on day 1 (even if always sum 31 days)
                majticks.append(mktime(dt.timetuple()))    
                dt += d
        
        elif dx > 172800: # 3600s24*2 = 2 days
            format = "%b/%d"
            d = timedelta(days=1)
            dt = dt1.replace(hour=0, minute=0, second=0, microsecond=0) + d
            while(dt<dt2):
                majticks.append(mktime(dt.timetuple()))
                dt += d
                
        elif dx > 7200: # 3600s*2 = 2hours
            format = "%b/%d-%Hh"
            d = timedelta(hours=1)
            dt = dt1.replace(minute=0, second=0, microsecond=0) + d
            while(dt<dt2):
                majticks.append(mktime(dt.timetuple()))
                dt += d
                
        elif dx > 1200: # 60s*20 =20 minutes
            format = "%H:%M"
            d = timedelta(minutes=10)
            dt = dt1.replace(minute=(dt1.minute//10)*10, second=0, microsecond=0) + d 
            while(dt<dt2):
                majticks.append(mktime(dt.timetuple()))
                dt += d
            
        elif dx > 120: # =60s*2 = 2 minutes
            format = "%H:%M"
            d = timedelta(minutes=1)
            dt = dt1.replace(second=0, microsecond=0) + d
            while(dt<dt2):
                majticks.append(mktime(dt.timetuple()))
                dt += d
            
        elif dx > 20: # 20 s
            format = "%H:%M:%S"
            d = timedelta(seconds=10)
            dt = dt1.replace(second=(dt1.second//10)*10, microsecond=0) + d 
            while(dt<dt2):
                majticks.append(mktime(dt.timetuple()))
                dt += d
                
        elif dx > 2: # 2s
            format = "%H:%M:%S"
            majticks=range(int(x1)+1, int(x2))
            
        else: #less than 2s (show microseconds)
            scaleDiv = Qwt5.QwtLinearScaleEngine.divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize)
            self.scaleDraw().setDatetimeLabelFormat("%S.%f")
            return scaleDiv
        
        #make sure to comply with maxMajTicks 
        L= len(majticks)
        if L > maxMajSteps:
            majticks = majticks[::int(numpy.ceil(float(L)/maxMajSteps))] 
        
        scaleDiv = Qwt5.QwtScaleDiv(interval, minticks, medticks, majticks)
        self.scaleDraw().setDatetimeLabelFormat(format)
        if x1>x2:
            scaleDiv.invert()
        
        ##START DEBUG
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        #for tk in  scaleDiv.ticks(scaleDiv.MajorTick):
        #    print datetime.fromtimestamp(tk).isoformat()
        #print "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
        ##END DEBUG
        
        return scaleDiv
    
    @staticmethod
    def getDefaultAxisLabelsAlignment(axis, rotation):
        '''return a "smart" alignment for the axis labels depending on the axis
        and the label rotation

        :param axis: (Qwt5.QwtPlot.Axis) the axis
        :param rotation: (float) The rotation (in degrees, clockwise-positive)

        :return: (Qt.Alignment) an alignment
        '''
        return _getDefaultAxisLabelsAlignment(axis, rotation)

    @staticmethod        
    def enableInAxis(plot, axis, scaleDraw =None, rotation=None):
        '''convenience method that will enable this engine in the given
        axis. Note that it changes the ScaleDraw as well.
         
        :param plot: (Qwt5.QwtPlot) the plot to change 
        :param axis: (Qwt5.QwtPlot.Axis) the id of the axis 
        :param scaleDraw: (Qwt5.QwtScaleDraw) Scale draw to use. If None given, 
                          the current ScaleDraw for the plot will be used if 
                          possible, and a :class:`TaurusTimeScaleDraw` will be set if not
        :param rotation: (float or None) The rotation of the labels (in degrees, clockwise-positive)
        '''
        if scaleDraw is None:
            scaleDraw = plot.axisScaleDraw(axis)
            if not isinstance(scaleDraw, TaurusTimeScaleDraw):
                scaleDraw = TaurusTimeScaleDraw()
        plot.setAxisScaleDraw(axis, scaleDraw)
        plot.setAxisScaleEngine(axis, DateTimeScaleEngine(scaleDraw))
        if rotation is not None:
            alignment = DateTimeScaleEngine.getDefaultAxisLabelsAlignment(axis, rotation)
            plot.setAxisLabelRotation(axis, rotation)
            plot.setAxisLabelAlignment(axis, alignment)
        
    @staticmethod 
    def disableInAxis(plot, axis, scaleDraw=None, scaleEngine=None):
        '''convenience method that will disable this engine in the given
        axis. Note that it changes the ScaleDraw as well.
         
        :param plot: (Qwt5.QwtPlot) the plot to change
        :param axis: (Qwt5.QwtPlot.Axis) the id of the axis
        :param scaleDraw: (Qwt5.QwtScaleDraw) Scale draw to use. If None given, 
                          a :class:`FancyScaleDraw` will be set
        :param scaleEngine: (Qwt5.QwtScaleEngine) Scale draw to use. If None given, 
                          a :class:`Qwt5.QwtLinearScaleEngine` will be set
        '''
        if scaleDraw is None:
            scaleDraw=FancyScaleDraw()
        if scaleEngine is None:
            scaleEngine = Qwt5.QwtLinearScaleEngine()
        plot.setAxisScaleEngine(axis, scaleEngine)
        plot.setAxisScaleDraw(axis, scaleDraw) 
    
  
class TaurusTimeScaleDraw(FancyScaleDraw):
    
    def __init__(self, *args):
        FancyScaleDraw.__init__(self, *args)
    
    def setDatetimeLabelFormat(self, format):
        self._datetimeLabelFormat = format
    
    def datetimeLabelFormat(self):
        return self._datetimeLabelFormat
    
    def label(self, val):
        if str(self._labelFormat) == "": return Qwt5.QwtText()
        # From val to a string with time
        t = datetime.fromtimestamp(val)
        try: #If the scaleDiv was created by a DateTimeScaleEngine it has a _datetimeLabelFormat 
            s = t.strftime(self._datetimeLabelFormat) 
        except AttributeError, e:
            print "Warning: cannot get the datetime label format (Are you using a DateTimeScaleEngine?)"
            s = t.isoformat(' ')
        return Qwt5.QwtText(s)
    

class DeltaTimeScaleEngine(Qwt5.QwtLinearScaleEngine):
    def __init__(self, scaleDraw=None):
        Qwt5.QwtLinearScaleEngine.__init__(self)
        self.setScaleDraw(scaleDraw)
        
    def setScaleDraw(self, scaleDraw):
        self._scaleDraw = scaleDraw
        
    def scaleDraw(self):
        return self._scaleDraw

    def divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize):
        ''' Reimplements Qwt5.QwtLinearScaleEngine.divideScale
                
        :return: (Qwt5.QwtScaleDiv) a scale division whose ticks are aligned with
                 the natural delta time units '''
        interval = Qwt5.QwtDoubleInterval(x1, x2).normalized()
        if interval.width() <= 0:
            return Qwt5.QwtScaleDiv()
        d_range = interval.width()
        if d_range < 2: # 2s
            return Qwt5.QwtLinearScaleEngine.divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize)
        elif d_range < 20: # 20 s
            s = 1
        elif d_range < 120: # =60s*2 = 2 minutes
            s = 10
        elif d_range < 1200: # 60s*20 =20 minutes
            s = 60
        elif d_range < 7200: # 3600s*2 = 2 hours
            s = 600
        elif d_range < 172800: # 3600s24*2 = 2 days
            s = 3600
        else: 
            s = 86400 #1 day
        #calculate a step size that respects the base step (s) and also enforces the maxMajSteps
        stepSize = s * int(numpy.ceil(float(d_range//s)/maxMajSteps))
        return Qwt5.QwtLinearScaleEngine.divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize)
    
    @staticmethod
    def getDefaultAxisLabelsAlignment(axis, rotation):
        '''return a "smart" alignment for the axis labels depending on the axis
        and the label rotation

        :param axis: (Qwt5.QwtPlot.Axis) the axis
        :param rotation: (float) The rotation (in degrees, clockwise-positive)

        :return: (Qt.Alignment) an alignment
        '''
        return _getDefaultAxisLabelsAlignment(axis, rotation)
        
    @staticmethod        
    def enableInAxis(plot, axis, scaleDraw =None, rotation=None):
        '''convenience method that will enable this engine in the given
        axis. Note that it changes the ScaleDraw as well.
         
        :param plot: (Qwt5.QwtPlot) the plot to change 
        :param axis: (Qwt5.QwtPlot.Axis) the id of the axis 
        :param scaleDraw: (Qwt5.QwtScaleDraw) Scale draw to use. If None given, 
                          the current ScaleDraw for the plot will be used if 
                          possible, and a :class:`TaurusTimeScaleDraw` will be set if not
        :param rotation: (float or None) The rotation of the labels (in degrees, clockwise-positive)
        '''
        if scaleDraw is None:
            scaleDraw = plot.axisScaleDraw(axis)
            if not isinstance(scaleDraw, DeltaTimeScaleDraw):
                scaleDraw = DeltaTimeScaleDraw()
        plot.setAxisScaleDraw(axis, scaleDraw)
        plot.setAxisScaleEngine(axis, DeltaTimeScaleEngine(scaleDraw))
        if rotation is not None:
            alignment = DeltaTimeScaleEngine.getDefaultAxisLabelsAlignment(axis, rotation)
            plot.setAxisLabelRotation(axis, rotation)
            plot.setAxisLabelAlignment(axis, alignment)
        
    @staticmethod 
    def disableInAxis(plot, axis, scaleDraw=None, scaleEngine=None):
        '''convenience method that will disable this engine in the given
        axis. Note that it changes the ScaleDraw as well.
         
        :param plot: (Qwt5.QwtPlot) the plot to change
        :param axis: (Qwt5.QwtPlot.Axis) the id of the axis
        :param scaleDraw: (Qwt5.QwtScaleDraw) Scale draw to use. If None given, 
                          a :class:`FancyScaleDraw` will be set
        :param scaleEngine: (Qwt5.QwtScaleEngine) Scale draw to use. If None given, 
                          a :class:`Qwt5.QwtLinearScaleEngine` will be set
        '''
        if scaleDraw is None:
            scaleDraw=FancyScaleDraw()
        if scaleEngine is None:
            scaleEngine = Qwt5.QwtLinearScaleEngine()
        plot.setAxisScaleEngine(axis, scaleEngine)
        plot.setAxisScaleDraw(axis, scaleDraw) 
    
  
class DeltaTimeScaleDraw(FancyScaleDraw):
    
    def __init__(self, *args):
        FancyScaleDraw.__init__(self, *args)
    
    def label(self, val):
        if val >= 0:
            s = "+%s"%str(timedelta(seconds=val))
        else:
            s = "-%s"%str(timedelta(seconds=-val))
        return Qwt5.QwtText(s)
    
 
    
class FixedLabelsScaleEngine(Qwt5.QwtLinearScaleEngine):
    def __init__(self, positions):
        '''labels is a sequence of (pos,label) tuples where pos is the point
        at wich to draw the label and label is given as a python string (or QwtText)'''
        Qwt5.QwtScaleEngine.__init__(self)
        self._positions = positions
        #self.setAttribute(self.Floating,True)
        
    def divideScale(self, x1, x2, maxMajSteps, maxMinSteps, stepSize=0.0):
        div = Qwt5.QwtScaleDiv(x1, x2, self._positions, [], [])
        div.setTicks(Qwt5.QwtScaleDiv.MajorTick, self._positions)
        return div
    
    @staticmethod        
    def enableInAxis(plot, axis, scaleDraw =None):
        '''convenience method that will enable this engine in the given
        axis. Note that it changes the ScaleDraw as well.
         
        :param plot: (Qwt5.QwtPlot) the plot to change 
        :param axis: (Qwt5.QwtPlot.Axis) the id of the axis 
        :param scaleDraw: (Qwt5.QwtScaleDraw) Scale draw to use. If None given, 
                          the current ScaleDraw for the plot will be used if 
                          possible, and a :class:`FixedLabelsScaleDraw` will be set if not
        '''
        if scaleDraw is None:
            scaleDraw = plot.axisScaleDraw(axis)
            if not isinstance(scaleDraw, FixedLabelsScaleDraw):
                scaleDraw = FixedLabelsScaleDraw()
        plot.setAxisScaleDraw(axis, scaleDraw)
        plot.setAxisScaleEngine(axis, FixedLabelsScaleEngine(scaleDraw))
        
    @staticmethod 
    def disableInAxis(plot, axis, scaleDraw=None, scaleEngine=None):
        '''convenience method that will disable this engine in the given
        axis. Note that it changes the ScaleDraw as well.
         
        :param plot: (Qwt5.QwtPlot) the plot to change
        :param axis: (Qwt5.QwtPlot.Axis) the id of the axis
        :param scaleDraw: (Qwt5.QwtScaleDraw) Scale draw to use. If None given, 
                          a :class:`FancyScaleDraw` will be set
        :param scaleEngine: (Qwt5.QwtScaleEngine) Scale draw to use. If None given, 
                          a :class:`Qwt5.QwtLinearScaleEngine` will be set
        '''
        if scaleDraw is None:
            scaleDraw=FancyScaleDraw()
        if scaleEngine is None:
            scaleEngine = Qwt5.QwtLinearScaleEngine()
        plot.setAxisScaleEngine(axis, scaleEngine)
        plot.setAxisScaleDraw(axis, scaleDraw) 


class FixedLabelsScaleDraw(FancyScaleDraw):
    def __init__(self, positions, labels):
        '''This is a custom ScaleDraw that shows labels at given positions (and nowhere else)
        positions is a sequence of points for which labels are defined.
        labels is a sequence strings (or QwtText)
        Note that the lengths of positions and labels must match'''
        
        if len(positions) != len(labels):
            raise ValueError('lengths of positions and labels do not match')
        
        FancyScaleDraw.__init__(self)
        self._positions = positions
        self._labels = labels
        #self._positionsarray = numpy.array(self._positions) #this is stored just in case
        
    def label(self, val):
        try:
            index = self._positions.index(val) #try to find an exact match
        except:
            index = None #It won't show any label
            #use the index of the closest position
            #index = (numpy.abs(self._positionsarray - val)).argmin()
        if index is not None:
            return Qwt5.QwtText(self._labels[index])
        else: Qwt5.QwtText()
        

