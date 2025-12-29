"""Tests for backtest module."""

from datetime import date

import numpy as np
import pandas as pd
import pytest

from twp.backtest import (
    Split,
    backtest,
    cagr,
    max_drawdown,
    metrics,
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


class TestMetricsFunctions:
    """Tests for individual metric functions."""

    def test_sharpe_positive(self) -> None:
        """Test Sharpe ratio with positive mean returns."""
        np.random.seed(42)
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
        weights = pd.DataFrame({"A": [0.5, 0.6, 0.4], "B": [0.5, 0.4, 0.6]})
        t = turnover(weights)
        assert t > 0


class TestMetricsAggregator:
    """Tests for the metrics() aggregator function."""

    def test_metrics_returns_dict(self) -> None:
        """Metrics should return a dictionary with all metrics."""
        equity = pd.Series([100, 101, 102, 103, 104])
        m = metrics(equity)

        assert isinstance(m, dict)
        assert "sharpe" in m
        assert "cagr" in m
        assert "volatility" in m
        assert "max_drawdown" in m

    def test_metrics_with_profitable_equity(self) -> None:
        """Metrics should be positive for profitable equity curve."""
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        equity = pd.Series([100 + i * 0.5 for i in range(100)], index=dates)
        m = metrics(equity)

        assert m["cagr"] > 0
        assert m["sharpe"] > 0


class TestBacktest:
    """Tests for backtest() function with cash tracking."""

    def test_cash_after_initial_buy(self) -> None:
        """Cash should decrease by cost of initial purchase."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        # Bought 10 shares at $100 = $1000 spent
        assert result["cash"].iloc[0] == 10000 - 1000

    def test_cash_decreases_on_buy(self) -> None:
        """Buying more shares should decrease cash."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 20, 20]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["cash"].iloc[0] == 9000
        assert result["cash"].iloc[1] == 8000
        assert result["cash"].iloc[2] == 8000

    def test_cash_increases_on_sell(self) -> None:
        """Selling shares should increase cash."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [20, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["cash"].iloc[0] == 8000
        assert result["cash"].iloc[1] == 9000

    def test_cash_with_transaction_costs_per_share(self) -> None:
        """Transaction costs should reduce cash."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [100, 100]}, index=dates)

        result = backtest(prices, shares, initial_capital=20000, cost_per_share=0.01)

        # Cash = 20000 - 10000 - 1 = 9999
        assert result["cash"].iloc[0] == 9999

    def test_cash_with_transaction_costs_pct(self) -> None:
        """Percentage transaction costs should reduce cash."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [100, 100]}, index=dates)

        result = backtest(prices, shares, initial_capital=20000, cost_pct=0.001)

        # Cash = 20000 - 10000 - 10 = 9990
        assert result["cash"].iloc[0] == 9990

    def test_equity_equals_cash_plus_position(self) -> None:
        """Equity should equal cash + position value."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        for i in range(len(dates)):
            position_value = result["positions"].iloc[i].sum()
            assert result["equity"].iloc[i] == result["cash"].iloc[i] + position_value

    def test_equity_starts_at_initial_capital(self) -> None:
        """Equity should start at initial capital."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["equity"].iloc[0] == 10000

    def test_equity_grows_with_price_increase(self) -> None:
        """Equity should grow when price increases."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 120.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["equity"].iloc[0] == 10000
        assert result["equity"].iloc[1] == 10100
        assert result["equity"].iloc[2] == 10200

    def test_pnl_from_price_change(self) -> None:
        """PnL should reflect gains from price changes."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["pnl"].iloc[0] == 0
        assert result["pnl"].iloc[1] == 100
        assert result["pnl"].iloc[2] == -50

    def test_pnl_includes_costs(self) -> None:
        """PnL should include transaction costs on trade days."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [100, 200, 200]}, index=dates)

        result = backtest(prices, shares, initial_capital=50000, cost_per_share=1.0)

        assert result["pnl"].iloc[0] == -100
        assert result["pnl"].iloc[1] == -100
        assert result["pnl"].iloc[2] == 0

    def test_pnl_sums_to_equity_change(self) -> None:
        """Total PnL should equal final equity minus initial capital."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0, 115.0, 120.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 20, 20, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000, cost_per_share=0.01)

        total_pnl = result["pnl"].sum()
        equity_change = result["equity"].iloc[-1] - 10000
        assert abs(total_pnl - equity_change) < 0.01

    def test_allows_negative_cash(self) -> None:
        """Backtest should allow negative cash (margin)."""
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 100.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [200, 200]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["cash"].iloc[0] == -10000
        assert result["equity"].iloc[0] == 10000

    def test_positions_output(self) -> None:
        """Positions should contain position values (shares * prices)."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 105.0]}, index=dates)
        shares = pd.DataFrame({"SPY": [10, 10, 10]}, index=dates)

        result = backtest(prices, shares, initial_capital=10000)

        assert result["positions"]["SPY"].iloc[0] == 1000
        assert result["positions"]["SPY"].iloc[1] == 1100
        assert result["positions"]["SPY"].iloc[2] == 1050
