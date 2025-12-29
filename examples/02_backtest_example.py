# %% Imports and setup
"""Simple Moving Average Crossover Backtest Example."""

from datetime import date

import numpy as np
import pandas as pd

from twp.backtest import Backtest
from twp.data import YahooSource

# %% Configuration
initial_capital = 100_000
fast_window = 10
slow_window = 30
cost_per_share = 0.005  # IB-like pricing

# %% Load data
print("Loading SPY data from Yahoo Finance...")
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
bt = Backtest(
    prices=prices,
    shares=shares,
    initial_capital=initial_capital,
    cost_per_share=cost_per_share,
)

# %% Print results
print(f"\n{'=' * 50}")
print(f"MA Crossover Strategy (fast={fast_window}, slow={slow_window})")
print(f"{'=' * 50}")
print(f"Period: {prices.index[0].date()} to {prices.index[-1].date()}")
print(f"Initial Capital: ${initial_capital:,.0f}")
print("\nPerformance Metrics:")
print(f"  Sharpe Ratio:  {bt.metrics['sharpe']:.2f}")
print(f"  CAGR:          {bt.metrics['cagr']:.1%}")
print(f"  Volatility:    {bt.metrics['volatility']:.1%}")
print(f"  Max Drawdown:  {bt.metrics['max_drawdown']:.1%}")
print(f"  Turnover:      {bt.metrics['turnover']:.2%}")
print(f"\nFinal Equity:    ${bt.equity.iloc[-1]:,.0f}")
print(f"Total PnL:       ${bt.pnl.sum():,.0f}")

# Check for margin usage
min_cash = bt.cash.min()
if min_cash < 0:
    print(f"\nWarning: Strategy used margin (min cash: ${min_cash:,.0f})")

# %% Generate report
benchmark = prices["SPY"]
report_path = bt.report(benchmark=benchmark, output_path="backtest_report.html")
print(f"\nReport saved to: {report_path}")
