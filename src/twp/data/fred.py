"""FRED data source with file-based caching."""

import os
from datetime import date
from pathlib import Path

import pandas as pd
from fredapi import Fred
from platformdirs import user_cache_dir


class FredSource:
    """FRED data source with file-based caching."""

    def __init__(self, api_key: str | None = None, cache_dir: Path | None = None):
        self.api_key = api_key or os.getenv("FRED_API_KEY") or os.getenv("FRED_TOKEN")
        if not self.api_key:
            raise ValueError("FRED_API_KEY not found in environment")

        self._cache_dir = cache_dir or Path(user_cache_dir("twp")) / "fred"
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._client: Fred | None = None

    @property
    def cache_dir(self) -> Path:
        """Directory where cached data files are stored."""
        return self._cache_dir

    @property
    def client(self) -> Fred:
        """Lazy-load FRED client."""
        if self._client is None:
            self._client = Fred(api_key=self.api_key)
        return self._client

    def get(
        self,
        ticker: str,
        start: date,
        end: date | None = None,
    ) -> pd.Series:
        """Fetch FRED series data, using cache if available."""
        end = end or date.today()
        cache_path = self._cache_path(ticker)

        # Try to load from cache
        if cache_path.exists():
            series = self._read_cache(cache_path)
            if not series.empty and series.index.min().date() <= start:
                return self._slice(series, ticker, start, end)

        # Download and cache
        series = self._download(ticker)
        if series.empty:
            raise ValueError(f"No data available for FRED series: {ticker}")

        self._write_cache(series, cache_path)
        return self._slice(series, ticker, start, end)

    def _cache_path(self, ticker: str) -> Path:
        """Get cache file path for a series."""
        return self._cache_dir / f"{ticker}.csv"

    def _download(self, ticker: str) -> pd.Series:
        """Download data from FRED."""
        series: pd.Series = self.client.get_series(ticker)
        series.index = pd.to_datetime(series.index)
        series.index.name = "Date"
        series.name = ticker
        return pd.to_numeric(series, errors="coerce")

    def _read_cache(self, path: Path) -> pd.Series:
        """Read cached data from CSV."""
        df = pd.read_csv(path, index_col="Date", parse_dates=True)
        series = df.iloc[:, 0]
        series.name = df.columns[0]
        return series

    def _write_cache(self, series: pd.Series, path: Path) -> None:
        """Write series to cache."""
        series.to_csv(path)

    def _slice(
        self,
        series: pd.Series,
        ticker: str,
        start: date,
        end: date,
    ) -> pd.Series:
        """Slice data to requested range."""
        start_dt = pd.Timestamp(start)
        end_dt = pd.Timestamp(end)
        result = series.loc[start_dt:end_dt]
        result.name = ticker
        return result

    def refresh(self, ticker: str) -> None:
        """Force re-download of a series."""
        cache_path = self._cache_path(ticker)
        series = self._download(ticker)

        if cache_path.exists():
            cache_path.unlink()
        if not series.empty:
            self._write_cache(series, cache_path)
