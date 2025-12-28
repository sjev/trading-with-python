"""Plotly convenience wrappers for financial charts."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd

if TYPE_CHECKING:
    import plotly.graph_objects as go


def plot_prices(
    prices: pd.DataFrame | pd.Series,
    title: str = "Prices",
    normalize: bool = False,
) -> go.Figure:
    """Plot price series.

    Args:
        prices: Price data (Series or DataFrame with multiple columns)
        title: Chart title
        normalize: If True, normalize all series to start at 100

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    if isinstance(prices, pd.Series):
        prices = prices.to_frame()

    for col in prices.columns:
        series = prices[col]
        if normalize:
            series = series / series.iloc[0] * 100

        fig.add_trace(
            go.Scatter(x=series.index, y=series.values, name=str(col), mode="lines")
        )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price" if not normalize else "Normalized (100 = start)",
        hovermode="x unified",
    )

    return fig


def plot_equity(
    equity: pd.Series,
    title: str = "Equity Curve",
    benchmark: pd.Series | None = None,
) -> go.Figure:
    """Plot equity curve with optional benchmark.

    Args:
        equity: Equity curve series
        title: Chart title
        benchmark: Optional benchmark equity curve

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    fig.add_trace(
        go.Scatter(
            x=equity.index, y=equity.values, name="Strategy", mode="lines", line={"color": "blue"}
        )
    )

    if benchmark is not None:
        fig.add_trace(
            go.Scatter(
                x=benchmark.index,
                y=benchmark.values,
                name="Benchmark",
                mode="lines",
                line={"color": "gray", "dash": "dash"},
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Equity",
        hovermode="x unified",
    )

    return fig


def plot_indicator(
    indicator_history: pd.DataFrame,
    title: str = "Indicator",
    show_direction: bool = True,
) -> go.Figure:
    """Plot indicator history with normalized values and direction.

    Args:
        indicator_history: DataFrame with 'normalized' and 'direction' columns
        title: Chart title
        show_direction: If True, color background by direction

    Returns:
        Plotly Figure object
    """
    import plotly.graph_objects as go

    fig = go.Figure()

    # Plot normalized values
    fig.add_trace(
        go.Scatter(
            x=indicator_history.index,
            y=indicator_history["normalized"],
            name="Value",
            mode="lines",
            line={"color": "blue"},
        )
    )

    # Add direction as colored markers if requested
    if show_direction and "direction" in indicator_history.columns:
        colors = indicator_history["direction"].map({1: "green", 0: "gray", -1: "red"})
        fig.add_trace(
            go.Scatter(
                x=indicator_history.index,
                y=indicator_history["normalized"],
                mode="markers",
                marker={"color": colors, "size": 4},
                name="Direction",
                showlegend=False,
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Normalized Value (0-1)",
        yaxis={"range": [0, 1]},
        hovermode="x unified",
    )

    return fig
