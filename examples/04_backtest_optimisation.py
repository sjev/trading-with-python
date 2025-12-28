#!/usr/bin/env python
"""Example: Moving Average Crossover Backtest with Optimization.

This example shows a simple MA crossover strategy with parameter optimization
on the training period and out-of-sample testing.

Usage:
    python examples/04_backtest_optimisation.py
"""

from datetime import date
from itertools import product

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from twp.backtest import Backtest, Split
from twp.data import YahooSource


def ma_crossover_signal(prices: pd.Series, fast: int = 10, slow: int = 30) -> pd.Series:
    """Generate binary signal from MA crossover (1=long, 0=out)."""
    fast_ma = prices.rolling(fast).mean()
    slow_ma = prices.rolling(slow).mean()
    return (fast_ma > slow_ma).fillna(0).astype(int)


def signal_to_shares(
    signal: pd.Series, prices: pd.Series, capital: float
) -> pd.DataFrame:
    """Convert signal to share positions based on available capital."""
    shares = np.floor(capital * signal / prices).fillna(0).astype(int)
    return pd.DataFrame({prices.name: shares}, index=prices.index)


def run_backtest(
    prices: pd.DataFrame,
    signal: pd.Series,
    initial_capital: float,
    cost_pct: float = 0.0,
) -> Backtest:
    """Run backtest from signal."""
    ticker = prices.columns[0]
    shares = signal_to_shares(signal, prices[ticker], initial_capital)
    return Backtest(
        prices=prices,
        shares=shares,
        initial_capital=initial_capital,
        cost_pct=cost_pct,
    )


def optimize_ma_params(
    prices: pd.DataFrame,
    ticker: str,
    initial_capital: float,
    fast_range: range = range(5, 31, 5),
    slow_range: range = range(20, 101, 10),
) -> tuple[int, int, float]:
    """Find MA params that maximize Sharpe on training data."""
    best_sharpe = float("-inf")
    best_fast, best_slow = 10, 30

    for fast, slow in product(fast_range, slow_range):
        if fast >= slow:
            continue
        signal = ma_crossover_signal(prices[ticker], fast, slow)
        bt = run_backtest(prices, signal, initial_capital)
        if bt.metrics["sharpe"] > best_sharpe:
            best_sharpe = bt.metrics["sharpe"]
            best_fast, best_slow = fast, slow

    return best_fast, best_slow, best_sharpe


def print_results(name: str, bt: Backtest) -> None:
    """Print backtest results."""
    m = bt.metrics
    print(f"\n{name}:")
    print(f"  Sharpe Ratio: {m['sharpe']:.2f}")
    print(f"  CAGR: {m['cagr']:.1%}")
    print(f"  Volatility: {m['volatility']:.1%}")
    print(f"  Max Drawdown: {m['max_drawdown']:.1%}")
    print(f"  Turnover: {m['turnover']:.2%}")
    print(f"  Final Equity: ${bt.equity.iloc[-1]:,.0f}")


def plot_backtest(
    prices: pd.Series,
    strategy_equity: pd.Series,
    bh_equity: pd.Series,
    fast_window: int,
    slow_window: int,
    split_date: date,
) -> go.Figure:
    """Create backtest chart with equity curves and MA signals."""
    fast_ma = prices.rolling(fast_window).mean()
    slow_ma = prices.rolling(slow_window).mean()

    # Normalize both to start at 1.0
    norm_strategy = strategy_equity / strategy_equity.iloc[0]
    norm_bh = bh_equity / bh_equity.iloc[0]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.08,
        row_heights=[0.5, 0.5],
        subplot_titles=("Equity (Normalized)", "Price & Moving Averages"),
    )

    # Top: Equity curves (normalized)
    fig.add_trace(
        go.Scatter(
            x=norm_strategy.index,
            y=norm_strategy.values,
            name="Strategy",
            line={"color": "blue"},
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=norm_bh.index,
            y=norm_bh.values,
            name="Buy & Hold",
            line={"color": "gray", "dash": "dash"},
        ),
        row=1,
        col=1,
    )

    # Bottom: Price and MAs
    fig.add_trace(
        go.Scatter(
            x=prices.index,
            y=prices.values,
            name="SPY",
            line={"color": "black", "width": 1},
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=fast_ma.index,
            y=fast_ma.values,
            name=f"Fast MA ({fast_window})",
            line={"color": "green"},
        ),
        row=2,
        col=1,
    )
    fig.add_trace(
        go.Scatter(
            x=slow_ma.index,
            y=slow_ma.values,
            name=f"Slow MA ({slow_window})",
            line={"color": "red"},
        ),
        row=2,
        col=1,
    )

    # Add vertical line at train/test split
    for row in [1, 2]:
        fig.add_vline(
            x=str(split_date),
            line={"color": "orange", "dash": "dot", "width": 2},
            row=row,
            col=1,
        )

    fig.update_layout(
        title="MA Crossover Strategy Backtest",
        hovermode="x unified",
        height=700,
        legend={"yanchor": "top", "y": 0.99, "xanchor": "left", "x": 0.01},
    )
    fig.update_yaxes(title_text="Equity (Normalized)", row=1, col=1)
    fig.update_yaxes(title_text="Price", row=2, col=1)

    return fig


def main() -> None:
    """Run MA crossover backtest with optimization."""
    # Configuration
    initial_capital = 100_000
    cost_pct = 0.0005  # 5 bps

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
    fast, slow, train_sharpe = optimize_ma_params(train_prices, "SPY", initial_capital)
    print(f"Best params: fast={fast}, slow={slow} (train Sharpe={train_sharpe:.2f})")

    # Backtest on train period with optimized params
    train_signal = ma_crossover_signal(train_prices["SPY"], fast, slow)
    train_bt = run_backtest(train_prices, train_signal, initial_capital, cost_pct)
    print_results("Train Period Results", train_bt)

    # Backtest on test period (out-of-sample)
    test_signal = ma_crossover_signal(test_prices["SPY"], fast, slow)
    test_bt = run_backtest(test_prices, test_signal, initial_capital, cost_pct)
    print_results("Test Period Results (Out-of-Sample)", test_bt)

    # Buy & hold comparison
    bh_train_signal = pd.Series(1, index=train_prices.index)
    bh_test_signal = pd.Series(1, index=test_prices.index)
    bh_train = run_backtest(train_prices, bh_train_signal, initial_capital)
    bh_test = run_backtest(test_prices, bh_test_signal, initial_capital)
    print("\nBuy & Hold Comparison:")
    print(
        f"  Train - Sharpe: {bh_train.metrics['sharpe']:.2f}, CAGR: {bh_train.metrics['cagr']:.1%}"
    )
    print(
        f"  Test  - Sharpe: {bh_test.metrics['sharpe']:.2f}, CAGR: {bh_test.metrics['cagr']:.1%}"
    )

    # Full period backtest for charting
    full_signal = ma_crossover_signal(prices["SPY"], fast, slow)
    full_bt = run_backtest(prices, full_signal, initial_capital, cost_pct)
    bh_full_signal = pd.Series(1, index=prices.index)
    bh_full = run_backtest(prices, bh_full_signal, initial_capital)

    # Plot
    fig = plot_backtest(
        prices=prices["SPY"],
        strategy_equity=full_bt.equity,
        bh_equity=bh_full.equity,
        fast_window=fast,
        slow_window=slow,
        split_date=split.test_start,
    )
    fig.show()


if __name__ == "__main__":
    main()
