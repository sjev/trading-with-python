"""Trading with Python - quantitative trading toolkit."""

__version__ = "4.0.0"

# Core submodules (always available)
from twp import backtest, data, indicators

__all__ = ["__version__", "backtest", "data", "indicators", "plotting"]


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    if name == "plotting":
        from twp import plotting

        return plotting
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
