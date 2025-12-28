"""Tests for backtest module."""

from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from twp.backtest import (
    Backtest,
    Split,
    cagr,
    max_drawdown,
    sharpe,
    train_test_split,
    turnover,
    volatility,
)


@pytest.fixture
def sample_prices() -> pd.DataFrame:
    """Sample price data for testing."""
    dates = pd.date_range("2024-01-01", periods=100, freq="D")
    np.random.seed(42)
    spy = 100 * (1 + np.random.randn(100).cumsum() * 0.01)
    qqq = 100 * (1 + np.random.randn(100).cumsum() * 0.015)
    return pd.DataFrame({"SPY": spy, "QQQ": qqq}, index=dates)


class TestSplit:
    """Tests for Split and train_test_split."""

    def test_train_test_split_default_ratio(self, sample_prices: pd.DataFrame) -> None:
        """Test default 70/30 split."""
        split = train_test_split(sample_prices)

        assert isinstance(split, Split)
        assert split.train_start == date(2024, 1, 1)
        assert split.train_end < split.test_start

    def test_train_test_split_custom_ratio(self, sample_prices: pd.DataFrame) -> None:
        """Test custom split ratio."""
        split = train_test_split(sample_prices, train_ratio=0.5)

        train_data = split.slice_train(sample_prices)
        test_data = split.slice_test(sample_prices)

        # Roughly equal sizes
        assert abs(len(train_data) - len(test_data)) <= 1

    def test_split_slice_methods(self, sample_prices: pd.DataFrame) -> None:
        """Test that slice methods return correct data."""
        split = train_test_split(sample_prices)

        train = split.slice_train(sample_prices)
        test = split.slice_test(sample_prices)

        assert len(train) > 0
        assert len(test) > 0
        assert train.index.max() < test.index.min()


class TestMetrics:
    """Tests for performance metrics."""

    def test_sharpe_positive(self) -> None:
        """Test Sharpe ratio with positive mean returns."""
        np.random.seed(42)
        # Positive mean with some volatility
        returns = pd.Series(0.001 + np.random.randn(252) * 0.01)
        s = sharpe(returns)

        assert s > 0

    def test_sharpe_zero_std(self) -> None:
        """Test Sharpe ratio with zero volatility."""
        returns = pd.Series([0.0] * 100)
        s = sharpe(returns)

        assert s == 0.0

    def test_max_drawdown_no_drawdown(self) -> None:
        """Test max drawdown with monotonically increasing equity."""
        equity = pd.Series([1.0, 1.1, 1.2, 1.3, 1.4])
        mdd = max_drawdown(equity)

        assert mdd == 0.0

    def test_max_drawdown_with_drawdown(self) -> None:
        """Test max drawdown calculation."""
        equity = pd.Series([1.0, 1.2, 1.0, 1.1])  # 16.67% drawdown
        mdd = max_drawdown(equity)

        assert 0.15 < mdd < 0.20

    def test_cagr_calculation(self) -> None:
        """Test CAGR calculation."""
        # 100% return over 1 year (252 days)
        equity = pd.Series([1.0] + [1.0] * 250 + [2.0])
        c = cagr(equity, periods=252)

        assert 0.95 < c < 1.05  # ~100% CAGR

    def test_volatility_calculation(self) -> None:
        """Test volatility calculation."""
        np.random.seed(42)
        returns = pd.Series(np.random.randn(252) * 0.01)
        vol = volatility(returns)

        assert 0.1 < vol < 0.2  # ~16% annualized vol

    def test_turnover_calculation(self) -> None:
        """Test turnover calculation."""
        weights = pd.DataFrame(
            {
                "A": [0.5, 0.6, 0.4],
                "B": [0.5, 0.4, 0.6],
            }
        )
        t = turnover(weights)

        assert t > 0


class TestBacktest:
    """Tests for Backtest class with cash tracking."""

    # --- Cash tracking tests ---

    def test_cash_after_initial_buy(self) -> None:
        """Cash should decrease by cost of initial purchase."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame(
            {"SPY": [10, 10, 10]}, index=dates
        )  # Buy 10 shares at $100

        bt = Backtest(prices, shares, initial_capital=10000)

        # Bought 10 shares at $100 = $1000 spent
        assert bt.cash.iloc[0] == 10000 - 1000

    def test_cash_decreases_on_buy(self) -> None:
        """Buying more shares should decrease cash."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame(
            {"SPY": [10, 20, 20]}, index=dates
        )  # Buy 10 more on day 2

        bt = Backtest(prices, shares, initial_capital=10000)

        # Day 0: bought 10 @ $100 = cash = 10000 - 1000 = 9000
        # Day 1: bought 10 more @ $100 = cash = 9000 - 1000 = 8000
        assert bt.cash.iloc[0] == 9000
        assert bt.cash.iloc[1] == 8000
        assert bt.cash.iloc[2] == 8000  # No change

    def test_cash_increases_on_sell(self) -> None:
        """Selling shares should increase cash."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [20, 10, 10]}, index=dates)  # Sell 10 on day 2

        bt = Backtest(prices, shares, initial_capital=10000)

        # Day 0: bought 20 @ $100 = cash = 10000 - 2000 = 8000
        # Day 1: sold 10 @ $100 = cash = 8000 + 1000 = 9000
        assert bt.cash.iloc[0] == 8000
        assert bt.cash.iloc[1] == 9000

    def test_cash_with_transaction_costs_per_share(self) -> None:
        """Transaction costs should reduce cash."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [100, 100]}, index=dates)  # Buy 100 shares

        bt = Backtest(prices, shares, initial_capital=20000, cost_per_share=0.01)

        # Bought 100 shares @ $100 = $10000
        # Cost: 100 * $0.01 = $1
        # Cash = 20000 - 10000 - 1 = 9999
        assert bt.cash.iloc[0] == 9999

    def test_cash_with_transaction_costs_pct(self) -> None:
        """Percentage transaction costs should reduce cash."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [100, 100]}, index=dates)  # Buy 100 shares

        bt = Backtest(prices, shares, initial_capital=20000, cost_pct=0.001)  # 10 bps

        # Bought 100 shares @ $100 = $10000
        # Cost: 10000 * 0.001 = $10
        # Cash = 20000 - 10000 - 10 = 9990
        assert bt.cash.iloc[0] == 9990

    # --- Position value tests ---

    def test_position_value_single_asset(self) -> None:
        """Position value should equal shares * price."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        assert bt.position_value.iloc[0] == 10 * 100
        assert bt.position_value.iloc[1] == 10 * 110
        assert bt.position_value.iloc[2] == 10 * 105

    def test_position_value_multiple_assets(self) -> None:
        """Position value should sum across assets."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame(
            {"SPY": [100.0, 100.0], "QQQ": [200.0, 200.0]}, index=dates
        )
        shares = pd.DataFrame({"SPY": [10, 10], "QQQ": [5, 5]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=20000)

        # Position value = 10*100 + 5*200 = 1000 + 1000 = 2000
        assert bt.position_value.iloc[0] == 2000

    # --- Equity tests ---

    def test_equity_equals_cash_plus_position(self) -> None:
        """Equity should equal cash + position value."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        for i in range(len(dates)):
            assert bt.equity.iloc[i] == bt.cash.iloc[i] + bt.position_value.iloc[i]

    def test_equity_starts_at_initial_capital(self) -> None:
        """Equity should start at initial capital (before price changes)."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        # Day 0: cash = 10000 - 1000 = 9000, position = 1000, equity = 10000
        assert bt.equity.iloc[0] == 10000

    def test_equity_grows_with_price_increase(self) -> None:
        """Equity should grow when price increases."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 120.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        # Day 0: equity = 10000
        # Day 1: equity = 9000 + 10*110 = 10100
        # Day 2: equity = 9000 + 10*120 = 10200
        assert bt.equity.iloc[0] == 10000
        assert bt.equity.iloc[1] == 10100
        assert bt.equity.iloc[2] == 10200

    # --- PnL tests ---

    def test_pnl_from_price_change(self) -> None:
        """PnL should reflect gains from price changes."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        # Day 0: pnl = equity[0] - initial_capital = 0
        # Day 1: pnl = equity[1] - equity[0] = 10100 - 10000 = 100
        # Day 2: pnl = equity[2] - equity[1] = 10050 - 10100 = -50
        assert bt.pnl.iloc[0] == 0
        assert bt.pnl.iloc[1] == 100
        assert bt.pnl.iloc[2] == -50

    def test_pnl_includes_costs(self) -> None:
        """PnL should include transaction costs on trade days."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame(
            {"SPY": [100, 200, 200]}, index=dates
        )  # Buy 100 more on day 2

        bt = Backtest(prices, shares, initial_capital=50000, cost_per_share=1.0)

        # Day 0: buy 100 shares, cost = $100, pnl = -100
        # Day 1: buy 100 more shares, cost = $100, pnl = -100
        # Day 2: no trade, pnl = 0
        assert bt.pnl.iloc[0] == -100
        assert bt.pnl.iloc[1] == -100
        assert bt.pnl.iloc[2] == 0

    def test_pnl_sums_to_equity_change(self) -> None:
        """Total PnL should equal final equity minus initial capital."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0, 115.0, 120.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 20, 20, 10]}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000, cost_per_share=0.01)

        total_pnl = bt.pnl.sum()
        equity_change = bt.equity.iloc[-1] - 10000
        assert abs(total_pnl - equity_change) < 0.01

    # --- Negative cash tests ---

    def test_allows_negative_cash(self) -> None:
        """Backtest should allow negative cash (margin)."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [200, 200]}, index=dates)  # $20000 position

        bt = Backtest(prices, shares, initial_capital=10000)  # Only $10000 capital

        # Cash = 10000 - 20000 = -10000
        assert bt.cash.iloc[0] == -10000
        # Equity still = cash + position = -10000 + 20000 = 10000
        assert bt.equity.iloc[0] == 10000


class TestBacktestMetrics:
    """Tests for Backtest.metrics property."""

    def test_metrics_returns_dict(self) -> None:
        """Metrics should return a dictionary."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        prices = pd.DataFrame({"SPY": 100 + np.random.randn(100).cumsum()}, index=dates)
        shares = pd.DataFrame({"SPY": [10] * 100}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)
        m = bt.metrics

        assert isinstance(m, dict)
        assert "sharpe" in m
        assert "cagr" in m
        assert "volatility" in m
        assert "max_drawdown" in m
        assert "turnover" in m

    def test_metrics_sharpe_is_float(self) -> None:
        """Sharpe ratio should be a float."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        np.random.seed(42)
        prices = pd.DataFrame({"SPY": 100 + np.random.randn(100).cumsum()}, index=dates)
        shares = pd.DataFrame({"SPY": [10] * 100}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        assert isinstance(bt.metrics["sharpe"], float)

    def test_metrics_with_profitable_strategy(self) -> None:
        """Metrics should be positive for profitable strategy."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        # Steadily rising prices
        prices = pd.DataFrame({"SPY": [100 + i * 0.5 for i in range(100)]}, index=dates)
        shares = pd.DataFrame({"SPY": [10] * 100}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)

        assert bt.metrics["cagr"] > 0
        assert bt.metrics["sharpe"] > 0


class TestBacktestReport:
    """Tests for Backtest.report() method."""

    def test_report_creates_html_file(self, tmp_path: Path) -> None:
        """Report should create an HTML file."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        prices = pd.DataFrame({"SPY": [100 + i for i in range(10)]}, index=dates)
        shares = pd.DataFrame({"SPY": [10] * 10}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)
        output_path = tmp_path / "test_report.html"
        result = bt.report(output_path=output_path)

        assert output_path.exists()
        assert result == output_path

    def test_report_with_benchmark(self, tmp_path: Path) -> None:
        """Report should include benchmark when provided."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        prices = pd.DataFrame({"SPY": [100 + i for i in range(10)]}, index=dates)
        shares = pd.DataFrame({"SPY": [10] * 10}, index=dates)
        benchmark = pd.Series([100 + i * 0.5 for i in range(10)], index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)
        output_path = tmp_path / "test_report_bench.html"
        bt.report(benchmark=benchmark, output_path=output_path)

        content = output_path.read_text()
        assert "Benchmark" in content or "benchmark" in content

    def test_report_default_path(self) -> None:
        """Report should default to backtest_report.html."""
        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        prices = pd.DataFrame({"SPY": [100 + i for i in range(10)]}, index=dates)
        shares = pd.DataFrame({"SPY": [10] * 10}, index=dates)

        bt = Backtest(prices, shares, initial_capital=10000)
        result = bt.report()

        assert result.name == "backtest_report.html"
        # Cleanup
        if result.exists():
            result.unlink()
