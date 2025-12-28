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
