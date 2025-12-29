# %% Imports
"""Simple Moving Average Crossover Backtest Example."""

from datetime import date

import numpy as np
import pandas as pd

from twp.backtest import backtest, metrics, summary
from twp.data import YahooSource
from twp.plotting import plot_equity

# %% Configuration
initial_capital = 100_000
fast_window = 10
slow_window = 30

# %% Load data
source = YahooSource()
spy = source.get("SPY", start=date(2020, 1, 1))
prices = pd.DataFrame({"SPY": spy["Close"]})

# %% Generate MA crossover signal
fast_ma = prices["SPY"].rolling(fast_window).mean()
slow_ma = prices["SPY"].rolling(slow_window).mean()
signal = (fast_ma > slow_ma).astype(int)

# %% Convert signal to share positions
shares = np.floor(initial_capital * signal / prices["SPY"]).fillna(0).astype(int)
shares = pd.DataFrame({"SPY": shares}, index=prices.index)

# %% Run backtest
result = backtest(prices, shares, initial_capital)

# %% Show metrics
m = metrics(result["equity"])
summary(m, title=f"MA Crossover (fast={fast_window}, slow={slow_window})")

# %% Plot
plot_equity(result["equity"], benchmark=prices["SPY"]).show()
