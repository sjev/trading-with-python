"""Market Regime Indicator - combines multiple indicators."""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING

import pandas as pd

from .normalization import compute_direction

if TYPE_CHECKING:
    from .protocol import IndicatorProtocol


class MarketRegimeIndicator:
    """Combines multiple indicators into a single Market Regime Indicator.

    Uses logistic regression coefficients to weight indicators.
    For now, uses simple weighted average with configurable coefficients.
    """

    def __init__(
        self,
        indicators: list[IndicatorProtocol],
        coefficients: dict[str, float] | None = None,
    ):
        self.indicators = indicators
        # Default to equal weights if not specified
        if coefficients is None:
            self.coefficients = {ind.name: 1.0 for ind in indicators}
        else:
            self.coefficients = coefficients

    @property
    def name(self) -> str:
        return "mri"

    def value(self, as_of: date | None = None) -> float:
        """Get combined MRI score (0..1) for a specific date."""
        values = []
        weights = []

        for ind in self.indicators:
            coef = self.coefficients.get(ind.name, 1.0)
            values.append(ind.value(as_of) * coef)
            weights.append(abs(coef))

        total_weight = sum(weights)
        if total_weight == 0:
            return 0.5

        return sum(values) / total_weight

    def direction(self, as_of: date | None = None) -> int:
        """Get combined direction (-1, 0, 1) for a specific date."""
        # Use majority voting weighted by coefficients
        weighted_dir = 0.0
        total_weight = 0.0

        for ind in self.indicators:
            coef = abs(self.coefficients.get(ind.name, 1.0))
            weighted_dir += ind.direction(as_of) * coef
            total_weight += coef

        if total_weight == 0:
            return 0

        avg_dir = weighted_dir / total_weight
        if avg_dir > 0.3:
            return 1
        elif avg_dir < -0.3:
            return -1
        return 0

    def history(
        self,
        start: date,
        end: date | None = None,
    ) -> pd.DataFrame:
        """Get historical MRI data with raw, normalized, direction columns."""
        end = end or date.today()

        # Collect all indicator histories
        histories = {}
        for ind in self.indicators:
            histories[ind.name] = ind.history(start, end)

        # Find common date range
        all_indices = [h.index for h in histories.values() if not h.empty]
        if not all_indices:
            return pd.DataFrame(columns=["raw", "normalized", "direction"])

        common_index = all_indices[0]
        for idx in all_indices[1:]:
            common_index = common_index.intersection(idx)

        if common_index.empty:
            return pd.DataFrame(columns=["raw", "normalized", "direction"])

        # Compute weighted average of normalized values
        total_weight = sum(
            abs(self.coefficients.get(ind.name, 1.0)) for ind in self.indicators
        )

        normalized = pd.Series(0.0, index=common_index)
        for ind in self.indicators:
            coef = self.coefficients.get(ind.name, 1.0)
            ind_normalized = histories[ind.name].loc[common_index, "normalized"]
            normalized += ind_normalized * coef / total_weight

        # Compute direction from combined normalized values
        direction = compute_direction(normalized)

        return pd.DataFrame(
            {
                "raw": normalized,  # For MRI, raw == normalized (it's already a composite)
                "normalized": normalized,
                "direction": direction,
            }
        )
