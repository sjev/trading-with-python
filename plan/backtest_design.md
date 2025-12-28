# Backtest Design

## Overview

`Backtest` class: simple backtesting with shares-based positions and cash tracking.

## Interface

```python
bt = Backtest(prices, shares, initial_capital=100000, cost_per_share=0.005, cost_pct=0.0)
bt.pnl            # Series: daily pnl
bt.equity         # Series: cash + position_value
bt.cash           # Series: cash balance over time
bt.position_value # Series: shares * prices summed across assets
bt.metrics        # dict: sharpe, cagr, volatility, max_drawdown, turnover
bt.report(benchmark=spy_prices)  # generate standalone HTML report
```

## Inputs

- `prices`: DataFrame with asset prices (index=dates, columns=assets)
- `shares`: DataFrame with position sizes (same shape as prices)
- `initial_capital`: starting cash amount
- `cost_per_share`: fixed cost per share traded, e.g. $0.005 (default 0)
- `cost_pct`: cost as fraction of trade value, e.g. 0.0005 for 5bps (default 0)

## Calculation

1. `delta_shares = shares.diff().fillna(shares.iloc[0])` — position changes
2. `trade_value = delta_shares * prices` — cost/proceeds of trades
3. `costs = abs(delta_shares) * cost_per_share + abs(trade_value) * cost_pct`
4. `cash_flow = -trade_value.sum(axis=1) - costs.sum(axis=1)` — negative when buying
5. `cash = initial_capital + cash_flow.cumsum()`
6. `position_value = (shares * prices).sum(axis=1)`
7. `equity = cash + position_value`
8. `pnl = equity.diff()` (first value = equity[0] - initial_capital)

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
