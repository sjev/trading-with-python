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
import numpy as np
import pandas as pd
from twp.data import YahooSource
from twp.backtest import Backtest

# Download data
source = YahooSource()
spy = source.get("SPY", date(2020, 1, 1))
prices = pd.DataFrame({"SPY": spy["Close"]})

# Generate signal and convert to shares
signal = (prices["SPY"].rolling(10).mean() > prices["SPY"].rolling(30).mean()).astype(int)
initial_capital = 100_000
shares = pd.DataFrame({"SPY": np.floor(initial_capital * signal / prices["SPY"]).fillna(0).astype(int)})

# Run backtest
bt = Backtest(prices=prices, shares=shares, initial_capital=initial_capital, cost_pct=0.0005)
print(f"Sharpe: {bt.metrics['sharpe']:.2f}, CAGR: {bt.metrics['cagr']:.1%}")
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
- `Backtest` - Run backtest with shares-based positions
- `Split` / `train_test_split()` - Split data by date
- Metrics: `sharpe`, `max_drawdown`, `cagr`, `volatility`, `turnover`

### Plotting (`twp.plotting`)
- `plot_prices()` - Price chart
- `plot_equity()` - Equity curve
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

BSD
