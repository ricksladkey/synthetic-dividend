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
    qty: float  # Number of shares (changed from int to float for fractional shares)
    notes: str = ""  # Optional explanation or metadata
    transaction_date: Optional[date] = None  # Transaction date (filled by backtest engine)
    price: float = 0.0  # Execution price per share (filled by backtest engine)
    ticker: str = ""  # Stock symbol (filled by backtest engine)
    limit_price: Optional[float] = None  # Algorithmic limit price (if this was a limit order)

    def to_string(self) -> str:
        """Format transaction as human-readable string."""
        if self.transaction_date and self.price > 0:
            value = self.qty * self.price
            if self.ticker == "CASH":
                # For CASH transactions, qty is in cents, price is $0.01 per cent
                dollar_amount = value
                return (
                    f"{self.transaction_date.isoformat()} {self.action} ${dollar_amount:.2f} {self.ticker} "
                    f"# {self.notes}"
                )
            else:
                # Regular stock transactions
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

    shares_to_sell: float = 0  # Number of shares to liquidate (allow fractional)
    cash_from_bank: float = 0.0  # Amount to withdraw from cash balance
    notes: str = ""  # Optional explanation


@dataclass
class AssetState:
    """Snapshot of single asset position. Pure data, no behavior."""

    ticker: str
    holdings: float  # Share count (changed from int to float for fractional shares)
    price: float  # Current price
