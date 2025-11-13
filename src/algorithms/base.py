"""Abstract base class for trading algorithms."""

import math
from abc import ABC, abstractmethod
from datetime import date
from typing import Any, Dict, List, Optional

import pandas as pd

# Import Transaction and WithdrawalResult from types module
from src.models.model_types import Transaction, WithdrawalResult


class AlgorithmBase(ABC):
    """Abstract base class for trading algorithms.

    Subclasses must implement three lifecycle hooks:
    - on_new_holdings: Called after initial purchase
    - on_day: Called each trading day, returns Transaction or None
    - on_end_holding: Called at end of backtest period
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with optional parameters dict."""
        self.params: Dict[str, Any] = params or {}

    @abstractmethod
    def on_new_holdings(self, holdings: float, current_price: float) -> None:
        """Initialize algorithm state after initial purchase.

        Args:
            holdings: Initial share count (changed from int to float for fractional shares)
            current_price: Price at initial purchase
        """

    @abstractmethod
    def on_day(
        self, date_: date, price_row: pd.Series, holdings: float, bank: float, history: pd.DataFrame
    ) -> List[Transaction]:
        """Process one trading day, return list of transactions executed.

        CRITICAL: This method should loop internally to process ALL triggered orders on the same day.
        This is essential for handling multi-bracket gaps (e.g., 20% gap with 9% brackets).

        Args:
            date_: Current date
            price_row: OHLC prices for current day
            holdings: Current share count (changed from int to float for fractional shares)
            bank: Current cash balance (may be negative)
            history: All price data up to previous day

        Returns:
            List of transactions executed on this day (may be empty if no triggers)
        """

    @abstractmethod
    def on_end_holding(self) -> None:
        """Cleanup/reporting after backtest completes."""

    def on_withdrawal(
        self,
        date_: date,
        requested_amount: float,
        current_price: float,
        holdings: float,
        bank: float,
        allow_margin: bool,
    ) -> WithdrawalResult:
        """Handle a withdrawal request, deciding how to fulfill it.

        Default implementation: Use cash first, then sell shares if needed.
        Subclasses can override to implement custom withdrawal strategies.

        Args:
            date_: Current date
            requested_amount: Amount of cash requested for withdrawal
            current_price: Current share price
            holdings: Current share count (changed from int to float for fractional shares)
            bank: Current cash balance (may be negative)
            allow_margin: Whether negative bank balance is allowed

        Returns:
            WithdrawalResult specifying how to fulfill the withdrawal
        """
        # Default strategy: cash first, then shares
        if bank >= requested_amount:
            # Sufficient cash - withdraw from bank only
            return WithdrawalResult(
                shares_to_sell=0,
                cash_from_bank=requested_amount,
                notes="Withdrawal from cash balance",
            )
        else:
            # Insufficient cash - need to sell shares
            # In allow_margin mode: only cover withdrawal
            # In strict mode: cover withdrawal AND repay any negative balance
            if allow_margin:
                cash_needed = requested_amount - max(0, bank)
            else:
                # Strict mode: also need to cover negative bank balance
                cash_needed = requested_amount - bank  # If bank<0, this increases cash_needed

            shares_to_sell: float = math.ceil(
                cash_needed / current_price
            )  # Allow fractional shares
            shares_to_sell = min(shares_to_sell, holdings)  # Cap at available

            # Calculate actual cash available from bank after share sale
            cash_from_bank = requested_amount

            return WithdrawalResult(
                shares_to_sell=shares_to_sell,
                cash_from_bank=cash_from_bank,
                notes=f"Selling {shares_to_sell} shares for withdrawal (need ${requested_amount:.2f})",
            )
