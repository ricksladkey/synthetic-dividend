"""Common data types for backtesting algorithms.

Renamed from `types.py` to avoid shadowing the Python standard library module
`types` which causes mypy confusion. Consumers should import from
`src.models.model_types`.
"""

from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class Transaction:
    """Represents a single buy or sell transaction."""

    action: str  # 'BUY' or 'SELL'
    qty: int  # Number of shares
    notes: str = ""  # Optional explanation or metadata
    transaction_date: Optional[date] = None  # Transaction date (filled by backtest engine)
    price: float = 0.0  # Execution price per share (filled by backtest engine)
    ticker: str = ""  # Stock symbol (filled by backtest engine)

    def to_string(self) -> str:
        """Format transaction as human-readable string."""
        if self.transaction_date and self.price > 0:
            value = self.qty * self.price
            return (
                f"{self.transaction_date.isoformat()} {self.action} {self.qty} {self.ticker} "
                f"@ {self.price:.2f} = {value:.2f}  # {self.notes}"
            )
        else:
            # Fallback for transactions without date/price
            return f"{self.action} {self.qty}  # {self.notes}"


@dataclass
class WithdrawalResult:
    """Represents the result of a withdrawal request.

    The algorithm decides how to fulfill a withdrawal request, returning:
    - shares_to_sell: Number of shares to liquidate (0 if using cash only)
    - cash_from_bank: Amount to withdraw from bank balance
    - notes: Optional explanation of the withdrawal strategy
    """

    shares_to_sell: int = 0  # Number of shares to liquidate
    cash_from_bank: float = 0.0  # Amount to withdraw from cash balance
    notes: str = ""  # Optional explanation
