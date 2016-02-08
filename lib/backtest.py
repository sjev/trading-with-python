# -*- coding: utf-8 -*-
"""
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
"""

import pandas as pd
import matplotlib.pyplot as plt
import sys
import numpy as np




def tradeBracket(price,entryBar,upper=None, lower=None, timeout=None):
    """
    trade a  bracket on price series, return price delta and exit bar #
    
    Parameters
    --------------
    price : np.array 
        array of price values
    entryBar : int
        entry bar number, *determines entry price*
    upper : float 
        high stop
    lower : float 
        low stop
    timeout : int 
        max number of periods to hold

    Returns 
    ------------    
    exit price  and number of bars held

    """
    assert isinstance(price, np.ndarray) , 'price must be a numpy array'
    
    
    # create list of exit indices and add max trade duration. Exits are relative to entry bar
    if timeout: # set trade length to timeout or series length
        exits = [min(timeout,len(price)-entryBar-1)]
    else:
        exits = [len(price)-entryBar-1] 
        
    p = price[entryBar:entryBar+exits[0]+1] # subseries of price
    
    # extend exits list with conditional exits
    # check upper bracket
    if upper:
        assert upper>p[0] , 'Upper bracket must be higher than entry price '
        idx = np.where(p>upper)[0] # find where price is higher than the upper bracket
        if idx.any(): 
            exits.append(idx[0]) # append first occurence
    # same for lower bracket
    if lower:
        assert lower<p[0] , 'Lower bracket must be lower than entry price '
        idx = np.where(p<lower)[0]
        if idx.any(): 
            exits.append(idx[0]) 
   
    
    exitBar = min(exits) # choose first exit    
  
    

    return p[exitBar], exitBar


class Backtest(object):
    """
    Simple vectorized backtester. Works with pandas objects.
    
    Attributes
    -----------
    trades : Series
        trade data
    
    """
    
    def __init__(self,price, signal, signalType='capital',initialCash = 0, roundShares=True):
        """
        
        Parameters
        ------------
        price :  Series 
            instrument price.
        signal : Series 
            capital to invest (long+,short-) or number of shares. 
        sitnalType : 'capital' or 'shares'
            capital to bet or number of shares 'capital' mode is default.
        initialCash : float
            starting cash. 
        roundShares : bool 
            round off number of shares to integers
        
        """
        
        #TODO: add auto rebalancing
        
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
            self.trades = (self.signal[tradeIdx]/price[tradeIdx])
            if roundShares:
                self.trades = self.trades.round()
        
        # now create internal data structure 
        self.data = pd.DataFrame(index=price.index , columns = ['price','shares','value','cash','pnl'])
        self.data['price'] = price
        
        self.data['shares'] = self.trades.reindex(self.data.index).ffill().fillna(0)
        self.data['value'] = self.data['shares'] * self.data['price']
       
        delta = self.data['shares'].diff() # shares bought sold
        
        self.data['cash'] = (-delta*self.data['price']).fillna(0).cumsum()+initialCash
        self.data['pnl'] = self.data['cash']+self.data['value']-initialCash
      
      
    @property
    def sharpe(self):
        """ return annualized sharpe ratio of the pnl """
        pnl = (self.data['pnl'].diff()).shift(-1)[self.data['shares']!=0] # use only days with position.
        return sharpe(pnl)  # need the diff here as sharpe works on daily returns.
        
    @property
    def pnl(self):
        """ easy access to pnl data column """
        return self.data['pnl']
    
    def plotTrades(self):
        """ 
        visualise trades on the price chart 
        long entry : green triangle up
        short entry : red triangle down
        exit : black circle
        """
        l = ['price']
        
        p = self.data['price']
        p.plot(style='x-')
        
        # ---plot markers
        # this works, but I rather prefer colored markers for each day of position rather than entry-exit signals
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
            l.append('long')
        
        #colored line for short positions    
        idx = (self.data['shares'] < 0) | (self.data['shares'] < 0).shift(1) 
        if idx.any():
            p[idx].plot(style='ro')
            l.append('short')

        plt.xlim([p.index[0],p.index[-1]]) # show full axis
        
        plt.legend(l,loc='best')
        plt.title('trades')
        
        
class ProgressBar:
    def __init__(self, iterations):
        self.iterations = iterations
        self.prog_bar = '[]'
        self.fill_char = '*'
        self.width = 50
        self.__update_amount(0)

    def animate(self, iteration):
        print('\r',self, end=' ')
        sys.stdout.flush()
        self.update_iteration(iteration + 1)

    def update_iteration(self, elapsed_iter):
        self.__update_amount((elapsed_iter / float(self.iterations)) * 100.0)
        self.prog_bar += '  %d of %s complete' % (elapsed_iter, self.iterations)

    def __update_amount(self, new_amount):
        percent_done = int(round((new_amount / 100.0) * 100.0))
        all_full = self.width - 2
        num_hashes = int(round((percent_done / 100.0) * all_full))
        self.prog_bar = '[' + self.fill_char * num_hashes + ' ' * (all_full - num_hashes) + ']'
        pct_place = (len(self.prog_bar) // 2) - len(str(percent_done))
        pct_string = '%d%%' % percent_done
        self.prog_bar = self.prog_bar[0:pct_place] + \
            (pct_string + self.prog_bar[pct_place + len(pct_string):])
    def __str__(self):
        return str(self.prog_bar)
    
def sharpe(pnl):
    return  np.sqrt(250)*pnl.mean()/pnl.std()

#-------------dummy class
class ExampleClass(object):
    """The summary line for a class docstring should fit on one line.

    If the class has public attributes, they may be documented here
    in an ``Attributes`` section and follow the same formatting as a
    function's ``Args`` section. Alternatively, attributes may be documented
    inline with the attribute's declaration (see __init__ method below).

    Properties created with the ``@property`` decorator should be documented
    in the property's getter method.

    Attribute and property types -- if given -- should be specified according
    to `PEP 484`_, though `PEP 484`_ conformance isn't required or enforced.

    Attributes
    ----------
    attr1 : str
        Description of `attr1`.
    attr2 : Optional[int]
        Description of `attr2`.


    .. _PEP 484:
       https://www.python.org/dev/peps/pep-0484/

    """

    def __init__(self, param1, param2, param3):
        """Example of docstring on the __init__ method.

        The __init__ method may be documented in either the class level
        docstring, or as a docstring on the __init__ method itself.

        Either form is acceptable, but the two should not be mixed. Choose one
        convention to document the __init__ method and be consistent with it.

        Note
        ----
        Do not include the `self` parameter in the ``Parameters`` section.

        Parameters
        ----------
        param1 : str
            Description of `param1`.
        param2 : List[str]
            Description of `param2`. Multiple
            lines are supported.
        param3 : Optional[int]
            Description of `param3`.

        """
        self.attr1 = param1
        self.attr2 = param2
        self.attr3 = param3  #: Doc comment *inline* with attribute

        #: List[str]: Doc comment *before* attribute, with type specified
        self.attr4 = ["attr4"]

        self.attr5 = None
        """Optional[str]: Docstring *after* attribute, with type specified."""

    @property
    def readonly_property(self):
        """str: Properties should be documented in their getter method."""
        return "readonly_property"

    @property
    def readwrite_property(self):
        """List[str]: Properties with both a getter and setter should only
        be documented in their getter method.

        If the setter method contains notable behavior, it should be
        mentioned here.
        """
        return ["readwrite_property"]

    @readwrite_property.setter
    def readwrite_property(self, value):
        value

    def example_method(self, param1, param2):
        """Class methods are similar to regular functions.

        Note
        ----
        Do not include the `self` parameter in the ``Parameters`` section.

        Parameters
        ----------
        param1
            The first parameter.
        param2
            The second parameter.

        Returns
        -------
        bool
            True if successful, False otherwise.

        """
        return True

    def __special__(self):
        """By default special members with docstrings are included.

        Special members are any methods or attributes that start with and
        end with a double underscore. Any special member with a docstring
        will be included in the output.

        This behavior can be disabled by changing the following setting in
        Sphinx's conf.py::

            napoleon_include_special_with_doc = False

        """
        pass

    def __special_without_docstring__(self):
        pass

    def _private(self):
        """By default private members are not included.

        Private members are any methods or attributes that start with an
        underscore and are *not* special. By default they are not included
        in the output.

        This behavior can be changed such that private members *are* included
        by changing the following setting in Sphinx's conf.py::

            napoleon_include_private_with_doc = True

        """
        pass

    def _private_without_docstring(self):
        pass
