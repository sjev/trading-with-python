"""Yahoo Finance data source with file-based caching."""

from datetime import date
from pathlib import Path

import pandas as pd
import yfinance as yf
from platformdirs import user_cache_dir


class YahooSource:
    """Yahoo Finance data source with file-based caching."""

    def __init__(self, cache_dir: Path | None = None):
        self._cache_dir = cache_dir or Path(user_cache_dir("twp")) / "yahoo"
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    @property
    def cache_dir(self) -> Path:
        """Directory where cached data files are stored."""
        return self._cache_dir

    def get(
        self,
        ticker: str,
        start: date,
        end: date | None = None,
    ) -> pd.Series | pd.DataFrame:
        """Fetch data for a ticker, using cache if available."""
        end = end or date.today()
        cache_path = self._cache_path(ticker)

        # Try to load from cache
        if cache_path.exists():
            df = self._read_cache(cache_path)
            # Check if cache covers requested range
            if not df.empty and df.index.min().date() <= start:
                return self._slice_and_return(df, ticker, start, end)

        # Download and cache
        df = self._download(ticker)
        if df.empty:
            raise ValueError(f"No data available for ticker: {ticker}")

        self._write_cache(df, cache_path)
        return self._slice_and_return(df, ticker, start, end)

    def _cache_path(self, ticker: str) -> Path:
        """Get cache file path for a ticker."""
        # Replace special characters in ticker names
        safe_name = ticker.replace("^", "_").replace("/", "_")
        return self._cache_dir / f"{safe_name}.csv"

    def _download(self, ticker: str, period: str = "20y") -> pd.DataFrame:
        """Download data from Yahoo Finance."""
        df = yf.download(
            ticker, period=period, progress=False, auto_adjust=True, threads=False
        )
        if df.empty:
            return df

        # Handle multi-level columns from newer yfinance versions
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Normalize index to date
        df.index = pd.to_datetime(df.index).date
        df.index = pd.DatetimeIndex(df.index)
        df.index.name = "Date"
        return df

    def _read_cache(self, path: Path) -> pd.DataFrame:
        """Read cached data from CSV."""
        return pd.read_csv(path, index_col="Date", parse_dates=True)

    def _write_cache(self, df: pd.DataFrame, path: Path) -> None:
        """Write data to cache."""
        df.to_csv(path, float_format="%.2f")

    def _slice_and_return(
        self,
        df: pd.DataFrame,
        ticker: str,
        start: date,
        end: date,
    ) -> pd.Series | pd.DataFrame:
        """Slice data to requested range and return appropriate type."""
        start_dt = pd.Timestamp(start)
        end_dt = pd.Timestamp(end)
        df = df.loc[start_dt:end_dt]

        # For single-value tickers (VIX, etc.), return Close as Series
        is_ohlcv = "Close" in df.columns and len(df.columns) <= 6
        if is_ohlcv and self._is_single_value_ticker(ticker):
            series = df["Close"]
            series.name = ticker
            return series

        return df

    def _is_single_value_ticker(self, ticker: str) -> bool:
        """Determine if ticker should return Series or DataFrame."""
        # VIX and similar indices are single-value
        single_value_prefixes = ("^VIX", "^VXV")
        return ticker.startswith(single_value_prefixes)

    def refresh(self, ticker: str) -> None:
        """Force re-download of a ticker's data."""
        cache_path = self._cache_path(ticker)
        if cache_path.exists():
            cache_path.unlink()
        df = self._download(ticker)
        if not df.empty:
            self._write_cache(df, cache_path)
