"""VIX-based market fear indicator."""

from __future__ import annotations

from datetime import date, timedelta
from typing import TYPE_CHECKING

import pandas as pd

from .normalization import LookupTable, compute_direction

if TYPE_CHECKING:
    from twp.data.protocol import DataSourceProtocol

# VIX level -> normalized score (0 = calm, 1 = panic)
VIX_SCALE = LookupTable(
    x_values=(10, 15, 20, 25, 30, 40, 60),
    y_values=(0.0, 0.1, 0.25, 0.4, 0.55, 0.8, 1.0),
)


class VixIndicator:
    """VIX-based market fear indicator.

    High VIX = high fear = high score (0 = calm, 1 = panic).
    Uses FRED VIXCLS data by default.
    """

    def __init__(
        self,
        source: DataSourceProtocol,
        ticker: str = "VIXCLS",
    ):
        self._source = source
        self._ticker = ticker

    @property
    def name(self) -> str:
        return "vix"

    def value(self, as_of: date | None = None) -> float:
        """Get normalized VIX score (0..1) for a specific date."""
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
        # Need buffer for direction calculation (uses 5-day window)
        start = as_of - timedelta(days=30)
        return self._compute_full_history(start, as_of)

    def _compute_full_history(self, start: date, end: date) -> pd.DataFrame:
        """Compute full history DataFrame with raw, normalized, direction."""
        raw = self._source.get(self._ticker, start, end)

        if isinstance(raw, pd.DataFrame):
            raw = raw["Close"]

        normalized = VIX_SCALE.apply(raw)
        direction = compute_direction(normalized)

        return pd.DataFrame(
            {"raw": raw, "normalized": normalized, "direction": direction}
        ).dropna()
