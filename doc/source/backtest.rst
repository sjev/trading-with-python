.. currentmodule:: tradingWithPython

.. ipython:: python
    :suppress:

    import matplotlib.pyplot as plt
    plt.style.use('ggplot')


===============
Backtesting
===============
Strategy simulation often includes going through same steps : determining entry and exit moments, calculating number of shares capital and pnl. To limit the number of lines of code needed to perform a backtest, the *twp* library includes a simple backtesting module.

The *backtest* module is a very simple version of a vectorized backtester. It can be used as a stand-alone module without the rest of the *tradingWithPython* library.

All of the functionality is accessible through the *Backtest* class, which will be demonstrated here.


The backtester needs an instrument price and entry/exit signals to do its job. Let's start by creating simple data series to test it.


.. ipython:: python

    import tradingWithPython as twp
    import pandas as pd
    import numpy as np




.. ipython:: python

   ts = pd.Series(np.random.randn(1000), index=pd.date_range('1/1/2000', periods=1000))
   ts = ts.cumsum()

   @savefig series_plot_basic.png
   ts.plot()





Backtest class
----------------
.. autoclass:: tradingWithPython.lib.backtest.Backtest
    :members:


Functions
------------
.. autofunction:: tradingWithPython.lib.backtest.tradeBracket
