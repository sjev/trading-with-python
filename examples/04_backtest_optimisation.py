# %% Imports
"""MA Crossover with Parameter Optimization Example."""

from datetime import date
from itertools import product

import numpy as np
import pandas as pd

from twp.backtest import Split, backtest, metrics, summary
from twp.data import YahooSource
from twp.plotting import plot_equity

# %% Configuration
initial_capital = 100_000
cost_pct = 0.0005  # 5 bps

# %% Load data
source = YahooSource()
spy = source.get("SPY", start=date(2010, 1, 1))
prices = pd.DataFrame({"SPY": spy["Close"]})

# %% Define train/test split
split = Split(
    train_start=prices.index[0].date(),
    train_end=date(2021, 12, 31),
    test_start=date(2022, 1, 1),
    test_end=prices.index[-1].date(),
)
print(f"Train: {split.train_start} to {split.train_end}")
print(f"Test:  {split.test_start} to {split.test_end}")

train_prices = pd.DataFrame(split.slice_train(prices))
test_prices = pd.DataFrame(split.slice_test(prices))


# %% Helper: generate MA crossover signal
def ma_signal(price: pd.Series, fast: int, slow: int) -> pd.Series:
    """Generate MA crossover signal (1=long, 0=out)."""
    return (
        (price.rolling(fast).mean() > price.rolling(slow).mean()).fillna(0).astype(int)
    )


# %% Helper: signal to shares
def to_shares(signal: pd.Series, price: pd.Series, capital: float) -> pd.DataFrame:
    """Convert signal to share positions."""
    shares = np.floor(capital * signal / price).fillna(0).astype(int)
    return pd.DataFrame({price.name: shares}, index=price.index)


# %% Optimize on training data
print("\nOptimizing MA parameters...")
best_sharpe = float("-inf")
best_fast, best_slow = 10, 30

for fast, slow in product(range(5, 31, 5), range(20, 101, 10)):
    if fast >= slow:
        continue
    signal = ma_signal(train_prices["SPY"], fast, slow)
    shares = to_shares(signal, train_prices["SPY"], initial_capital)
    result = backtest(train_prices, shares, initial_capital)
    m = metrics(result["equity"])
    if m["sharpe"] > best_sharpe:
        best_sharpe = m["sharpe"]
        best_fast, best_slow = fast, slow

print(
    f"Best params: fast={best_fast}, slow={best_slow} (train Sharpe={best_sharpe:.2f})"
)

# %% Train period results
train_signal = ma_signal(train_prices["SPY"], best_fast, best_slow)
train_shares = to_shares(train_signal, train_prices["SPY"], initial_capital)
train_result = backtest(train_prices, train_shares, initial_capital, cost_pct=cost_pct)
summary(metrics(train_result["equity"]), title="Train Period")

# %% Test period results (out-of-sample)
test_signal = ma_signal(test_prices["SPY"], best_fast, best_slow)
test_shares = to_shares(test_signal, test_prices["SPY"], initial_capital)
test_result = backtest(test_prices, test_shares, initial_capital, cost_pct=cost_pct)
summary(metrics(test_result["equity"]), title="Test Period (Out-of-Sample)")

# %% Buy & hold comparison
print("\nBuy & Hold Comparison:")
for name, p in [("Train", train_prices), ("Test", test_prices)]:
    bh_shares = to_shares(pd.Series(1, index=p.index), p["SPY"], initial_capital)
    bh_result = backtest(p, bh_shares, initial_capital)
    bh_m = metrics(bh_result["equity"])
    print(f"  {name} - Sharpe: {bh_m['sharpe']:.2f}, CAGR: {bh_m['cagr']:.1%}")

# %% Plot full period
full_signal = ma_signal(prices["SPY"], best_fast, best_slow)
full_shares = to_shares(full_signal, prices["SPY"], initial_capital)
full_result = backtest(prices, full_shares, initial_capital, cost_pct=cost_pct)

bh_full_shares = to_shares(
    pd.Series(1, index=prices.index), prices["SPY"], initial_capital
)
bh_full_result = backtest(prices, bh_full_shares, initial_capital)

plot_equity(
    full_result["equity"],
    benchmark=bh_full_result["equity"],
    title=f"MA Crossover ({best_fast}/{best_slow}) vs Buy & Hold",
).show()
