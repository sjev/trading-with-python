.. currentmodule:: tradingWithPython

.. automodule:: lib.yahooFinance

Module functionality
====================



Getting historic data
----------------------

The module is usually imported as follows:

.. ipython:: python

   from tradingWithPython import yahooFinance as yf

   
   
Then, to get raw yahoo finance data for a symbol use :func:`~lib.yahooFinance.getSymbolData`

.. ipython:: python

   df = yf.getSymbolData("SPY")
   df.head()
   
We can also normalize OHLC with the *adj_close* data column. After normalization,
the *close* column will be equal to *adj_close* , so the latter is omitted from the result.

.. ipython:: python

    df = yf.getSymbolData("SPY",adjust=True)
    df.head()
    

Getting current quotes
-----------------------

The :func:`~lib.yahooFinance.getQuote` is used to get current quote 

.. ipython:: python

    quote = yf.getQuote(['SPY','XLE','QQQ'])
    quote
    
.. note::

    YahooFinance quotes may be delayed for more than 15 minutes

  
   
Functions
==========

.. autofunction:: getSymbolData
.. autofunction:: getQuote