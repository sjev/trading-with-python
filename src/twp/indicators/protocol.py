"""Indicator protocol definition."""

from datetime import date
from typing import Protocol

import pandas as pd


class IndicatorProtocol(Protocol):
    """Transforms raw data into normalized signals."""

    @property
    def name(self) -> str:
        """Unique identifier for the indicator."""
        ...

    def value(self, as_of: date | None = None) -> float:
        """Get normalized value (0..1) for a specific date.

        Args:
            as_of: Date to get value for (None means today/latest)

        Returns:
            Normalized value between 0 and 1
        """
        ...

    def direction(self, as_of: date | None = None) -> int:
        """Get trend direction for a specific date.

        Args:
            as_of: Date to get direction for (None means today/latest)

        Returns:
            -1 (bearish), 0 (neutral), or 1 (bullish)
        """
        ...

    def history(
        self,
        start: date,
        end: date | None = None,
    ) -> pd.DataFrame:
        """Get historical data for a date range.

        Args:
            start: Start date
            end: End date (None means today)

        Returns:
            DataFrame with columns: raw, normalized, direction
        """
        ...
