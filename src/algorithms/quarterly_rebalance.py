"""Traditional quarterly portfolio rebalancing algorithm."""

from datetime import date
from typing import Dict, List, Optional

import pandas as pd

from src.algorithms.portfolio_base import PortfolioAlgorithmBase
from src.models.model_types import AssetState, Transaction


class QuarterlyRebalanceAlgorithm(PortfolioAlgorithmBase):
    """Traditional portfolio rebalancing at fixed intervals.

    Rebalances portfolio back to target allocations on specified months
    (typically quarterly: March, June, September, December).

    This is the baseline strategy for comparison against synthetic dividends.

    Example:
        >>> algo = QuarterlyRebalanceAlgorithm(
        ...     target_allocations={'VOO': 0.6, 'BIL': 0.4},
        ...     rebalance_months=[3, 6, 9, 12]
        ... )
    """

    def __init__(
        self,
        target_allocations: Dict[str, float],
        rebalance_months: List[int] = [3, 6, 9, 12],
        min_trade_threshold: float = 100.0,
    ) -> None:
        """Initialize quarterly rebalancing algorithm.

        Args:
            target_allocations: Dict mapping ticker → target allocation (0.0-1.0)
            rebalance_months: List of months (1-12) when rebalancing occurs
            min_trade_threshold: Minimum dollar value to trigger a trade
        """
        self.targets = target_allocations
        self.rebalance_months = rebalance_months
        self.min_trade_threshold = min_trade_threshold
        self.last_rebalance: Optional[date] = None

        # Validate allocations sum to 1.0
        total = sum(target_allocations.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Target allocations must sum to 1.0, got {total:.3f}")

    def on_portfolio_day(
        self,
        date_: date,
        assets: Dict[str, AssetState],
        bank: float,
        prices: Dict[str, pd.Series],
        history: Dict[str, pd.DataFrame],
    ) -> Dict[str, List[Transaction]]:
        """Rebalance portfolio to target allocations if due."""
        # Check if rebalance is due
        if date_.month not in self.rebalance_months:
            return {}

        # Prevent multiple rebalances in same quarter
        if self.last_rebalance is not None:
            days_since_last = (date_ - self.last_rebalance).days
            if days_since_last < 80:  # ~3 months
                return {}

        # Calculate total portfolio value
        total_value = bank + sum(asset.holdings * asset.price for asset in assets.values())

        # Generate rebalancing trades
        transactions: Dict[str, List[Transaction]] = {}

        for ticker, target_pct in self.targets.items():
            asset = assets[ticker]
            current_value = asset.holdings * asset.price
            target_value = total_value * target_pct
            diff = target_value - current_value

            # Only trade if difference exceeds threshold
            if abs(diff) > self.min_trade_threshold:
                qty = int(abs(diff) / asset.price)
                if qty > 0:
                    if diff > 0:
                        # Need to buy
                        action = "BUY"
                    else:
                        # Need to sell
                        action = "SELL"

                    transactions[ticker] = [
                        Transaction(
                            transaction_date=date_,
                            action=action,
                            qty=qty,
                            price=asset.price,
                            ticker=ticker,
                            notes=f"Quarterly rebalance to {target_pct*100:.1f}%",
                        )
                    ]

        # Record rebalance date
        if transactions:
            self.last_rebalance = date_

        return transactions
