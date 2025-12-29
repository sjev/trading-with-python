# trading-with-python

Open-source toolbox for quantitative trading strategy development.

## Installation

```bash
pip install twp
```

## Quick Start

```python
from datetime import date
import numpy as np
import pandas as pd
from twp.data import YahooSource
from twp.backtest import backtest, metrics, summary
from twp.plotting import plot_equity

# Download data
source = YahooSource()
spy = source.get("SPY", date(2020, 1, 1))
prices = pd.DataFrame({"SPY": spy["Close"]})

# Generate signal and convert to shares
signal = (prices["SPY"].rolling(10).mean() > prices["SPY"].rolling(30).mean()).astype(int)
initial_capital = 100_000
shares = pd.DataFrame({"SPY": np.floor(initial_capital * signal / prices["SPY"]).fillna(0).astype(int)})

# Run backtest
result = backtest(prices, shares, initial_capital, cost_pct=0.0005)

# Show metrics and plot
m = metrics(result["equity"])
summary(m, title="MA Crossover")
plot_equity(result["equity"], benchmark=prices["SPY"]).show()
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
- `backtest()` - Run backtest, returns dict with equity/pnl/cash/positions
- `metrics()` - Compute metrics from equity curve
- `summary()` - Print formatted metrics
- `Split` / `train_test_split()` - Split data by date
- Individual metrics: `sharpe`, `max_drawdown`, `cagr`, `volatility`

### Plotting (`twp.plotting`)
- `plot_prices()` - Price chart
- `plot_equity()` - Equity curve with optional benchmark
- `plot_indicator()` - Indicator visualization

## Examples

See the `examples/` directory:
- `00_download_data.py` - Data download demo
- `01_indicators.py` - Indicator usage
- `02_backtest_example.py` - MA crossover strategy
- `03_backtest_regime_filter.py` - Regime-filtered strategy
- `04_backtest_optimisation.py` - Parameter optimization

## Development

```bash
uv sync --group dev
inv lint   # ruff + mypy
inv test   # pytest
```

## License

MIT
