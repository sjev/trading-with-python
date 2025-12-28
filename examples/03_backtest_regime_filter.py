#!/usr/bin/env python
"""Example: Regime-Filtered Strategy Backtest.

This example shows how to use market regime indicators to filter trades.
The strategy is long SPY when the regime indicator is bullish.

Usage:
    python examples/03_backtest_regime_filter.py
"""

from datetime import date
from pathlib import Path

import pandas as pd

from twp.backtest import backtest
from twp.data import LocalCsvSource
from twp.indicators import MomentumIndicator, VixIndicator


def regime_filter_weights(
    source: LocalCsvSource,
    start: date,
    end: date,
) -> pd.DataFrame:
    """Generate weights based on regime filter.

    Long SPY when momentum is bullish and VIX is low.
    """
    # Get indicator histories
    momentum = MomentumIndicator(source=source, ticker="SPY", ma_window=5)
    vix = VixIndicator(source=source, ticker="^VIX")

    mom_history = momentum.history(start, end)
    vix_history = vix.history(start, end)

    # Align indices
    common_idx = mom_history.index.intersection(vix_history.index)
    mom_norm = mom_history.loc[common_idx, "normalized"]
    vix_norm = vix_history.loc[common_idx, "normalized"]

    # Signal: long when momentum > 0.5 AND vix < 0.5
    signal = ((mom_norm > 0.5) & (vix_norm < 0.5)).astype(float)

    weights = pd.DataFrame({"SPY": signal})
    return weights


def main() -> None:
    """Run regime-filtered backtest."""
    # Load data
    data_dir = Path(__file__).parent.parent / "tests/testdata/prices"
    source = LocalCsvSource(data_dir)

    start = date(2023, 6, 1)
    end = date(2024, 1, 10)

    # Get prices
    spy = source.get("SPY", start, end)
    prices = pd.DataFrame({"SPY": spy if isinstance(spy, pd.Series) else spy["Close"]})

    # Generate regime-filtered weights
    weights = regime_filter_weights(source, start, end)

    # Align prices and weights
    common_idx = prices.index.intersection(weights.index)
    prices = prices.loc[common_idx]
    weights = weights.loc[common_idx]

    # Run backtest
    result = backtest(prices, weights, cost_bps=5)

    # Print results
    print("Regime-Filtered Strategy Results:")
    print(f"  Period: {start} to {end}")
    print(f"  Sharpe Ratio: {result.sharpe:.2f}")
    print(f"  CAGR: {result.cagr*100:.1f}%")
    print(f"  Volatility: {result.volatility*100:.1f}%")
    print(f"  Max Drawdown: {result.max_drawdown*100:.1f}%")
    print(f"  Turnover: {result.turnover:.2f}")
    print(f"  Final Equity: {result.equity.iloc[-1]:.2f}")

    # Calculate exposure
    exposure = weights["SPY"].mean() * 100
    print(f"  Average Exposure: {exposure:.1f}%")

    # Compare to buy-and-hold
    bh_weights = pd.DataFrame({"SPY": 1.0}, index=prices.index)
    bh_result = backtest(prices, bh_weights)
    print("\nBuy & Hold Comparison:")
    print(f"  Sharpe: {bh_result.sharpe:.2f}")
    print(f"  Final Equity: {bh_result.equity.iloc[-1]:.2f}")


if __name__ == "__main__":
    main()
