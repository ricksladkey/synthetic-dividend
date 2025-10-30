"""Abstract base class for portfolio-level trading algorithms."""

from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, List

import pandas as pd

from src.models.model_types import AssetState, Transaction


class PortfolioAlgorithmBase(ABC):
    """Abstract base class for portfolio-level trading algorithms.

    Portfolio algorithms make decisions across the entire portfolio,
    seeing all asset positions and the shared cash pool.

    Subclasses must implement one method:
    - on_portfolio_day: Called each trading day with full portfolio state
    """

    @abstractmethod
    def on_portfolio_day(
        self,
        date_: date,
        assets: Dict[str, AssetState],
        bank: float,
        prices: Dict[str, pd.Series],
        history: Dict[str, pd.DataFrame],
    ) -> Dict[str, List[Transaction]]:
        """Process one trading day at portfolio level, return transactions by ticker.

        Args:
            date_: Current date
            assets: Dict of ticker → AssetState (current position per asset)
            bank: Shared cash pool balance (may be negative if allow_margin=True)
            prices: Dict of ticker → OHLC prices for current day
            history: Dict of ticker → all price data up to previous day

        Returns:
            Dict of ticker → list of transactions for that asset
            Empty dict or empty lists if no transactions
        """
