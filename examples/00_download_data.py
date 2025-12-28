#!/usr/bin/env python
"""Example: Download market data from Yahoo Finance.

This example shows how to use YahooSource to fetch and cache market data.

Usage:
    python examples/00_download_data.py
"""

from datetime import date

# Note: Requires yfinance to be installed (pip install yfinance)
try:
    from twp.data import YahooSource
except ImportError as err:
    print("yfinance not installed. Install with: pip install yfinance")
    raise SystemExit(1) from err


def main() -> None:
    """Download sample market data."""
    # Create Yahoo source (caches to ~/.twp/cache/yahoo/)
    source = YahooSource()

    # Download SPY data
    print("Downloading SPY data...")
    spy = source.get("SPY", start=date(2020, 1, 1))
    print(f"  Got {len(spy)} days of SPY data")
    print(f"  Date range: {spy.index[0].date()} to {spy.index[-1].date()}")
    print(f"  Latest close: ${spy['Close'].iloc[-1]:.2f}")

    # Download VIX data
    print("\nDownloading VIX data...")
    vix = source.get("^VIX", start=date(2020, 1, 1))
    print(f"  Got {len(vix)} days of VIX data")
    print(f"  Latest VIX: {vix.iloc[-1]:.2f}")

    # Download sector ETFs
    sectors = ["XLF", "XLK", "XLE", "XLV"]
    print(f"\nDownloading sector ETFs: {sectors}")
    for ticker in sectors:
        data = source.get(ticker, start=date(2020, 1, 1))
        print(f"  {ticker}: {len(data)} days")

    print("\nData cached to ~/.twp/cache/yahoo/")
    print("Run again to use cached data (faster).")


if __name__ == "__main__":
    main()
