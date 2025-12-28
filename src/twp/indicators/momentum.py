"""Price momentum indicator."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import pandas as pd

from .normalization import compute_direction, linear_scale

if TYPE_CHECKING:
    from twp.data.protocol import DataSourceProtocol


class MomentumIndicator:
    """Price momentum indicator.

    Measures distance from moving average, scaled to 0..1.
    Positive momentum (above MA) = high score.
    """

    def __init__(
        self,
        source: DataSourceProtocol,
        ticker: str = "SPY",
        ma_window: int = 125,
        low_pct: float = -10.0,
        high_pct: float = 10.0,
    ):
        self.source = source
        self.ticker = ticker
        self.ma_window = ma_window
        self.low_pct = low_pct
        self.high_pct = high_pct

    @property
    def name(self) -> str:
        return "momentum"

    def value(self, as_of: date | None = None) -> float:
        """Get normalized momentum score (0..1) for a specific date."""
        df = self._get_history(as_of)
        if df.empty:
            return 0.5

        as_of = as_of or date.today()
        if as_of in df.index:
            return float(df.loc[as_of, "normalized"])  # type: ignore

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
        start = as_of - timedelta(days=self.ma_window * 2)
        return self._compute_full_history(start, as_of)

    def _compute_full_history(self, start: date, end: date) -> pd.DataFrame:
        """Compute full history DataFrame with raw, normalized, direction."""
        buffer_start = start - timedelta(days=self.ma_window)
        raw_data = self.source.get(self.ticker, buffer_start, end)

        # Extract Close price if DataFrame
        prices = raw_data["Close"] if isinstance(raw_data, pd.DataFrame) else raw_data

        # Compute percent from moving average
        ma = prices.rolling(self.ma_window).mean()
        pct_from_ma = (prices - ma) / ma * 100

        # Normalize to 0..1
        normalized = linear_scale(pct_from_ma, self.low_pct, self.high_pct)

        # Compute direction
        direction = compute_direction(normalized)

        df = pd.DataFrame(
            {
                "raw": pct_from_ma,
                "normalized": normalized,
                "direction": direction,
            }
        )

        return df.loc[pd.Timestamp(start) : pd.Timestamp(end)].dropna()
