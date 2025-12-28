"""Minimal backtesting engine."""

from dataclasses import dataclass

import pandas as pd

from .metrics import cagr, max_drawdown, sharpe, turnover, volatility


@dataclass
class BacktestResult:
    """Results from a backtest."""

    returns: pd.Series
    equity: pd.Series
    sharpe: float
    cagr: float
    volatility: float
    max_drawdown: float
    turnover: float


def backtest(
    prices: pd.DataFrame,
    weights: pd.DataFrame,
    cost_bps: float = 0.0,
) -> BacktestResult:
    """Run a simple backtest.

    Args:
        prices: DataFrame of asset prices (columns = tickers)
        weights: DataFrame of portfolio weights (columns = tickers)
                 Weights should sum to 1.0 (or less for cash allocation)
        cost_bps: Transaction cost in basis points (default 0)

    Returns:
        BacktestResult with returns, equity curve, and metrics
    """
    # Align prices and weights
    common_cols = prices.columns.intersection(weights.columns)
    prices = prices[common_cols]
    weights = weights[common_cols]

    # Align dates
    common_idx = prices.index.intersection(weights.index)
    prices = prices.loc[common_idx]
    weights = weights.loc[common_idx]

    # Calculate asset returns
    asset_returns = prices.pct_change().fillna(0)

    # Calculate portfolio returns (weighted sum of asset returns)
    portfolio_returns = (asset_returns * weights.shift(1)).sum(axis=1)

    # Apply transaction costs
    if cost_bps > 0:
        weight_changes = weights.diff().abs().sum(axis=1)
        costs = weight_changes * cost_bps / 10000
        portfolio_returns = portfolio_returns - costs

    # Calculate equity curve (starting at 1.0)
    equity = (1 + portfolio_returns).cumprod()

    # Calculate metrics
    return BacktestResult(
        returns=portfolio_returns,
        equity=equity,
        sharpe=sharpe(portfolio_returns),
        cagr=cagr(equity),
        volatility=volatility(portfolio_returns),
        max_drawdown=max_drawdown(equity),
        turnover=turnover(weights),
    )
