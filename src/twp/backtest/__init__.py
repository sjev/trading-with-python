"""KISS backtesting framework."""

from twp.backtest.engine import BacktestResult, backtest
from twp.backtest.metrics import (
    Metrics,
    cagr,
    max_drawdown,
    metrics,
    sharpe,
    summary,
    turnover,
    volatility,
)
from twp.backtest.split import Split, train_test_split

__all__ = [
    "BacktestResult",
    "Metrics",
    "Split",
    "backtest",
    "cagr",
    "max_drawdown",
    "metrics",
    "sharpe",
    "summary",
    "train_test_split",
    "turnover",
    "volatility",
]
