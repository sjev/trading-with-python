"""Train/test split utilities for backtesting."""

from dataclasses import dataclass
from datetime import date

import pandas as pd


@dataclass
class Split:
    """A train/test split with date boundaries."""

    train_start: date
    train_end: date
    test_start: date
    test_end: date

    def slice_train(self, data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
        """Slice data to training period."""
        return data.loc[str(self.train_start) : str(self.train_end)]  # type: ignore[misc]

    def slice_test(self, data: pd.DataFrame | pd.Series) -> pd.DataFrame | pd.Series:
        """Slice data to test period."""
        return data.loc[str(self.test_start) : str(self.test_end)]  # type: ignore[misc]


def train_test_split(
    data: pd.DataFrame | pd.Series,
    train_ratio: float = 0.7,
) -> Split:
    """Create a train/test split from data.

    Args:
        data: Time series data with DatetimeIndex
        train_ratio: Fraction of data for training (default 0.7)

    Returns:
        Split object with date boundaries
    """
    if not isinstance(data.index, pd.DatetimeIndex):
        raise ValueError("Data must have DatetimeIndex")

    n = len(data)
    train_end_idx = int(n * train_ratio)

    train_start = data.index[0].date()
    train_end = data.index[train_end_idx - 1].date()
    test_start = data.index[train_end_idx].date()
    test_end = data.index[-1].date()

    return Split(
        train_start=train_start,
        train_end=train_end,
        test_start=test_start,
        test_end=test_end,
    )
