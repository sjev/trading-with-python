#!/usr/bin/env python
"""Example: Calculate market indicators.

This example shows how to use the indicator classes to analyze market conditions.

Usage:
    python examples/01_indicators.py
"""

from datetime import date
from pathlib import Path

from twp.data import LocalCsvSource
from twp.indicators import (
    MarketRegimeIndicator,
    MomentumIndicator,
    VixIndicator,
)


def main() -> None:
    """Calculate and display market indicators."""
    # Use local CSV data for this example
    data_dir = Path(__file__).parent.parent / "tests/testdata/prices"
    source = LocalCsvSource(data_dir)

    # Create indicators
    vix = VixIndicator(source=source, ticker="^VIX")
    momentum = MomentumIndicator(source=source, ticker="SPY", ma_window=5)

    # Get indicator values for a specific date
    as_of = date(2024, 1, 10)
    print(f"Indicator values as of {as_of}:")
    print(f"  VIX: {vix.value(as_of):.2f} (direction: {vix.direction(as_of):+d})")
    print(
        f"  Momentum: {momentum.value(as_of):.2f} (direction: {momentum.direction(as_of):+d})"
    )

    # Create combined Market Regime Indicator
    mri = MarketRegimeIndicator(
        indicators=[vix, momentum],
        coefficients={"vix": 1.0, "momentum": 1.0},
    )
    print(f"  MRI: {mri.value(as_of):.2f} (direction: {mri.direction(as_of):+d})")

    # Get historical data
    print("\nVIX history (last 5 days):")
    history = vix.history(date(2024, 1, 1), date(2024, 1, 10))
    print(history.tail())

    # Interpretation guide
    print("\nInterpretation:")
    print("  VIX > 0.5 = elevated fear")
    print("  Momentum > 0.5 = bullish trend")
    print("  MRI > 0.5 = risk-off conditions")


if __name__ == "__main__":
    main()
