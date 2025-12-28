"""Normalization utilities for indicator components."""

from bisect import bisect_right
from typing import TypeVar

import numpy as np
import pandas as pd

T = TypeVar("T", pd.Series, pd.DataFrame)


class LookupTable:
    """Piecewise linear interpolation from a lookup table."""

    def __init__(self, x_values: tuple[float, ...], y_values: tuple[float, ...]):
        if len(x_values) != len(y_values):
            raise ValueError("x_values and y_values must have same length")
        if len(x_values) < 2:
            raise ValueError("Need at least 2 points")
        self._x = x_values
        self._y = y_values

    def __call__(self, x: float) -> float:
        """Interpolate single value."""
        import math

        if math.isnan(x):
            return float("nan")
        if x <= self._x[0]:
            return self._y[0]
        if x >= self._x[-1]:
            return self._y[-1]

        i = bisect_right(self._x, x)
        x0, x1 = self._x[i - 1], self._x[i]
        y0, y1 = self._y[i - 1], self._y[i]
        t = (x - x0) / (x1 - x0)
        return y0 + t * (y1 - y0)

    def apply(self, series: pd.Series) -> pd.Series:
        """Apply to pandas Series."""
        return series.apply(self.__call__)


def percentile_rank(
    series: pd.Series, window: int = 252, invert: bool = False
) -> pd.Series:
    """Calculate rolling percentile rank (0..1).

    For each value, compute its percentile rank within the trailing window.
    If invert=True, returns 1 - percentile (high raw value = low score).

    Args:
        series: Input time series
        window: Lookback window for percentile calculation
        invert: If True, invert the percentile (useful for fear indicators)

    Returns:
        Series with percentile ranks (0..1)
    """

    def rank_last(arr: pd.Series) -> float:
        if len(arr) < 2:
            return 0.5  # Neutral if insufficient data
        last_val = arr.iloc[-1]
        return (arr < last_val).sum() / len(arr)

    score = series.rolling(window=window).apply(rank_last, raw=False)
    return 1.0 - score if invert else score


def linear_scale(
    series: pd.Series, low_value: float, high_value: float, invert: bool = False
) -> pd.Series:
    """Scale series linearly from [low_value, high_value] to [0, 1].

    Values outside range are clipped to [0, 1].
    If invert=True, low_value maps to 1 and high_value maps to 0.

    Args:
        series: Input time series
        low_value: Value that maps to 0 (or 1 if inverted)
        high_value: Value that maps to 1 (or 0 if inverted)
        invert: If True, reverse the scaling

    Returns:
        Series scaled to 0..1 range
    """
    scaled = (series - low_value) / (high_value - low_value)
    scaled = scaled.clip(0, 1)
    return 1.0 - scaled if invert else scaled


def compute_direction(series: pd.Series, window: int = 5) -> pd.Series:
    """Compute trend direction based on short-term slope.

    Args:
        series: Normalized indicator values (0..1)
        window: Window for trend calculation

    Returns:
        Series with direction: -1 (bearish), 0 (neutral), 1 (bullish)
    """
    # Simple approach: compare current to moving average
    ma = series.rolling(window=window).mean()
    diff = series - ma

    # Threshold for significant change (can be tuned)
    threshold = 0.02

    direction = pd.Series(0, index=series.index)
    direction[diff > threshold] = 1
    direction[diff < -threshold] = -1
    return direction.astype(int)


def log_returns(prices: T) -> T:
    """Calculate log returns from price series.

    Log returns are computed as ln(P_t / P_{t-1}).

    Args:
        prices: Price series or DataFrame with price columns.

    Returns:
        Log returns with same shape and index as input.
        First row will be NaN (no prior price available).
    """
    result: T = np.log(prices / prices.shift(1))  # type: ignore[assignment]
    return result
