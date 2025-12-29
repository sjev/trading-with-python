"""Backtest engine - functional approach."""

from typing import TypedDict

import pandas as pd


class BacktestResult(TypedDict):
    """Result of a backtest run."""

    equity: pd.Series
    pnl: pd.Series
    cash: pd.Series
    positions: pd.DataFrame


def backtest(
    prices: pd.DataFrame,
    shares: pd.DataFrame,
    initial_capital: float,
    cost_per_share: float = 0.0,
    cost_pct: float = 0.0,
) -> BacktestResult:
    """Run backtest with shares-based positions.

    Args:
        prices: DataFrame of asset prices (index=dates, columns=assets)
        shares: DataFrame of position sizes in shares (same shape as prices)
        initial_capital: Starting cash amount
        cost_per_share: Fixed cost per share traded (e.g., $0.005)
        cost_pct: Cost as fraction of trade value (e.g., 0.0005 for 5bps)

    Returns:
        Dict with equity, pnl, cash, and positions series/dataframes
    """
    # Align prices and shares
    common_cols = prices.columns.intersection(shares.columns)
    common_idx = prices.index.intersection(shares.index)
    prices = prices.loc[common_idx, common_cols]
    shares = shares.loc[common_idx, common_cols]

    # Position changes (first row is initial position)
    delta_shares = shares.diff()
    delta_shares.iloc[0] = shares.iloc[0]

    # Trade value and costs
    trade_value = delta_shares * prices
    per_share_cost = delta_shares.abs() * cost_per_share
    pct_cost = trade_value.abs() * cost_pct
    costs = (per_share_cost + pct_cost).sum(axis=1)

    # Cash flow (negative when buying)
    cash_flow = -trade_value.sum(axis=1) - costs
    cash = initial_capital + cash_flow.cumsum()

    # Position value and equity
    position_value = (shares * prices).sum(axis=1)
    equity = cash + position_value

    # Daily PnL
    pnl = equity.diff()
    pnl.iloc[0] = equity.iloc[0] - initial_capital

    return {
        "equity": equity,
        "pnl": pnl,
        "cash": cash,
        "positions": shares * prices,
    }
