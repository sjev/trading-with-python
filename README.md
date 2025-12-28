# trading-with-python

Open-source toolbox for quantitative trading strategy development.

## Installation

```bash
pip install twp

# With optional dependencies
pip install "twp[yahoo]"     # Yahoo Finance data
pip install "twp[fred]"      # FRED economic data
pip install "twp[plotting]"  # Plotly charts
pip install "twp[all]"       # All extras
```

## Quick Start

```python
from datetime import date
from twp.data import YahooSource
from twp.indicators import MomentumIndicator
from twp.backtest import backtest, train_test_split

# Download data
source = YahooSource()
prices = source.get("SPY", date(2020, 1, 1))

# Calculate indicators
momentum = MomentumIndicator(source, ticker="SPY")
print(f"Current momentum: {momentum.value():.2f}")

# Run backtest
weights = ...  # your strategy weights
result = backtest(prices, weights, cost_bps=5)
print(f"Sharpe: {result.sharpe:.2f}, CAGR: {result.cagr*100:.1f}%")
```

## Modules

### Data Sources (`twp.data`)
- `YahooSource` - Yahoo Finance with file caching
- `FredSource` - FRED economic data with caching
- `LocalCsvSource` - Local CSV files for offline use

### Indicators (`twp.indicators`)
- `VixIndicator` - VIX-based fear gauge
- `MomentumIndicator` - Price momentum (distance from MA)
- `AbsorptionRatioIndicator` - Market fragility measure
- `MarketRegimeIndicator` - Combined regime indicator

### Backtesting (`twp.backtest`)
- `train_test_split()` - Split data by date
- `backtest()` - Run backtest with weights
- Metrics: `sharpe`, `max_drawdown`, `cagr`, `volatility`, `turnover`

### Plotting (`twp.plotting`)
- `plot_prices()` - Price chart
- `plot_equity()` - Equity curve
- `plot_indicator()` - Indicator visualization

## Examples

See the `examples/` directory:
- `00_download_data.py` - Data download demo
- `01_indicators.py` - Indicator usage
- `02_backtest_ma_crossover.py` - MA crossover strategy
- `03_backtest_regime_filter.py` - Regime-filtered strategy

## Development

```bash
uv sync --group dev
inv lint   # ruff + mypy
inv test   # pytest
```

## License

BSD
