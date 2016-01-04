
yahooFinance
=============

Toolset working with yahoo finance data
This module includes functions for easy access to YahooFinance data


First, we import as follows:

.. ipython:: python

   from tradingWithPython import yahooFinance as yf
   import numpy as np
   
   
Then, to get data for a symbol use `getSymbolData`

.. ipython:: python
    
   df = yf.getSymbolData("SPY")
   df.head()
   
   
   
Functions
-------------

.. autofunction:: lib.yahooFinance.getSymbolData