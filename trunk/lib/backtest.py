#-------------------------------------------------------------------------------
# Name:        backtest
# Purpose:     perform routine backtesting  tasks. 
#              This module should be useable as a stand-alone library outide of the TWP package.
#
# Author:      Jev Kuznetsov
#
# Created:     03/07/2014
# Copyright:   (c) Jev Kuznetsov 2013
# Licence:     BSD
#-------------------------------------------------------------------------------

import pandas as pd
#import matplotlib.pyplot as plt

class Backtest(object):
    """
    Backtest class, simple vectorized one. Works with pandas objects.
    """
    
    def __init__(self,price, signal, signalType='capital',initialCash = 0):
        """
        Arguments:
        
        *price*  Series with instrument price.
        *signal* Series with capital to invest (long+,short-) or number of shares. 
        *sitnalType* capital to bet or number of shares 'capital' mode is default.
        *initialCash* starting cash. 
        
        """
        # check for correct input
        assert signalType in ['capital','shares'], "Wrong signal type provided, must be 'capital' or 'shares'"
        
        #save internal settings to a dict
        self.settings = {'signalType':signalType}
        
        # first thing to do is to clean up the signal, removing nans and duplicate entries or exits
        self.signal = signal.ffill().fillna(0)
        
        # now find dates with a trade
        tradeIdx = self.signal.diff().fillna(0) !=0 # days with trades are set to True
        if signalType == 'shares':
            self.trades = self.signal[tradeIdx] # selected rows where tradeDir changes value. trades are in Shares
        elif signalType =='capital':
            self.trades = (self.signal[tradeIdx]/price[tradeIdx]).round()
        
        # now create internal data structure 
        self.data = pd.DataFrame(index=price.index , columns = ['price','shares','value','cash','pnl'])
        self.data['price'] = price
        
        self.data['shares'] = self.trades.reindex(self.data.index).ffill().fillna(0)
        self.data['value'] = self.data['shares'] * self.data['price']
       
        delta = self.data['shares'].diff() # shares bought sold
        
        self.data['cash'] = (-delta*self.data['price']).fillna(0).cumsum()+initialCash
        self.data['pnl'] = self.data['cash']+self.data['value']-initialCash
        
    @property
    def pnl(self):
        '''easy access to pnl data column '''
        return self.data['pnl']
    
    def plotTrades(self):
        """ 
        visualise trades on the price chart 
            long entry : green triangle up
            short entry : red triangle down
            exit : black circle
        """
        p = self.data['price']
        p.plot(style='x-')
        
        # ---plot markers
        
#         indices = {'g^': self.trades[self.trades > 0].index , 
#                    'ko':self.trades[self.trades == 0].index, 
#                    'rv':self.trades[self.trades < 0].index}
#        
#         
#         for style, idx in indices.iteritems():
#             if len(idx) > 0:
#                 p[idx].plot(style=style)
        
        # --- plot trades
        #colored line for long positions
        idx = (self.data['shares'] > 0) | (self.data['shares'] > 0).shift(1) 
        if idx.any():
            p[idx].plot(style='go')
        
        #colored line for short positions    
        idx = (self.data['shares'] < 0) | (self.data['shares'] < 0).shift(1) 
        if idx.any():
            p[idx].plot(style='ro')

