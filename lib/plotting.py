#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""

Plotting module
===================

This module contains plotting functionality for easy data visualisation.
It is essentially a wrapper around `Bokeh <https://bokeh.pydata.org/en/latest/>`_ plotting library.



"""
import numpy as np
from math import pi
from bokeh.plotting import figure, output_notebook, show

from bokeh.layouts import gridplot
from bokeh.models import ColumnDataSource

class Plot:
    
    def __init__(self,width=900):
        
        self.fig = figure(x_axis_type="datetime",width=width)
        self.fig.xaxis.major_label_orientation = pi/4
    
    def line(self,series,**kwargs):
        """
        plot Series as a line
        
        Parameters
        -------------
        series : pd.Series
            time series 
        **kwargs : named arguments
            extra arguments to be passed to bokeh.line
        """
        
        x = series.index
        y = series.values
        print(kwargs)
        self.fig.line(x,y,**kwargs)
    
    
    def candlestick(self, df):
        """
        plot candlesticks from DataFrame
        
        Parameters
        ------------
        df : pd.DataFrame
            input, must contain 'open','low','high' and 'close' columns
        """
        
        
        x = df.index
        p = self.fig
        
        inc = df.close > df.open
        dec = df.open > df.close
        w =  np.median(np.diff(df.index))/np.timedelta64(1,'ms')/1.5 # bar width in ms
        
        p.segment(x, df.high, x, df.low, color="#0066DD")
        p.vbar(x[inc], w, df.open[inc], df.close[inc], fill_color="white", line_color="#0066DD")
        p.vbar(x[dec], w, df.open[dec], df.close[dec], fill_color="#0066DD", line_color="#0066DD")
    
    
    def triangle(self,series,orientation='up',**kwargs):
        """
        Plot triangular markers
        
        Parameters
        -----------
        series : pd.Series
            input data
        orientation : 'up' (default) or 'down'
            marker direction
         **kwargs : named arguments
            extra arguments to be passed to bokeh
        """
        
        angles = {'up':0,'down':45}
        self.fig.triangle(series.index,series.values,angle=angles[orientation],size=10,**kwargs)
    
    def  show(self):
        """ show plot """
        show(self.fig)
        





def linkedPlots(df, xy, plot_options = dict(width=800, 
                                    plot_height=250, 
                                    tools='box_select,pan,wheel_zoom,undo,box_zoom,reset')
):
    """ 
    Plot time series above each other
    
    Parameters
    -------------
    df : DataFrame
        pandas dataframe
   
    xy : [(x0,y0),(x1,y1),...]
          pairs of column names in df to plot
    
    plot_options : dict
        plot options for bokeh
        
    
    Returns
    --------
    figures : lsit 
        list of bokeh figures
    
    """
    
    source = ColumnDataSource(df)
    
    figures = []

    for idx, (x,y) in enumerate(xy):
        
        if x=='index':
            fig = figure(x_axis_type="datetime",**plot_options)
        else:
            fig = figure(**plot_options)
        # link panning
        if idx != 0:
            fig.x_range = figures[0].x_range
        
        fig.line(x,y,source=source)
        fig.circle(x,y,
                   source=source,selection_color="firebrick",fill_color='white')
        figures.append(fig)
    
    p = gridplot([[f] for f in figures])
    show(p)
    
    return figures