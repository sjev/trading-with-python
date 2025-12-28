# trading-with-python v4 — modernization plan (2025)

## Goals (what this repo should provide)
- **Data download + caching**
  - Yahoo Finance (via `yfinance`)
  - FRED (via `fredapi` and/or simple HTTP)
- **Indicators** (ported from `investing`)
  - VIX, momentum, absorption ratio, market regime indicator (MRI), normalization utilities
- **KISS backtesting framework**
  - Simple training/testing split
  - A minimal portfolio backtest loop (positions/weights → returns → equity curve → metrics)
  - Optional transaction cost model (bps)
- **Examples with interactive plots**
  - Prefer modern interactive plotting (recommendation: Plotly)
  - Keep examples reproducible as plain Python scripts
- **Notebook workflow**
  - Default to plain Python scripts as canonical examples
  - Optionally add Jupyter notebooks once the API stabilizes (revisit Marimo later)

---

## Restructuring plan (current state → desired structure)

### Current state (important constraints)
- The repository contains legacy code under **`lib/`**.
- The installable package is now under **`src/twp/`** (standard `src/` layout).
- Legacy tests/docs referenced a `tradingWithPython` import path and were removed during initial cleanup.
- `setup.py` has been removed; **`pyproject.toml`** is the packaging source of truth.

### Desired structure (v4)
Keep the public library under **`src/twp/`** and treat `lib/` as legacy until fully ported.

Proposed package layout:

```
trading-with-python/
  pyproject.toml
  src/
    twp/
      __init__.py
      data/
        __init__.py
        yahoo.py          # YahooSource (yfinance + caching)
        fred.py           # FredSource (fredapi + caching)
        local_csv.py      # LocalCsvSource for offline tests/examples
        protocol.py       # DataSourceProtocol
      indicators/
        __init__.py
        vix.py
        momentum.py
        absorption_ratio.py
        mri.py
        normalization.py
        protocol.py       # IndicatorProtocol (optional)
      backtest/
        __init__.py
        split.py          # train/test split helpers
        engine.py         # minimal backtest engine
        metrics.py        # sharpe, maxdd, CAGR, turnover
      plotting/
        __init__.py
        plotly.py         # convenience wrappers (optional)
  examples/
    00_download_data.py
    01_indicators.py
    02_backtest_ma_crossover.py
    03_backtest_regime_filter.py
  tests/
    ...
  plan/
    update2025.md
```

---

## What to ADD

### 1) Data tools
- `src/twp/data/yahoo.py`
  - Port from `investing/src/folio/data_sources/yahoo.py`
  - Keep: file caching, safe ticker filenames, `get(ticker, start, end)` API
- `src/twp/data/fred.py`
  - Port from `investing/src/folio/data_sources/fred.py`
  - Keep: caching, simple series retrieval API
- `src/twp/data/local_csv.py` + `src/twp/data/protocol.py`
  - Port from `investing/src/folio/data_sources/local_csv.py` and protocol

### 2) Indicators
Port these from `investing/src/folio/indicators/`:
- `VixIndicator`
- `MomentumIndicator`
- `AbsorptionRatioIndicator`
- `MarketRegimeIndicator`
- `normalization` helpers

**Required refactor while porting**: remove coupling to `folio.config.Config`.
- Data sources should accept explicit `cache_dir`/`data_dir` constructor args.
- Indicators should only depend on a `DataSourceProtocol`.

### 3) Backtesting (KISS)
Add `src/twp/backtest/`:
- `split.py`: a tiny utility to define train/test periods (date-based)
- `engine.py`: minimal backtester
  - input: prices (or returns), weights/positions
  - output: equity curve + returns + basic stats
- `metrics.py`: sharpe, max drawdown, CAGR, volatility, turnover

### 4) Examples + plotting
- `examples/` scripts that:
  - download data (Yahoo, FRED)
  - compute indicators
  - run a backtest with a train/test split
  - output an interactive plot (recommend: Plotly)

### 5) Tests
- Reintroduce `tests/` based on the modernized modules:
  - copy/port `investing/tests/test_indicators.py` patterns
  - add offline test data fixtures (local CSVs)

### 6) Optional: Notebooks
Decision:
- Start with **plain Python scripts** as the authoritative examples.
- Add `notebooks/` later only for exploration/demos.

If/when adding notebooks:
- Prefer **Jupyter** first (widest compatibility).
- Re-evaluate **Marimo** later once the library API is stable.

---

## What to KEEP

### Keep (core)
- `src/twp/` package (as the installable library)
- `examples/` (keep, but refresh content to match v4 APIs)
- `tools/` and `scratch/` only if they are still useful; otherwise migrate important pieces into `examples/`.

### Keep as legacy (read-only / deprecate)
- `lib/` (for now):
  - Treat it as legacy code (not part of the v4 public API)
  - Do not add new features here
  - Gradually port useful pieces into `src/twp/` modules

---

## What to REMOVE / DEPRECATE

### Remove now (already done or to be done)
- `setup.py` (removed)
- course-coupled docs/notebooks/docker scaffolding (removed)

### Deprecate (do not evolve; remove later)
- `lib/` once the equivalent functionality exists under `src/twp/`
- any references to `tradingWithPython.*` import paths

---

## Incremental execution plan (next steps)

### Phase 1 — Port data + indicators
1. Create `src/twp/data/` and `src/twp/indicators/` packages.
2. Port data sources + indicators from `investing`.
3. Make sure everything works offline with `LocalCsvSource`.

### Phase 2 — Add tests
1. Add `tests/` for data + indicators.
2. Include local CSV fixtures for SPY, VIX and sector ETFs.

### Phase 3 — Backtest MVP
1. Implement `src/twp/backtest/engine.py` with train/test split.
2. Add 1–2 simple strategies.
3. Add Plotly-based example scripts.

### Phase 4 — API polish + docs reboot
1. Update README with new module structure and examples.
2. Add a minimal `docs/` later (if needed), but only after API stabilizes.

---

## Notes / design decisions
- **Plotting**: recommend Plotly for interactive plots (HTML export, works in notebooks and scripts).
- **Notebook tooling**: default to scripts; add Jupyter notebooks later; evaluate Marimo after v4 settles.
- **Packaging**: `pyproject.toml` + `src/` layout from day 1 (already in place).
