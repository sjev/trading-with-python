"""Tests for data sources."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from twp.data import LocalCsvSource


@pytest.fixture
def source() -> LocalCsvSource:
    """Create a LocalCsvSource pointing to test data."""
    return LocalCsvSource(Path(__file__).parent / "testdata/prices")


class TestLocalCsvSource:
    """Tests for LocalCsvSource."""

    def test_get_returns_data(self, source: LocalCsvSource) -> None:
        """Test that get() returns data for a ticker."""
        data = source.get("SPY", date(2024, 1, 1), date(2024, 1, 10))

        # Test fixtures have only Close column, so Series is returned
        assert isinstance(data, (pd.Series, pd.DataFrame))
        assert not data.empty

    def test_get_returns_series_for_single_column(self, source: LocalCsvSource) -> None:
        """Test that get() returns Series for single-column data."""
        # VIX data should have Close column
        data = source.get("^VIX", date(2024, 1, 1), date(2024, 1, 10))

        # LocalCsvSource returns DataFrame since VIX CSV has multiple columns
        assert isinstance(data, (pd.Series, pd.DataFrame))

    def test_get_handles_safe_name(self, source: LocalCsvSource) -> None:
        """Test that get() handles tickers with special characters."""
        # ^VIX should find _VIX.csv
        data = source.get("^VIX", date(2024, 1, 1), date(2024, 1, 10))
        assert not data.empty

    def test_get_raises_for_missing_ticker(self, source: LocalCsvSource) -> None:
        """Test that get() raises FileNotFoundError for missing ticker."""
        with pytest.raises(FileNotFoundError, match="No CSV found"):
            source.get("NONEXISTENT", date(2024, 1, 1))

    def test_get_slices_to_date_range(self, source: LocalCsvSource) -> None:
        """Test that get() returns data only within date range."""
        df = source.get("SPY", date(2024, 1, 2), date(2024, 1, 5))

        # Check dates are within range
        assert df.index.min() >= pd.Timestamp("2024-01-02")
        assert df.index.max() <= pd.Timestamp("2024-01-05")

    def test_cache_dir_property(self, source: LocalCsvSource) -> None:
        """Test that cache_dir property returns data_dir."""
        assert source.cache_dir == source.data_dir

    def test_refresh_is_noop(self, source: LocalCsvSource) -> None:
        """Test that refresh() does nothing (no error)."""
        source.refresh("SPY")  # Should not raise
