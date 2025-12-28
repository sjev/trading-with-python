"""Local CSV data source for testing and offline use."""

from datetime import date
from pathlib import Path

import pandas as pd


class LocalCsvSource:
    """Load data from local CSV files (for testing/offline use)."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir

    @property
    def cache_dir(self) -> Path:
        """Directory where data files are stored."""
        return self.data_dir

    def get(
        self,
        ticker: str,
        start: date,
        end: date | None = None,
    ) -> pd.Series | pd.DataFrame:
        """Load data from CSV file."""
        end = end or date.today()

        # Handle special characters in ticker names
        safe_name = ticker.replace("^", "_").replace("/", "_")

        # Try both original and safe name patterns
        for name in [ticker, safe_name]:
            path = self.data_dir / f"{name}.csv"
            if path.exists():
                break
        else:
            raise FileNotFoundError(f"No CSV found for ticker: {ticker}")

        df = pd.read_csv(path, index_col="Date", parse_dates=True)

        # Slice to date range
        start_dt = pd.Timestamp(start)
        end_dt = pd.Timestamp(end)
        df = df.loc[start_dt:end_dt]

        # Return Series if only Close column, otherwise DataFrame
        if "Close" in df.columns and len(df.columns) == 1:
            series = df["Close"]
            series.name = ticker
            return series

        return df

    def refresh(self, ticker: str) -> None:
        """No-op for local CSV source."""
        pass
