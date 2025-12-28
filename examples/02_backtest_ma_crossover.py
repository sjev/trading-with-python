#!/usr/bin/env python
"""Example: Moving Average Crossover Backtest with Optimization.

This example shows a simple MA crossover strategy with parameter optimization
on the training period and out-of-sample testing.

Usage:
    python examples/02_backtest_ma_crossover.py
"""

from datetime import date
from itertools import product

import pandas as pd

from twp.backtest import Split, backtest
from twp.data import YahooSource


def ma_crossover_weights(
    prices: pd.Series, fast_window: int = 10, slow_window: int = 30
) -> pd.DataFrame:
    """Generate weights based on MA crossover."""
    fast_ma = prices.rolling(fast_window).mean()
    slow_ma = prices.rolling(slow_window).mean()
    signal = (fast_ma > slow_ma).astype(float)
    weights = pd.DataFrame({prices.name: signal}, index=prices.index)
    return weights.fillna(0)


def optimize_ma_params(
    prices: pd.DataFrame,
    ticker: str,
    fast_range: range = range(5, 31, 5),
    slow_range: range = range(20, 101, 10),
) -> tuple[int, int, float]:
    """Find MA params that maximize Sharpe on training data."""
    best_sharpe = float("-inf")
    best_fast, best_slow = 10, 30

    for fast, slow in product(fast_range, slow_range):
        if fast >= slow:
            continue
        weights = ma_crossover_weights(prices[ticker], fast, slow)
        result = backtest(prices, weights)
        if result.sharpe > best_sharpe:
            best_sharpe = result.sharpe
            best_fast, best_slow = fast, slow

    return best_fast, best_slow, best_sharpe


def print_results(name: str, result) -> None:
    """Print backtest results."""
    print(f"\n{name}:")
    print(f"  Sharpe Ratio: {result.sharpe:.2f}")
    print(f"  CAGR: {result.cagr * 100:.1f}%")
    print(f"  Volatility: {result.volatility * 100:.1f}%")
    print(f"  Max Drawdown: {result.max_drawdown * 100:.1f}%")
    print(f"  Turnover: {result.turnover:.2f}")
    print(f"  Final Equity: {result.equity.iloc[-1]:.2f}")


def main() -> None:
    """Run MA crossover backtest with optimization."""
    # Load data from Yahoo Finance
    source = YahooSource()
    spy = source.get("SPY", start=date(2010, 1, 1))
    prices = pd.DataFrame({"SPY": spy["Close"]})

    # Split at 2022-01-01
    split = Split(
        train_start=prices.index[0].date(),
        train_end=date(2021, 12, 31),
        test_start=date(2022, 1, 1),
        test_end=prices.index[-1].date(),
    )
    print(f"Train period: {split.train_start} to {split.train_end}")
    print(f"Test period: {split.test_start} to {split.test_end}")

    train_prices = pd.DataFrame(split.slice_train(prices))
    test_prices = pd.DataFrame(split.slice_test(prices))

    # Optimize on training data
    print("\nOptimizing MA parameters on training data...")
    fast, slow, train_sharpe = optimize_ma_params(train_prices, "SPY")
    print(f"Best params: fast={fast}, slow={slow} (train Sharpe={train_sharpe:.2f})")

    # Backtest on train period with optimized params
    train_weights = ma_crossover_weights(train_prices["SPY"], fast, slow)
    train_result = backtest(train_prices, train_weights, cost_bps=5)
    print_results("Train Period Results", train_result)

    # Backtest on test period (out-of-sample)
    test_weights = ma_crossover_weights(test_prices["SPY"], fast, slow)
    test_result = backtest(test_prices, test_weights, cost_bps=5)
    print_results("Test Period Results (Out-of-Sample)", test_result)

    # Buy & hold comparison
    bh_train = backtest(
        train_prices, pd.DataFrame({"SPY": 1.0}, index=train_prices.index)
    )
    bh_test = backtest(test_prices, pd.DataFrame({"SPY": 1.0}, index=test_prices.index))
    print("\nBuy & Hold Comparison:")
    print(f"  Train - Sharpe: {bh_train.sharpe:.2f}, CAGR: {bh_train.cagr * 100:.1f}%")
    print(f"  Test  - Sharpe: {bh_test.sharpe:.2f}, CAGR: {bh_test.cagr * 100:.1f}%")


if __name__ == "__main__":
    main()
