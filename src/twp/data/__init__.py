"""Data sources for market data retrieval."""

from twp.data.local_csv import LocalCsvSource
from twp.data.protocol import DataSourceProtocol
from twp.data.yahoo import YahooSource

__all__ = ["DataSourceProtocol", "FredSource", "LocalCsvSource", "YahooSource"]


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    if name == "FredSource":
        from twp.data.fred import FredSource

        return FredSource
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
