"""Performance metrics for backtesting."""

import numpy as np
import pandas as pd


def sharpe(returns: pd.Series, risk_free: float = 0.0, periods: int = 252) -> float:
    """Calculate annualized Sharpe ratio.

    Args:
        returns: Daily returns series
        risk_free: Risk-free rate (annualized, default 0)
        periods: Trading periods per year (default 252)

    Returns:
        Annualized Sharpe ratio
    """
    excess = returns - risk_free / periods
    if excess.std() == 0:
        return 0.0
    return float(np.sqrt(periods) * excess.mean() / excess.std())


def max_drawdown(equity: pd.Series) -> float:
    """Calculate maximum drawdown.

    Args:
        equity: Equity curve (cumulative returns or prices)

    Returns:
        Maximum drawdown as a positive fraction (e.g., 0.20 = 20% drawdown)
    """
    peak = equity.expanding().max()
    drawdown = (equity - peak) / peak
    return float(-drawdown.min())


def cagr(equity: pd.Series, periods: int = 252) -> float:
    """Calculate Compound Annual Growth Rate.

    Args:
        equity: Equity curve (starting from 1.0 or initial value)
        periods: Trading periods per year (default 252)

    Returns:
        CAGR as a fraction (e.g., 0.10 = 10% annual return)
    """
    if len(equity) < 2:
        return 0.0

    start_val = equity.iloc[0]
    end_val = equity.iloc[-1]
    n_periods = len(equity)
    years = n_periods / periods

    if start_val <= 0 or years <= 0:
        return 0.0

    return float((end_val / start_val) ** (1 / years) - 1)


def volatility(returns: pd.Series, periods: int = 252) -> float:
    """Calculate annualized volatility.

    Args:
        returns: Daily returns series
        periods: Trading periods per year (default 252)

    Returns:
        Annualized volatility as a fraction
    """
    return float(returns.std() * np.sqrt(periods))


def turnover(weights: pd.DataFrame) -> float:
    """Calculate average daily turnover.

    Args:
        weights: DataFrame of portfolio weights over time

    Returns:
        Average daily turnover (sum of absolute weight changes)
    """
    if len(weights) < 2:
        return 0.0

    daily_turnover = weights.diff().abs().sum(axis=1)
    return float(daily_turnover.mean())
