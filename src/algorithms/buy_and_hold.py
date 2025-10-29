"""Buy-and-hold algorithm: passive investment strategy."""

from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

from src.algorithms.base import AlgorithmBase
from src.models.model_types import Transaction


class BuyAndHoldAlgorithm(AlgorithmBase):
    """Passive buy-and-hold strategy: no trades after initial purchase."""

    def __init__(
        self,
        rebalance_size_pct: float = 0.0,
        profit_sharing_pct: float = 0.0,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize (params ignored for compatibility)."""
        super().__init__(params)

    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        """No-op: no initialization needed."""

    def on_day(
        self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame
    ) -> List[Transaction]:
        """Always returns empty list: hold position."""
        return []

    def on_end_holding(self) -> None:
        """No-op: no cleanup needed."""
