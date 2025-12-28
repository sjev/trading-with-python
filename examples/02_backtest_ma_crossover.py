#!/usr/bin/env python
"""Example: Moving Average Crossover Backtest.

This example shows a simple MA crossover strategy using the backtest module.

Usage:
    python examples/02_backtest_ma_crossover.py
"""

from datetime import date
from pathlib import Path

import pandas as pd

from twp.backtest import backtest, train_test_split
from twp.data import LocalCsvSource


def ma_crossover_weights(
    prices: pd.Series, fast_window: int = 10, slow_window: int = 30
) -> pd.DataFrame:
    """Generate weights based on MA crossover.

    Long when fast MA > slow MA, otherwise flat (cash).
    """
    fast_ma = prices.rolling(fast_window).mean()
    slow_ma = prices.rolling(slow_window).mean()

    # Signal: 1 when fast > slow, 0 otherwise
    signal = (fast_ma > slow_ma).astype(float)

    # Create weights DataFrame
    weights = pd.DataFrame({"SPY": signal}, index=prices.index)
    return weights.fillna(0)


def main() -> None:
    """Run MA crossover backtest."""
    # Load data
    data_dir = Path(__file__).parent.parent / "tests/testdata/prices"
    source = LocalCsvSource(data_dir)
    spy = source.get("SPY", date(2023, 1, 1), date(2024, 12, 31))

    # Convert Series to DataFrame for backtest
    prices = pd.DataFrame({"SPY": spy if isinstance(spy, pd.Series) else spy["Close"]})

    # Generate strategy weights
    weights = ma_crossover_weights(prices["SPY"])

    # Split into train/test
    split = train_test_split(prices, train_ratio=0.7)
    print(f"Train period: {split.train_start} to {split.train_end}")
    print(f"Test period: {split.test_start} to {split.test_end}")

    # Backtest on test period
    test_prices = pd.DataFrame(split.slice_test(prices))
    test_weights = pd.DataFrame(split.slice_test(weights))

    result = backtest(test_prices, test_weights, cost_bps=5)

    # Print results
    print("\nBacktest Results (Test Period):")
    print(f"  Sharpe Ratio: {result.sharpe:.2f}")
    print(f"  CAGR: {result.cagr * 100:.1f}%")
    print(f"  Volatility: {result.volatility * 100:.1f}%")
    print(f"  Max Drawdown: {result.max_drawdown * 100:.1f}%")
    print(f"  Turnover: {result.turnover:.2f}")
    print(f"  Final Equity: {result.equity.iloc[-1]:.2f}")

    # Compare to buy-and-hold
    bh_weights = pd.DataFrame({"SPY": 1.0}, index=test_prices.index)
    bh_result = backtest(test_prices, bh_weights)
    print("\nBuy & Hold Comparison:")
    print(f"  Sharpe: {bh_result.sharpe:.2f}")
    print(f"  Final Equity: {bh_result.equity.iloc[-1]:.2f}")


if __name__ == "__main__":
    main()
