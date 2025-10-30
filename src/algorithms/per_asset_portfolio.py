"""Adapter that runs per-asset algorithms in portfolio context."""

from datetime import date
from typing import Dict, List

import pandas as pd

from src.algorithms.base import AlgorithmBase
from src.algorithms.portfolio_base import PortfolioAlgorithmBase
from src.models.model_types import AssetState, Transaction


class PerAssetPortfolioAlgorithm(PortfolioAlgorithmBase):
    """Runs per-asset algorithms in portfolio context with shared cash pool.

    This is the adapter that connects the two algorithm levels:
    - Takes a dict of per-asset algorithms
    - Implements portfolio interface
    - Delegates to each asset's algorithm

    Example:
        >>> hybrid = PerAssetPortfolioAlgorithm({
        ...     'NVDA': SyntheticDividendAlgorithm(0.0905, 50.0),
        ...     'BTC-USD': SyntheticDividendAlgorithm(0.1892, 50.0),
        ...     'VOO': BuyAndHoldAlgorithm(),
        ... })
    """

    def __init__(self, strategies: Dict[str, AlgorithmBase]) -> None:
        """Initialize with per-asset strategies.

        Args:
            strategies: Dict mapping ticker → algorithm instance
        """
        self.strategies = strategies

    def on_portfolio_day(
        self,
        date_: date,
        assets: Dict[str, AssetState],
        bank: float,
        prices: Dict[str, pd.Series],
        history: Dict[str, pd.DataFrame],
    ) -> Dict[str, List[Transaction]]:
        """Run each asset's algorithm independently with shared bank view.

        Each algorithm sees the shared bank balance but makes independent decisions.
        The backtest engine will execute transactions sequentially and update the
        shared bank accordingly.
        """
        transactions: Dict[str, List[Transaction]] = {}

        for ticker, algo in self.strategies.items():
            # Call per-asset algorithm
            txns = algo.on_day(
                date_=date_,
                price_row=prices[ticker],
                holdings=assets[ticker].holdings,
                bank=bank,  # Shared bank - algorithm sees current balance
                history=history[ticker],
            )
            transactions[ticker] = txns

        return transactions
