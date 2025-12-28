# Backtest Design

## Overview

`Backtest` class: simple backtesting with shares-based positions.

## Interface

```python
bt = Backtest(prices, shares, cost_per_share=0.005, cost_pct=0.0)
bt.pnl          # Series: daily pnl
bt.equity       # Series: cumulative equity curve
bt.metrics      # dict: sharpe, cagr, volatility, max_drawdown, turnover
bt.report(benchmark=spy_prices)  # generate standalone HTML report
```

## Inputs

- `prices`: DataFrame with asset prices (index=dates, columns=assets)
- `shares`: DataFrame with position sizes (same shape as prices)
- `cost_per_share`: fixed cost per share traded, e.g. $0.005 (default 0)
- `cost_pct`: cost as fraction of trade value, e.g. 0.0005 for 5bps (default 0)

## Calculation

1. `delta_shares = shares.diff()` — position changes
2. `delta_prices = prices.diff()` — price changes
3. `pnl = (shares.shift(1) * delta_prices).sum(axis=1)` — mark-to-market pnl
4. `trade_value = delta_shares.abs() * prices` — value of trades
5. `costs = (delta_shares.abs() * cost_per_share + trade_value * cost_pct).sum(axis=1)`
6. `net_pnl = pnl - costs`

## Metrics

- Sharpe ratio (annualized)
- CAGR
- Volatility (annualized)
- Max drawdown
- Turnover

## Report

`report(benchmark=None, output_path=None)` — generate standalone HTML file

- `benchmark`: optional Series of benchmark prices (e.g. SPY), normalized to start at same value
- `output_path`: file path, defaults to `backtest_report.html`

Contents:
- Equity curve plot (with benchmark overlay if provided)
- Metrics summary table
- Positions over time (optional)
