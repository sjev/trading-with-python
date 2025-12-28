"""Absorption Ratio indicator for market fragility measurement."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import numpy as np
import pandas as pd

from .normalization import compute_direction, log_returns, percentile_rank

if TYPE_CHECKING:
    from twp.data.protocol import DataSourceProtocol


class AbsorptionRatioIndicator:
    """Absorption Ratio indicator for measuring market fragility.

    The Absorption Ratio measures what fraction of total variance is explained
    by the top principal components. High AR indicates tightly coupled markets,
    which signals fragility.

    Formula: AR = sum(top N eigenvalues) / sum(all eigenvalues)
    where N = n_assets // 5 (default).

    Reference: Kritzman et al. - "Principal Components as a Measure of
    Systemic Risk" - JPM 2011
    """

    def __init__(
        self,
        source: DataSourceProtocol,
        tickers: list[str],
        window: int = 252,
        n_components: int | None = None,
        percentile_window: int = 252,
        shift_window: int = 15,
    ):
        """Initialize AbsorptionRatioIndicator.

        Args:
            source: Data source for fetching prices.
            tickers: List of ticker symbols (e.g., sector ETFs).
            window: Rolling window for return covariance (default 252 trading days).
            n_components: Number of top components for AR. Default: len(tickers) // 5.
            percentile_window: Window for percentile rank normalization.
            shift_window: Window for delta_ar calculation (default 15 days per paper).
        """
        self.source = source
        self.tickers = tickers
        self.window = window
        self.n_components = n_components or max(1, len(tickers) // 5)
        self.percentile_window = percentile_window
        self.shift_window = shift_window

    @property
    def name(self) -> str:
        return "absorption_ratio"

    def value(self, as_of: date | None = None) -> float:
        """Get normalized AR score (0..1) for a specific date.

        High AR (fragile market) maps to high score.
        """
        df = self._get_history(as_of)
        if df.empty:
            return 0.5  # Neutral if no data

        as_of = as_of or date.today()
        if as_of in df.index:
            return float(df.loc[as_of, "normalized"])  # type: ignore

        # Get closest date before as_of
        valid = df[df.index <= pd.Timestamp(as_of)]
        if valid.empty:
            return 0.5
        return float(valid.iloc[-1]["normalized"])

    def direction(self, as_of: date | None = None) -> int:
        """Get trend direction (-1, 0, 1) for a specific date."""
        df = self._get_history(as_of)
        if df.empty:
            return 0

        as_of = as_of or date.today()
        if as_of in df.index:
            return int(df.loc[as_of, "direction"])  # type: ignore

        valid = df[df.index <= pd.Timestamp(as_of)]
        if valid.empty:
            return 0
        return int(valid.iloc[-1]["direction"])

    def history(
        self,
        start: date,
        end: date | None = None,
    ) -> pd.DataFrame:
        """Get historical data with raw, normalized, direction columns."""
        end = end or date.today()
        df = self._compute_full_history(start, end)
        return df.loc[pd.Timestamp(start) : pd.Timestamp(end)]

    def _get_history(self, as_of: date | None = None) -> pd.DataFrame:
        """Get or compute history up to as_of date."""
        as_of = as_of or date.today()
        # Need extra history for rolling window calculation
        start = as_of - timedelta(days=self.window * 2)
        return self._compute_full_history(start, as_of)

    def _compute_full_history(self, start: date, end: date) -> pd.DataFrame:
        """Compute full history DataFrame with raw, normalized, direction."""
        # Fetch price data with buffer for rolling calculations
        buffer_start = start - timedelta(days=self.window + self.percentile_window)
        prices = self._fetch_prices(buffer_start, end)

        if prices.empty:
            return pd.DataFrame(columns=["raw", "delta_ar", "normalized", "direction"])

        # Calculate log returns
        returns_raw = log_returns(prices).dropna()
        assert isinstance(returns_raw, pd.DataFrame)
        returns = returns_raw

        if len(returns) < self.window:
            return pd.DataFrame(columns=["raw", "delta_ar", "normalized", "direction"])

        # Calculate rolling absorption ratio
        ar_series = self._calculate_rolling_ar(returns)

        # Calculate delta_ar: standardized shift (z-score of AR change)
        ar_shift = ar_series - ar_series.shift(self.shift_window)
        ar_rolling_std = ar_series.rolling(window=self.percentile_window).std()
        delta_ar = ar_shift / ar_rolling_std

        # Normalize using percentile rank (high AR = high score)
        normalized = percentile_rank(ar_series, window=self.percentile_window)

        # Compute direction
        direction = compute_direction(normalized)

        # Build result DataFrame
        df = pd.DataFrame(
            {
                "raw": ar_series,
                "delta_ar": delta_ar,
                "normalized": normalized,
                "direction": direction,
            }
        )

        # Slice to requested range (after rolling window warmup)
        return df.loc[pd.Timestamp(start) : pd.Timestamp(end)].dropna()

    def _fetch_prices(self, start: date, end: date) -> pd.DataFrame:
        """Fetch close prices for all tickers."""
        prices_dict = {}

        for ticker in self.tickers:
            try:
                data = self.source.get(ticker, start, end)
                if isinstance(data, pd.DataFrame):
                    prices_dict[ticker] = data["Close"]
                else:
                    prices_dict[ticker] = data
            except Exception:
                # Skip tickers that fail to load
                continue

        if not prices_dict:
            return pd.DataFrame()

        # Combine into DataFrame and forward-fill missing values
        prices = pd.DataFrame(prices_dict)
        prices = prices.ffill().dropna()
        return prices

    def _calculate_rolling_ar(self, returns: pd.DataFrame) -> pd.Series:
        """Calculate rolling absorption ratio.

        For each date, compute AR using trailing window of returns.
        """
        ar_values = []
        dates = []

        for i in range(self.window, len(returns)):
            window_returns = returns.iloc[i - self.window : i]
            ar = self._compute_ar(window_returns)
            ar_values.append(ar)
            dates.append(returns.index[i])

        return pd.Series(ar_values, index=dates, name="absorption_ratio")

    def _compute_ar(self, returns: pd.DataFrame) -> float:
        """Compute absorption ratio from return matrix.

        AR = sum(top N eigenvalues) / sum(all eigenvalues)
        """
        # Compute covariance matrix
        cov_matrix = returns.cov().values

        # Calculate eigenvalues (eigvalsh for symmetric matrix, sorted ascending)
        eigenvalues = np.linalg.eigvalsh(cov_matrix)

        # Sort descending to get largest first
        eigenvalues = np.sort(eigenvalues)[::-1]

        # AR = sum of top N / sum of all
        total_variance = eigenvalues.sum()
        if total_variance <= 0:
            return 0.5  # Neutral if no variance

        top_variance = eigenvalues[: self.n_components].sum()
        return top_variance / total_variance
