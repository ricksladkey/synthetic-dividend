"""
Account: A trading account with portfolio and debt tracking.

An Account represents a brokerage account that contains:
- Portfolio: Assets owned (stocks, ETFs, etc.)
- Debt: Money borrowed (margin/borrowing)

Design Philosophy:
- Portfolio tracks what you OWN (always positive positions)
- Debt tracks what you OWE (can be negative = borrowed)
- Clean separation of assets vs liabilities
- Account = Portfolio + Debt = Net worth
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

from src.models.holding import Transaction
from src.models.portfolio import Portfolio


@dataclass
class Account:
    """
    A brokerage account with assets (portfolio) and liabilities (debt).

    Conceptual Model:
    - Portfolio: What you own (NVDA shares, VOO shares, etc.)
    - Debt: What you owe (borrowed money for margin trading)
    - Net Worth = Portfolio Value - Debt

    Example:
        >>> account = Account()
        >>> # Buy $1M of NVDA on margin (borrow the money)
        >>> account.borrow(1_000_000, date(2024, 1, 1), "Initial margin loan")
        >>> account.portfolio.buy("NVDA", shares=10000, purchase_date=..., purchase_price=100.0)
        >>>
        >>> # Sell some NVDA, pay back debt
        >>> account.portfolio.sell("NVDA", shares=1000, sale_date=..., sale_price=110.0)
        >>> account.repay(110_000, date(2024, 2, 1), "Partial repayment")
        >>>
        >>> # Check account status
        >>> account.net_worth(prices={"NVDA": 110.0})
        >>> # Portfolio: 9000 × $110 = $990,000
        >>> # Debt: $890,000
        >>> # Net Worth: $100,000
    """

    portfolio: Portfolio = field(default_factory=Portfolio)
    debt: float = 0.0  # Amount owed (positive = borrowed, negative = cash on hand)

    # Debt tracking for statistics
    debt_history: List[tuple[date, float]] = field(default_factory=list)

    def borrow(self, amount: float, borrow_date: date, notes: str = "") -> None:
        """
        Borrow money (increase debt).

        Args:
            amount: Dollar amount to borrow (positive)
            borrow_date: Date of borrowing
            notes: Optional explanation
        """
        if amount <= 0:
            raise ValueError(f"Borrow amount must be positive, got: {amount}")

        self.debt += amount
        self.debt_history.append((borrow_date, self.debt))

    def repay(self, amount: float, repay_date: date, notes: str = "") -> None:
        """
        Repay borrowed money (decrease debt).

        Args:
            amount: Dollar amount to repay (positive)
            repay_date: Date of repayment
            notes: Optional explanation
        """
        if amount <= 0:
            raise ValueError(f"Repay amount must be positive, got: {amount}")

        self.debt -= amount
        self.debt_history.append((repay_date, self.debt))

    def deposit_cash(self, amount: float, deposit_date: date, notes: str = "") -> None:
        """
        Deposit cash into account (reduces debt or creates negative debt = cash).

        Args:
            amount: Dollar amount to deposit (positive)
            deposit_date: Date of deposit
            notes: Optional explanation
        """
        if amount <= 0:
            raise ValueError(f"Deposit amount must be positive, got: {amount}")

        # Depositing cash reduces debt (or makes debt negative = cash surplus)
        self.debt -= amount
        self.debt_history.append((deposit_date, self.debt))

    def withdraw_cash(self, amount: float, withdraw_date: date, notes: str = "") -> None:
        """
        Withdraw cash from account (increases debt or uses cash if available).

        Args:
            amount: Dollar amount to withdraw (positive)
            withdraw_date: Date of withdrawal
            notes: Optional explanation
        """
        if amount <= 0:
            raise ValueError(f"Withdraw amount must be positive, got: {amount}")

        # Withdrawing cash increases debt (or reduces cash surplus)
        self.debt += amount
        self.debt_history.append((withdraw_date, self.debt))

    def net_worth(self, prices: Dict[str, float]) -> float:
        """
        Calculate account net worth: Portfolio Value - Debt.

        Args:
            prices: Dictionary mapping ticker → current price

        Returns:
            Net worth (can be negative if overleveraged)
        """
        portfolio_value = self.portfolio.total_value(prices)
        return portfolio_value - self.debt

    def debt_statistics(self) -> Dict[str, float]:
        """
        Calculate debt statistics over account history.

        Returns:
            Dictionary with min, max, avg debt levels
        """
        if not self.debt_history:
            return {"min_debt": 0.0, "max_debt": 0.0, "avg_debt": 0.0, "current_debt": self.debt}

        debt_balances = [debt for _, debt in self.debt_history]

        return {
            "min_debt": min(debt_balances),
            "max_debt": max(debt_balances),
            "avg_debt": sum(debt_balances) / len(debt_balances),
            "current_debt": self.debt,
        }

    def cash_balance(self) -> float:
        """
        Get current cash balance (negative debt = cash, positive debt = borrowed).

        Returns:
            Cash balance: negative debt means cash on hand, positive means borrowed
        """
        return -self.debt

    def has_margin_debt(self) -> bool:
        """Check if account currently has margin debt (borrowed money)."""
        return self.debt > 0

    def has_cash(self) -> bool:
        """Check if account currently has cash (negative debt)."""
        return self.debt < 0

    def account_summary(self, prices: Dict[str, float]) -> Dict:
        """
        Get comprehensive account summary.

        Args:
            prices: Dictionary mapping ticker → current price

        Returns:
            Dictionary with account-level statistics
        """
        portfolio_value = self.portfolio.total_value(prices)
        net = self.net_worth(prices)
        debt_stats = self.debt_statistics()

        return {
            "portfolio_value": portfolio_value,
            "debt": self.debt,
            "cash_balance": self.cash_balance(),
            "net_worth": net,
            "leverage_ratio": portfolio_value / net if net > 0 else float("inf"),
            "debt_stats": debt_stats,
            "portfolio_summary": self.portfolio.portfolio_summary(prices),
        }

    def __str__(self) -> str:
        """Human-readable account summary."""
        cash_or_debt = f"${abs(self.debt):,.2f} {'cash' if self.debt < 0 else 'debt'}"
        return f"Account: {self.portfolio} | {cash_or_debt}"

    def __repr__(self) -> str:
        return f"Account(portfolio={repr(self.portfolio)}, debt={self.debt:.2f})"
