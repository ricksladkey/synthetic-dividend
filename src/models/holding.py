"""
Holding: A clean transaction-based model for tracking stock positions.

A Holding represents ownership of a single ticker through all its transactions.
This is the foundational building block for portfolio management.

Design Philosophy:
- Transaction history is the source of truth
- Current state is derived, not stored
- Simple, beautiful conceptual model
- Easy to audit and reconstruct
"""

from dataclasses import dataclass, field
from datetime import date
from typing import List, Optional


@dataclass
class Transaction:
    """
    A single buy or sell transaction for a ticker.

    This is the atomic unit of trading activity. A transaction records:
    - What happened (BUY or SELL)
    - How many shares
    - When it happened (purchase_date)
    - At what price (purchase_price)
    - For sells: when closed (sale_date) and at what price (sale_price)

    Design Notes:
    - sale_date = None means position is still open (held today)
    - sale_price = None means position is still open (use current market price)
    - ticker is stored at Holding level, not per transaction (single-ticker invariant)
    """

    transaction_type: str  # 'BUY' or 'SELL'
    shares: int  # Number of shares (always positive)
    purchase_date: date  # When the transaction occurred
    purchase_price: float  # Price per share at purchase

    # For SELL transactions or closed positions:
    sale_date: Optional[date] = None  # None = still held
    sale_price: Optional[float] = None  # None = use current market price

    # Optional metadata:
    notes: str = ""  # Human-readable explanation ("ATH rebalance", "buyback", etc.)

    def __post_init__(self):
        """Validate transaction invariants."""
        if self.transaction_type not in ("BUY", "SELL"):
            raise ValueError(
                f"transaction_type must be 'BUY' or 'SELL', got: {self.transaction_type}"
            )
        if self.shares <= 0:
            raise ValueError(f"shares must be positive, got: {self.shares}")
        if self.purchase_price <= 0:
            raise ValueError(f"purchase_price must be positive, got: {self.purchase_price}")

        # Sale validation
        if self.sale_date is not None or self.sale_price is not None:
            if self.sale_date is None or self.sale_price is None:
                raise ValueError("sale_date and sale_price must both be set or both be None")
            if self.sale_date < self.purchase_date:
                raise ValueError(
                    f"sale_date {self.sale_date} cannot be before purchase_date {self.purchase_date}"
                )

    @property
    def is_open(self) -> bool:
        """Is this position still held (not yet sold)?"""
        return self.sale_date is None

    @property
    def is_closed(self) -> bool:
        """Has this position been sold?"""
        return self.sale_date is not None

    def close(self, sale_date: date, sale_price: float) -> None:
        """
        Close an open position by recording the sale.

        Args:
            sale_date: Date the position was sold
            sale_price: Price per share at sale

        Raises:
            ValueError: If position is already closed
        """
        if self.is_closed:
            raise ValueError(f"Transaction already closed on {self.sale_date}")
        if sale_date < self.purchase_date:
            raise ValueError(
                f"sale_date {sale_date} cannot be before purchase_date {self.purchase_date}"
            )
        if sale_price <= 0:
            raise ValueError(f"sale_price must be positive, got: {sale_price}")

        self.sale_date = sale_date
        self.sale_price = sale_price

    def market_value(self, current_price: float, current_date: Optional[date] = None) -> float:
        """
        Calculate current market value of this transaction.

        For open positions: shares × current_price
        For closed positions: 0 (no longer held)

        Args:
            current_price: Current market price per share
            current_date: Current date (optional, for validation)

        Returns:
            Market value in dollars
        """
        if self.is_closed:
            return 0.0
        return self.shares * current_price

    def realized_gain_loss(self) -> Optional[float]:
        """
        Calculate realized profit/loss for closed positions.

        Returns:
            Profit/loss in dollars, or None if position still open
        """
        if self.is_open:
            return None

        cost_basis = self.shares * self.purchase_price
        proceeds = self.shares * self.sale_price
        return proceeds - cost_basis

    def unrealized_gain_loss(self, current_price: float) -> Optional[float]:
        """
        Calculate unrealized profit/loss for open positions.

        Args:
            current_price: Current market price per share

        Returns:
            Unrealized profit/loss in dollars, or None if position closed
        """
        if self.is_closed:
            return None

        cost_basis = self.shares * self.purchase_price
        current_value = self.shares * current_price
        return current_value - cost_basis

    def __str__(self) -> str:
        """Human-readable transaction summary."""
        status = "OPEN" if self.is_open else "CLOSED"
        base = f"[{status}] {self.purchase_date} {self.transaction_type} {self.shares} @ ${self.purchase_price:.2f}"

        if self.is_closed:
            gain_loss = self.realized_gain_loss()
            base += f" → SOLD {self.sale_date} @ ${self.sale_price:.2f} (P/L: ${gain_loss:.2f})"

        if self.notes:
            base += f" # {self.notes}"

        return base


@dataclass
class Holding:
    """
    A position in a single ticker, tracked through all transactions.

    This is the foundational abstraction: a Holding is simply a ticker
    plus the complete transaction history. Everything else (current shares,
    market value, cost basis) is derived from this history.

    Design Principles:
    - Transaction history is immutable (append-only)
    - Current state is computed, not stored
    - Single ticker per holding (portfolio combines holdings)
    - FIFO cost basis tracking (can be extended to LIFO/specific lot)

    Example:
        >>> holding = Holding(ticker="NVDA")
        >>> holding.add_buy(shares=100, date=date(2024, 1, 1), price=50.0)
        >>> holding.add_sell(shares=50, date=date(2024, 6, 1), price=75.0)
        >>> holding.current_shares()  # 50
        >>> holding.market_value(current_price=80.0)  # 4000.0
    """

    ticker: str
    transactions: List[Transaction] = field(default_factory=list)

    def add_buy(
        self, shares: int, purchase_date: date, purchase_price: float, notes: str = ""
    ) -> Transaction:
        """
        Record a buy transaction.

        Args:
            shares: Number of shares purchased (positive integer)
            purchase_date: Date of purchase
            purchase_price: Price per share
            notes: Optional explanation

        Returns:
            The created Transaction
        """
        txn = Transaction(
            transaction_type="BUY",
            shares=shares,
            purchase_date=purchase_date,
            purchase_price=purchase_price,
            notes=notes,
        )
        self.transactions.append(txn)
        return txn

    def add_sell(
        self,
        shares: int,
        sale_date: date,
        sale_price: float,
        notes: str = "",
        lot_selection: str = "FIFO",
    ) -> List[Transaction]:
        """
        Record a sell transaction using specified lot selection method.

        This creates SELL transactions and matches them against existing
        open BUY transactions to track cost basis.

        Args:
            shares: Number of shares to sell
            sale_date: Date of sale
            sale_price: Price per share
            notes: Optional explanation
            lot_selection: Method for selecting which lots to sell ('FIFO', 'LIFO', etc.)

        Returns:
            List of Transaction objects representing the sale(s)

        Raises:
            ValueError: If trying to sell more shares than currently held
        """
        from src.models.lot_selector import get_selector

        current = self.current_shares()
        if shares > current:
            raise ValueError(
                f"Cannot sell {shares} shares of {self.ticker}: only {current} shares held"
            )

        # Use lot selector strategy to determine order
        selector = get_selector(lot_selection)

        # Process lots in selected order
        remaining_to_sell = shares
        sell_transactions = []

        for txn in selector.select_lots(self.transactions):
            if remaining_to_sell <= 0:
                break

            # Determine how many shares to sell from this lot
            shares_from_this_lot = min(remaining_to_sell, txn.shares)

            # If selling partial lot, we need to split the transaction
            if shares_from_this_lot < txn.shares:
                # Split: Create a new transaction for the unsold portion
                unsold = Transaction(
                    transaction_type="BUY",
                    shares=txn.shares - shares_from_this_lot,
                    purchase_date=txn.purchase_date,
                    purchase_price=txn.purchase_price,
                    notes=f"Split from {txn.notes}" if txn.notes else "Split lot",
                )

                # Update original transaction to reflect only the sold portion
                txn.shares = shares_from_this_lot

                # Insert the unsold portion right after the current transaction
                idx = self.transactions.index(txn)
                self.transactions.insert(idx + 1, unsold)

            # Close this lot (mark as sold)
            txn.close(sale_date=sale_date, sale_price=sale_price)

            # Record the sell transaction
            sell_txn = Transaction(
                transaction_type="SELL",
                shares=shares_from_this_lot,
                purchase_date=sale_date,  # For SELL, purchase_date = sale_date
                purchase_price=sale_price,  # For SELL, purchase_price = sale_price
                sale_date=sale_date,
                sale_price=sale_price,
                notes=notes or f"Sold lot from {txn.purchase_date}",
            )
            sell_transactions.append(sell_txn)
            self.transactions.append(sell_txn)

            remaining_to_sell -= shares_from_this_lot

        return sell_transactions

    def current_shares(self) -> int:
        """
        Calculate total shares currently held (open positions only).

        Returns:
            Number of shares (always >= 0)
        """
        total = 0
        for txn in self.transactions:
            if txn.transaction_type == "BUY" and txn.is_open:
                total += txn.shares
        return total

    def market_value(self, current_price: float, current_date: Optional[date] = None) -> float:
        """
        Calculate total market value of all open positions.

        Args:
            current_price: Current market price per share
            current_date: Current date (optional)

        Returns:
            Total market value in dollars
        """
        return sum(txn.market_value(current_price, current_date) for txn in self.transactions)

    def cost_basis(self) -> float:
        """
        Calculate total cost basis of all open positions.

        Returns:
            Total cost basis in dollars
        """
        total = 0.0
        for txn in self.transactions:
            if txn.transaction_type == "BUY" and txn.is_open:
                total += txn.shares * txn.purchase_price
        return total

    def unrealized_gain_loss(self, current_price: float) -> float:
        """
        Calculate total unrealized profit/loss on open positions.

        Args:
            current_price: Current market price per share

        Returns:
            Unrealized P/L in dollars
        """
        return self.market_value(current_price) - self.cost_basis()

    def realized_gain_loss(self) -> float:
        """
        Calculate total realized profit/loss from closed positions.

        Returns:
            Realized P/L in dollars
        """
        total = 0.0
        for txn in self.transactions:
            if txn.is_closed:
                gain_loss = txn.realized_gain_loss()
                if gain_loss is not None:
                    total += gain_loss
        return total

    def total_gain_loss(self, current_price: float) -> float:
        """
        Calculate total profit/loss (realized + unrealized).

        Args:
            current_price: Current market price per share

        Returns:
            Total P/L in dollars
        """
        return self.realized_gain_loss() + self.unrealized_gain_loss(current_price)

    def average_cost_basis(self) -> float:
        """
        Calculate weighted average cost basis per share for open positions.

        Returns:
            Average cost per share, or 0 if no open positions
        """
        shares = self.current_shares()
        if shares == 0:
            return 0.0
        return self.cost_basis() / shares

    def get_open_lots(self) -> List[Transaction]:
        """
        Get all open (unsold) buy transactions.

        Returns:
            List of open BUY transactions
        """
        return [txn for txn in self.transactions if txn.transaction_type == "BUY" and txn.is_open]

    def get_closed_lots(self) -> List[Transaction]:
        """
        Get all closed (sold) buy transactions.

        Returns:
            List of closed BUY transactions
        """
        return [txn for txn in self.transactions if txn.transaction_type == "BUY" and txn.is_closed]

    def get_sell_transactions(self) -> List[Transaction]:
        """
        Get all sell transactions.

        Returns:
            List of SELL transactions
        """
        return [txn for txn in self.transactions if txn.transaction_type == "SELL"]

    def transaction_summary(self) -> dict:
        """
        Get summary statistics about transactions.

        Returns:
            Dictionary with transaction counts and values
        """
        open_lots = self.get_open_lots()
        closed_lots = self.get_closed_lots()
        sells = self.get_sell_transactions()

        return {
            "ticker": self.ticker,
            "total_transactions": len(self.transactions),
            "open_lots": len(open_lots),
            "closed_lots": len(closed_lots),
            "sell_transactions": len(sells),
            "current_shares": self.current_shares(),
            "cost_basis": self.cost_basis(),
            "realized_gain_loss": self.realized_gain_loss(),
        }

    def __str__(self) -> str:
        """Human-readable holding summary."""
        shares = self.current_shares()
        if shares == 0:
            return f"Holding({self.ticker}): No open positions ({len(self.transactions)} historical transactions)"

        avg_cost = self.average_cost_basis()
        return (
            f"Holding({self.ticker}): {shares} shares @ avg ${avg_cost:.2f} "
            f"({len(self.get_open_lots())} lots, {len(self.transactions)} total transactions)"
        )

    def __repr__(self) -> str:
        return f"Holding(ticker={self.ticker!r}, transactions={len(self.transactions)})"
