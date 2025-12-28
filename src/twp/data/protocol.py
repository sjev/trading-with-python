"""DataSource protocol definition."""

from datetime import date
from pathlib import Path
from typing import Protocol

import pandas as pd


class DataSourceProtocol(Protocol):
    """Fetches and caches raw market data."""

    def get(
        self,
        ticker: str,
        start: date,
        end: date | None = None,
    ) -> pd.Series | pd.DataFrame:
        """Fetch data for a single ticker.

        Args:
            ticker: The ticker symbol (e.g., "^VIX", "VIXCLS", "SPY")
            start: Start date for the data range
            end: End date (None means today)

        Returns:
            Series for single-value data (VIX, FRED series)
            DataFrame when OHLCV needed (price data)

        Caching is internal and transparent to the caller.
        """
        ...

    def refresh(self, ticker: str) -> None:
        """Force re-download of a ticker's cached data."""
        ...

    @property
    def cache_dir(self) -> Path:
        """Directory where cached data files are stored."""
        ...
