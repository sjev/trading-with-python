
yahooFinance
=============

Toolset working with yahoo finance data
This module includes functions for easy access to YahooFinance data


The module is usually imported as follows:

.. ipython:: python

   from tradingWithPython import yahooFinance as yf
  
   
   
Then, to get raw yahoo finance data for a symbol use :func:`getSymbolData`

.. ipython:: python
    
   df = yf.getSymbolData("SPY")
   df.head()
   
We can also normalize OHLC with the adj_close data:

.. ipython:: python

    df = yf.getSymbolData("SPY",adjust=True)
    df.head()
    
  
   
Functions
-------------

.. autofunction:: lib.yahooFinance.getSymbolData