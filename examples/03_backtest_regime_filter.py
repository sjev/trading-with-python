#!/usr/bin/env python
"""Example: Regime-Filtered Strategy Backtest.

This example shows how to use market regime indicators to filter trades.
The strategy is long SPY when the regime indicator is bullish.

Usage:
    python examples/03_backtest_regime_filter.py
"""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from twp.backtest import Backtest
from twp.data import LocalCsvSource
from twp.indicators import MomentumIndicator, VixIndicator


def regime_signal(source: LocalCsvSource, start: date, end: date) -> pd.Series:
    """Generate binary signal based on regime filter (1=long, 0=out)."""
    momentum = MomentumIndicator(source=source, ticker="SPY", ma_window=5)
    vix = VixIndicator(source=source, ticker="^VIX")

    mom_history = momentum.history(start, end)
    vix_history = vix.history(start, end)

    # Align indices
    common_idx = mom_history.index.intersection(vix_history.index)
    mom_norm = mom_history.loc[common_idx, "normalized"]
    vix_norm = vix_history.loc[common_idx, "normalized"]

    # Long when momentum > 0.5 AND vix < 0.5
    return ((mom_norm > 0.5) & (vix_norm < 0.5)).astype(int)


def signal_to_shares(
    signal: pd.Series, prices: pd.Series, capital: float
) -> pd.DataFrame:
    """Convert signal to share positions based on available capital."""
    shares = np.floor(capital * signal / prices).fillna(0).astype(int)
    return pd.DataFrame({prices.name: shares}, index=prices.index)


def main() -> None:
    """Run regime-filtered backtest."""
    # Configuration
    initial_capital = 100_000
    cost_pct = 0.0005  # 5 bps

    # Load data
    data_dir = Path(__file__).parent.parent / "tests/testdata/prices"
    source = LocalCsvSource(data_dir)

    start = date(2023, 6, 1)
    end = date(2024, 1, 10)

    # Get prices
    spy = source.get("SPY", start, end)
    prices = pd.DataFrame({"SPY": spy if isinstance(spy, pd.Series) else spy["Close"]})

    # Generate signal and convert to shares
    signal = regime_signal(source, start, end)
    common_idx = prices.index.intersection(signal.index)
    prices = prices.loc[common_idx]
    signal = signal.loc[common_idx]
    shares = signal_to_shares(signal, prices["SPY"], initial_capital)

    # Run backtest
    bt = Backtest(
        prices=prices,
        shares=shares,
        initial_capital=initial_capital,
        cost_pct=cost_pct,
    )

    # Print results
    print("Regime-Filtered Strategy Results:")
    print(f"  Period: {start} to {end}")
    print(f"  Sharpe Ratio: {bt.metrics['sharpe']:.2f}")
    print(f"  CAGR: {bt.metrics['cagr']:.1%}")
    print(f"  Volatility: {bt.metrics['volatility']:.1%}")
    print(f"  Max Drawdown: {bt.metrics['max_drawdown']:.1%}")
    print(f"  Turnover: {bt.metrics['turnover']:.2%}")
    print(f"  Final Equity: ${bt.equity.iloc[-1]:,.0f}")

    # Calculate exposure
    exposure = signal.mean() * 100
    print(f"  Average Exposure: {exposure:.1f}%")

    # Compare to buy-and-hold
    bh_shares = signal_to_shares(
        pd.Series(1, index=prices.index), prices["SPY"], initial_capital
    )
    bh = Backtest(prices=prices, shares=bh_shares, initial_capital=initial_capital)
    print("\nBuy & Hold Comparison:")
    print(f"  Sharpe: {bh.metrics['sharpe']:.2f}")
    print(f"  Final Equity: ${bh.equity.iloc[-1]:,.0f}")


if __name__ == "__main__":
    main()
