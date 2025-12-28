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


@pytest.fixture
def sample_weights(sample_prices: pd.DataFrame) -> pd.DataFrame:
    """Sample weights for testing."""
    return pd.DataFrame(
        {"SPY": 0.6, "QQQ": 0.4},
        index=sample_prices.index,
    )


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


class TestBacktestReturns:
    """Tests to verify return calculation correctness."""

    def test_buy_hold_matches_price_ratio(self) -> None:
        """Buy & hold equity should match price ratio exactly."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 102.0, 101.0, 105.0, 103.0]}, index=dates)
        weights = pd.DataFrame({"SPY": 1.0}, index=dates)

        result = backtest(prices, weights, cost_bps=0)

        # Final equity should equal final_price / initial_price
        expected_equity = 103.0 / 100.0
        assert abs(result.equity.iloc[-1] - expected_equity) < 1e-10

    def test_daily_returns_match_price_changes(self) -> None:
        """Daily returns should match price percentage changes."""
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 99.0, 108.9]}, index=dates)
        weights = pd.DataFrame({"SPY": 1.0}, index=dates)

        result = backtest(prices, weights, cost_bps=0)

        # Day 0: return = 0 (no prior weight due to shift)
        # Day 1: return = (110-100)/100 = 10%
        # Day 2: return = (99-110)/110 = -10%
        # Day 3: return = (108.9-99)/99 = 10%
        expected_returns = [0.0, 0.10, -0.10, 0.10]

        for i, expected in enumerate(expected_returns):
            assert abs(result.returns.iloc[i] - expected) < 1e-10, f"Day {i} mismatch"

    def test_zero_weight_means_zero_return(self) -> None:
        """When weight is 0, return should be 0 regardless of price move."""
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 150.0, 200.0, 50.0]}, index=dates)
        weights = pd.DataFrame({"SPY": 0.0}, index=dates)

        result = backtest(prices, weights, cost_bps=0)

        # All returns should be 0
        assert (result.returns == 0).all()
        assert result.equity.iloc[-1] == 1.0

    def test_partial_weight_scales_returns(self) -> None:
        """50% weight should give 50% of the return."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 121.0]}, index=dates)

        full_weights = pd.DataFrame({"SPY": 1.0}, index=dates)
        half_weights = pd.DataFrame({"SPY": 0.5}, index=dates)

        full_result = backtest(prices, full_weights, cost_bps=0)
        half_result = backtest(prices, half_weights, cost_bps=0)

        # Half weight returns should be half of full weight returns (after day 0)
        for i in range(1, len(dates)):
            expected = full_result.returns.iloc[i] * 0.5
            assert abs(half_result.returns.iloc[i] - expected) < 1e-10

    def test_weight_applied_with_one_day_lag(self) -> None:
        """Weight change should affect next day's return, not same day."""
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 121.0, 133.1]}, index=dates)
        # Start out, then go in on day 1
        weights = pd.DataFrame({"SPY": [0.0, 1.0, 1.0, 1.0]}, index=dates)

        result = backtest(prices, weights, cost_bps=0)

        # Day 0: return = 0 (shift gives NaN weight)
        # Day 1: return = 10% * weight[0]=0 = 0  (weight lagged!)
        # Day 2: return = 10% * weight[1]=1 = 10%
        # Day 3: return = 10% * weight[2]=1 = 10%
        expected_returns = [0.0, 0.0, 0.10, 0.10]

        for i, expected in enumerate(expected_returns):
            assert abs(result.returns.iloc[i] - expected) < 1e-10, f"Day {i} mismatch"

    def test_equity_compounds_correctly(self) -> None:
        """Equity should compound: (1+r1)*(1+r2)*..."""
        dates = pd.date_range("2024-01-01", periods=4, freq="D")
        prices = pd.DataFrame({"SPY": [100.0, 110.0, 121.0, 108.9]}, index=dates)
        weights = pd.DataFrame({"SPY": 1.0}, index=dates)

        result = backtest(prices, weights, cost_bps=0)

        # Manual calculation:
        # Day 0: equity = 1.0
        # Day 1: equity = 1.0 * 1.10 = 1.10
        # Day 2: equity = 1.10 * 1.10 = 1.21
        # Day 3: equity = 1.21 * 0.90 = 1.089
        expected_equity = [1.0, 1.10, 1.21, 1.089]

        for i, expected in enumerate(expected_equity):
            assert abs(result.equity.iloc[i] - expected) < 1e-10, f"Day {i} mismatch"


class TestBacktest:
    """Tests for backtest engine."""

    def test_backtest_returns_result(
        self, sample_prices: pd.DataFrame, sample_weights: pd.DataFrame
    ) -> None:
        """Test that backtest returns a BacktestResult."""
        result = backtest(sample_prices, sample_weights)

        assert hasattr(result, "returns")
        assert hasattr(result, "equity")
        assert hasattr(result, "sharpe")
        assert hasattr(result, "cagr")
        assert hasattr(result, "max_drawdown")

    def test_backtest_equity_starts_at_one(
        self, sample_prices: pd.DataFrame, sample_weights: pd.DataFrame
    ) -> None:
        """Test that equity curve starts at 1.0."""
        result = backtest(sample_prices, sample_weights)

        assert result.equity.iloc[0] == 1.0

    def test_backtest_with_costs(
        self, sample_prices: pd.DataFrame, sample_weights: pd.DataFrame
    ) -> None:
        """Test that transaction costs reduce returns."""
        result_no_cost = backtest(sample_prices, sample_weights, cost_bps=0)
        result_with_cost = backtest(sample_prices, sample_weights, cost_bps=10)

        # Equity with costs should be lower
        assert result_with_cost.equity.iloc[-1] <= result_no_cost.equity.iloc[-1]

    def test_backtest_lengths_match(
        self, sample_prices: pd.DataFrame, sample_weights: pd.DataFrame
    ) -> None:
        """Test that returns and equity have same length as input."""
        result = backtest(sample_prices, sample_weights)

        assert len(result.returns) == len(sample_prices)
        assert len(result.equity) == len(sample_prices)
