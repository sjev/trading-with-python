"""Backtest engine with shares-based position tracking."""

from functools import cached_property
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .metrics import cagr, max_drawdown, sharpe, volatility


class Backtest:
    """Backtest with shares-based positions and cash tracking."""

    def __init__(
        self,
        prices: pd.DataFrame,
        shares: pd.DataFrame,
        initial_capital: float,
        cost_per_share: float = 0.0,
        cost_pct: float = 0.0,
    ) -> None:
        """Initialize backtest.

        Args:
            prices: DataFrame of asset prices (index=dates, columns=assets)
            shares: DataFrame of position sizes (same shape as prices)
            initial_capital: Starting cash amount
            cost_per_share: Fixed cost per share traded (e.g., $0.005)
            cost_pct: Cost as fraction of trade value (e.g., 0.0005 for 5bps)
        """
        # Align prices and shares
        common_cols = prices.columns.intersection(shares.columns)
        common_idx = prices.index.intersection(shares.index)

        self._prices = prices.loc[common_idx, common_cols]
        self._shares = shares.loc[common_idx, common_cols]
        self._initial_capital = initial_capital
        self._cost_per_share = cost_per_share
        self._cost_pct = cost_pct

    @cached_property
    def _delta_shares(self) -> pd.DataFrame:
        """Position changes (first row is initial buy)."""
        delta = self._shares.diff()
        delta.iloc[0] = self._shares.iloc[0]
        return delta

    @cached_property
    def _trade_value(self) -> pd.DataFrame:
        """Value of trades (shares * price)."""
        return self._delta_shares * self._prices

    @cached_property
    def _costs(self) -> pd.Series:
        """Transaction costs per day."""
        per_share_cost = self._delta_shares.abs() * self._cost_per_share
        pct_cost = self._trade_value.abs() * self._cost_pct
        return (per_share_cost + pct_cost).sum(axis=1)

    @cached_property
    def _cash_flow(self) -> pd.Series:
        """Cash flow per day (negative when buying)."""
        return -self._trade_value.sum(axis=1) - self._costs

    @cached_property
    def cash(self) -> pd.Series:
        """Cash balance over time."""
        return self._initial_capital + self._cash_flow.cumsum()

    @cached_property
    def position_value(self) -> pd.Series:
        """Total position value (shares * prices summed across assets)."""
        return (self._shares * self._prices).sum(axis=1)

    @cached_property
    def equity(self) -> pd.Series:
        """Total equity (cash + position value)."""
        return self.cash + self.position_value

    @cached_property
    def pnl(self) -> pd.Series:
        """Daily profit/loss."""
        pnl = self.equity.diff()
        pnl.iloc[0] = self.equity.iloc[0] - self._initial_capital
        return pnl

    @cached_property
    def _returns(self) -> pd.Series:
        """Daily returns (for metrics calculation)."""
        return self.equity.pct_change().fillna(0)

    @cached_property
    def metrics(self) -> dict[str, float]:
        """Performance metrics."""
        # Turnover: average daily absolute share changes relative to position
        total_shares = self._shares.abs().sum(axis=1)
        daily_turnover = self._delta_shares.abs().sum(axis=1)
        avg_turnover = (daily_turnover / total_shares.replace(0, 1)).mean()

        return {
            "sharpe": sharpe(self._returns),
            "cagr": cagr(self.equity),
            "volatility": volatility(self._returns),
            "max_drawdown": max_drawdown(self.equity),
            "turnover": float(avg_turnover),
        }

    def summary(self, title: str = "Backtest") -> None:
        """Print performance summary."""
        m = self.metrics
        print(f"\n{'=' * 50}")
        print(title)
        print(f"{'=' * 50}")
        print(
            f"Period: {self._prices.index[0].date()} to {self._prices.index[-1].date()}"
        )
        print(f"Initial Capital: ${self._initial_capital:,.0f}")
        print(f"\nSharpe Ratio:  {m['sharpe']:.2f}")
        print(f"CAGR:          {m['cagr']:.1%}")
        print(f"Volatility:    {m['volatility']:.1%}")
        print(f"Max Drawdown:  {m['max_drawdown']:.1%}")
        print(f"Turnover:      {m['turnover']:.2%}")
        print(f"\nFinal Equity:  ${self.equity.iloc[-1]:,.0f}")
        print(f"Total PnL:     ${self.pnl.sum():,.0f}")
        if self.cash.min() < 0:
            print(f"\nWarning: Used margin (min cash: ${self.cash.min():,.0f})")

    def plot(self, benchmark: pd.Series | None = None) -> None:
        """Show interactive plotly charts."""
        fig = self._create_figure(benchmark)
        fig.show()

    def _create_figure(self, benchmark: pd.Series | None = None) -> go.Figure:
        """Create plotly figure with equity curve and positions."""
        equity_normalized = self.equity / self.equity.iloc[0] * 100

        fig = make_subplots(
            rows=2,
            cols=1,
            row_heights=[0.7, 0.3],
            subplot_titles=["Equity Curve", "Positions"],
            vertical_spacing=0.1,
        )

        fig.add_trace(
            go.Scatter(
                x=equity_normalized.index,
                y=equity_normalized.values,
                name="Strategy",
                line={"color": "blue"},
            ),
            row=1,
            col=1,
        )

        if benchmark is not None:
            bench_normalized = benchmark / benchmark.iloc[0] * 100
            fig.add_trace(
                go.Scatter(
                    x=bench_normalized.index,
                    y=bench_normalized.values,
                    name="Benchmark",
                    line={"color": "gray", "dash": "dash"},
                ),
                row=1,
                col=1,
            )

        position_values = self._shares * self._prices
        for col in position_values.columns:
            fig.add_trace(
                go.Scatter(
                    x=position_values.index,
                    y=position_values[col].values,
                    name=col,
                    stackgroup="positions",
                ),
                row=2,
                col=1,
            )

        m = self.metrics
        metrics_text = (
            f"<b>Metrics</b><br>"
            f"Sharpe: {m['sharpe']:.2f}<br>"
            f"CAGR: {m['cagr']:.1%}<br>"
            f"Volatility: {m['volatility']:.1%}<br>"
            f"Max DD: {m['max_drawdown']:.1%}<br>"
            f"Turnover: {m['turnover']:.2%}"
        )

        fig.add_annotation(
            text=metrics_text,
            xref="paper",
            yref="paper",
            x=0.02,
            y=0.98,
            showarrow=False,
            font={"size": 12},
            align="left",
            bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray",
            borderwidth=1,
        )

        fig.update_layout(
            title="Backtest Report",
            hovermode="x unified",
            showlegend=True,
            height=700,
        )

        return fig

    def report(
        self,
        benchmark: pd.Series | None = None,
        output_path: Path | str | None = None,
    ) -> Path:
        """Generate HTML report."""
        if output_path is None:
            output_path = Path("backtest_report.html")
        else:
            output_path = Path(output_path)

        fig = self._create_figure(benchmark)
        fig.write_html(output_path)
        return output_path
