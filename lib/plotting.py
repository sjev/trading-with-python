#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plotting functions for data visualisation.


"""

from bokeh.plotting import figure, output_notebook, show

from bokeh.layouts import gridplot
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource


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