# %% Imports
"""Regime-Filtered Strategy Backtest Example."""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from twp.backtest import backtest, metrics, summary
from twp.data import LocalCsvSource
from twp.indicators import MomentumIndicator, VixIndicator
from twp.plotting import plot_equity

# %% Configuration
initial_capital = 100_000
cost_pct = 0.0005  # 5 bps
start = date(2023, 6, 1)
end = date(2024, 1, 10)

# %% Load data
data_dir = Path(__file__).parent.parent / "tests/testdata/prices"
source = LocalCsvSource(data_dir)
spy = source.get("SPY", start, end)
prices = pd.DataFrame({"SPY": spy if isinstance(spy, pd.Series) else spy["Close"]})

# %% Generate regime signal
momentum = MomentumIndicator(source=source, ticker="SPY", ma_window=5)
vix = VixIndicator(source=source, ticker="^VIX")

mom_history = momentum.history(start, end)
vix_history = vix.history(start, end)

# Align indices
common_idx = mom_history.index.intersection(vix_history.index).intersection(
    prices.index
)
prices = prices.loc[common_idx]
mom_norm = mom_history.loc[common_idx, "normalized"]
vix_norm = vix_history.loc[common_idx, "normalized"]

# Long when momentum > 0.5 AND vix < 0.5
signal = ((mom_norm > 0.5) & (vix_norm < 0.5)).astype(int)

# %% Convert signal to shares
shares = np.floor(initial_capital * signal / prices["SPY"]).fillna(0).astype(int)
shares = pd.DataFrame({"SPY": shares}, index=prices.index)

# %% Run strategy backtest
result = backtest(prices, shares, initial_capital, cost_pct=cost_pct)
m = metrics(result["equity"])
summary(m, title="Regime-Filtered Strategy")

exposure = signal.mean() * 100
print(f"Average Exposure: {exposure:.1f}%")

# %% Compare to buy-and-hold
bh_shares = np.floor(initial_capital / prices["SPY"].iloc[0]).astype(int)
bh_shares = pd.DataFrame({"SPY": [bh_shares] * len(prices)}, index=prices.index)
bh_result = backtest(prices, bh_shares, initial_capital)
bh_m = metrics(bh_result["equity"])
summary(bh_m, title="Buy & Hold")

# %% Plot comparison
plot_equity(result["equity"], benchmark=bh_result["equity"]).show()
