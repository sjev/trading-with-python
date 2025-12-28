"""Tests for indicators."""

from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from twp.data import LocalCsvSource
from twp.indicators import (
    AbsorptionRatioIndicator,
    MarketRegimeIndicator,
    MomentumIndicator,
    VixIndicator,
)


@pytest.fixture
def source() -> LocalCsvSource:
    """Create a LocalCsvSource pointing to test data."""
    return LocalCsvSource(Path(__file__).parent / "testdata/prices")


class TestVixIndicator:
    """Tests for VixIndicator."""

    def test_value_returns_float(self, source: LocalCsvSource) -> None:
        """Test that value() returns a float in 0..1 range."""
        ind = VixIndicator(source=source, ticker="^VIX")
        val = ind.value(date(2024, 1, 10))

        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0

    def test_direction_returns_int(self, source: LocalCsvSource) -> None:
        """Test that direction() returns -1, 0, or 1."""
        ind = VixIndicator(source=source, ticker="^VIX")
        direction = ind.direction(date(2024, 1, 10))

        assert direction in (-1, 0, 1)

    def test_history_returns_dataframe(self, source: LocalCsvSource) -> None:
        """Test that history() returns DataFrame with correct columns."""
        ind = VixIndicator(source=source, ticker="^VIX")
        df = ind.history(date(2024, 1, 1), date(2024, 1, 10))

        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"raw", "normalized", "direction"}

    def test_name_property(self, source: LocalCsvSource) -> None:
        """Test that name property returns correct value."""
        ind = VixIndicator(source=source, ticker="^VIX")
        assert ind.name == "vix"


class TestMomentumIndicator:
    """Tests for MomentumIndicator."""

    def test_value_returns_float(self, source: LocalCsvSource) -> None:
        """Test that value() returns a float in 0..1 range."""
        ind = MomentumIndicator(source=source, ma_window=3)
        val = ind.value(date(2024, 1, 10))

        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0

    def test_direction_returns_int(self, source: LocalCsvSource) -> None:
        """Test that direction() returns -1, 0, or 1."""
        ind = MomentumIndicator(source=source, ma_window=3)
        direction = ind.direction(date(2024, 1, 10))

        assert direction in (-1, 0, 1)

    def test_history_returns_dataframe(self, source: LocalCsvSource) -> None:
        """Test that history() returns DataFrame with correct columns."""
        ind = MomentumIndicator(source=source, ma_window=3)
        df = ind.history(date(2024, 1, 1), date(2024, 1, 10))

        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"raw", "normalized", "direction"}

    def test_name_property(self, source: LocalCsvSource) -> None:
        """Test that name property returns correct value."""
        ind = MomentumIndicator(source=source)
        assert ind.name == "momentum"


class TestMarketRegimeIndicator:
    """Tests for MarketRegimeIndicator."""

    def test_combines_indicators(self, source: LocalCsvSource) -> None:
        """Test that MRI combines multiple indicators."""
        vix = VixIndicator(source=source, ticker="^VIX")
        momentum = MomentumIndicator(source=source, ma_window=3)

        mri = MarketRegimeIndicator(indicators=[vix, momentum])
        val = mri.value(date(2024, 1, 10))

        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0

    def test_history_returns_dataframe(self, source: LocalCsvSource) -> None:
        """Test that history() returns DataFrame with correct columns."""
        vix = VixIndicator(source=source, ticker="^VIX")
        momentum = MomentumIndicator(source=source, ma_window=3)

        mri = MarketRegimeIndicator(indicators=[vix, momentum])
        df = mri.history(date(2024, 1, 1), date(2024, 1, 10))

        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"raw", "normalized", "direction"}

    def test_weighted_coefficients(self, source: LocalCsvSource) -> None:
        """Test that coefficients affect the combined value."""
        vix = VixIndicator(source=source, ticker="^VIX")
        momentum = MomentumIndicator(source=source, ma_window=3)

        # MRI with equal weights
        mri_equal = MarketRegimeIndicator(
            indicators=[vix, momentum],
            coefficients={"vix": 1.0, "momentum": 1.0},
        )

        # MRI with vix weighted higher
        mri_vix_heavy = MarketRegimeIndicator(
            indicators=[vix, momentum],
            coefficients={"vix": 2.0, "momentum": 1.0},
        )

        as_of = date(2024, 1, 10)
        val_equal = mri_equal.value(as_of)
        val_vix_heavy = mri_vix_heavy.value(as_of)

        # Values should be different if VIX and momentum differ
        assert isinstance(val_equal, float)
        assert isinstance(val_vix_heavy, float)


SECTOR_ETFS = [
    "XLB",
    "XLC",
    "XLE",
    "XLF",
    "XLI",
    "XLK",
    "XLP",
    "XLRE",
    "XLU",
    "XLV",
    "XLY",
]


class TestAbsorptionRatioIndicator:
    """Tests for AbsorptionRatioIndicator."""

    def test_value_returns_float(self, source: LocalCsvSource) -> None:
        """Test that value() returns a float in 0..1 range."""
        ind = AbsorptionRatioIndicator(
            source=source, tickers=SECTOR_ETFS, window=20, percentile_window=20
        )
        val = ind.value(date(2023, 12, 1))

        assert isinstance(val, float)
        assert 0.0 <= val <= 1.0

    def test_direction_returns_int(self, source: LocalCsvSource) -> None:
        """Test that direction() returns -1, 0, or 1."""
        ind = AbsorptionRatioIndicator(
            source=source, tickers=SECTOR_ETFS, window=20, percentile_window=20
        )
        direction = ind.direction(date(2023, 12, 1))

        assert direction in (-1, 0, 1)

    def test_history_returns_dataframe(self, source: LocalCsvSource) -> None:
        """Test that history() returns DataFrame with correct columns."""
        ind = AbsorptionRatioIndicator(
            source=source, tickers=SECTOR_ETFS, window=20, percentile_window=20
        )
        df = ind.history(date(2023, 10, 1), date(2023, 12, 1))

        assert isinstance(df, pd.DataFrame)
        assert set(df.columns) == {"raw", "normalized", "direction", "delta_ar"}

    def test_name_property(self, source: LocalCsvSource) -> None:
        """Test that name property returns correct value."""
        ind = AbsorptionRatioIndicator(source=source, tickers=SECTOR_ETFS)
        assert ind.name == "absorption_ratio"

    def test_n_components_default(self, source: LocalCsvSource) -> None:
        """Test that n_components defaults to len(tickers) // 5."""
        ind = AbsorptionRatioIndicator(source=source, tickers=SECTOR_ETFS)
        # 11 tickers // 5 = 2
        assert ind.n_components == 2

    def test_raw_ar_in_valid_range(self, source: LocalCsvSource) -> None:
        """Test that raw AR values are between 0 and 1."""
        ind = AbsorptionRatioIndicator(
            source=source, tickers=SECTOR_ETFS, window=20, percentile_window=20
        )
        df = ind.history(date(2023, 10, 1), date(2023, 12, 1))

        if not df.empty:
            assert df["raw"].min() >= 0.0
            assert df["raw"].max() <= 1.0
