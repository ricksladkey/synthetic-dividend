"""Lot selection strategies for tax and accounting purposes.

Lot selection determines which shares to sell when you have multiple purchases
at different prices and dates. This affects cost basis, capital gains, and taxes.

Design Philosophy:
- Strategy pattern: Each selection method is a pluggable strategy
- Orthogonal to algorithms: Works with any trading algorithm
- Extensible: Easy to add new strategies (tax optimization, etc.)
- Testable: Each strategy can be tested independently
"""

from abc import ABC, abstractmethod
from typing import Iterator, List

from src.models.holding import Transaction


class LotSelector(ABC):
    """Abstract base class for lot selection strategies."""

    @abstractmethod
    def select_lots(self, transactions: List[Transaction]) -> Iterator[Transaction]:
        """
        Select which lots to sell, in order.

        Args:
            transactions: List of all transactions (BUY and SELL)

        Yields:
            Open BUY transactions in the order they should be sold
        """

    @abstractmethod
    def name(self) -> str:
        """Return the name of this strategy (e.g., 'FIFO', 'LIFO')."""


class FIFOSelector(LotSelector):
    """First-In-First-Out: Sell oldest purchases first.

    This is the default method and most common for tax purposes.
    Generally results in higher capital gains (sells appreciated shares first).

    Tax Implications:
    - Sells long-term holdings first (lower tax rate)
    - Higher cost basis = lower taxable gains (in declining market)
    - Most conservative and widely accepted
    """

    def select_lots(self, transactions: List[Transaction]) -> Iterator[Transaction]:
        """Yield open BUY transactions from oldest to newest."""
        for txn in transactions:
            if txn.transaction_type == "BUY" and txn.is_open:
                yield txn

    def name(self) -> str:
        return "FIFO"


class LIFOSelector(LotSelector):
    """Last-In-First-Out: Sell newest purchases first.

    Can reduce short-term capital gains by selling recently purchased shares.
    Useful for tax-loss harvesting or managing wash sale rules.

    Tax Implications:
    - May result in short-term capital gains (higher tax rate)
    - Lower cost basis = higher taxable gains (in rising market)
    - Can defer long-term gains

    Use Cases:
    - Volatile markets where recent buys have losses
    - When you want to preserve older, lower-cost lots
    - Strategic tax-loss harvesting
    """

    def select_lots(self, transactions: List[Transaction]) -> Iterator[Transaction]:
        """Yield open BUY transactions from newest to oldest."""
        for txn in reversed(transactions):
            if txn.transaction_type == "BUY" and txn.is_open:
                yield txn

    def name(self) -> str:
        return "LIFO"


class HighestCostSelector(LotSelector):
    """Sell shares with highest cost basis first (minimize gains).

    Tax Optimization Strategy:
    - Minimizes taxable capital gains
    - Useful when you expect lower tax rates in future
    - Good for tax-loss harvesting

    Use Cases:
    - High-income year (minimize current taxes)
    - Rebalancing without triggering large gains
    - Losses can offset other gains
    """

    def select_lots(self, transactions: List[Transaction]) -> Iterator[Transaction]:
        """Yield open BUY transactions from highest to lowest cost."""
        open_buys = [t for t in transactions if t.transaction_type == "BUY" and t.is_open]
        # Sort by purchase price descending
        sorted_buys = sorted(open_buys, key=lambda t: t.purchase_price, reverse=True)
        yield from sorted_buys

    def name(self) -> str:
        return "HIGHEST_COST"


class LowestCostSelector(LotSelector):
    """Sell shares with lowest cost basis first (maximize gains).

    Tax Optimization Strategy:
    - Maximizes realized capital gains
    - Useful when you want to use capital gains exemption
    - Good for low-income years or long-term capital gains rates

    Use Cases:
    - Low-income year (utilize lower tax bracket)
    - Harvest long-term gains at favorable rates
    - Step-up cost basis strategy (estate planning)
    """

    def select_lots(self, transactions: List[Transaction]) -> Iterator[Transaction]:
        """Yield open BUY transactions from lowest to highest cost."""
        open_buys = [t for t in transactions if t.transaction_type == "BUY" and t.is_open]
        # Sort by purchase price ascending
        sorted_buys = sorted(open_buys, key=lambda t: t.purchase_price)
        yield from sorted_buys

    def name(self) -> str:
        return "LOWEST_COST"


# Registry for easy lookup
_SELECTORS = {
    "FIFO": FIFOSelector(),
    "LIFO": LIFOSelector(),
    "HIGHEST_COST": HighestCostSelector(),
    "LOWEST_COST": LowestCostSelector(),
}


def get_selector(strategy: str) -> LotSelector:
    """
    Get a lot selector by name.

    Args:
        strategy: Name of strategy ('FIFO', 'LIFO', 'HIGHEST_COST', 'LOWEST_COST')

    Returns:
        LotSelector instance

    Raises:
        ValueError: If strategy name is not recognized

    Example:
        >>> selector = get_selector('LIFO')
        >>> selector.name()
        'LIFO'
    """
    if strategy not in _SELECTORS:
        available = ", ".join(_SELECTORS.keys())
        raise ValueError(f"Unknown lot selection strategy '{strategy}'. " f"Available: {available}")
    return _SELECTORS[strategy]


def available_strategies() -> List[str]:
    """
    Get list of available lot selection strategies.

    Returns:
        List of strategy names

    Example:
        >>> available_strategies()
        ['FIFO', 'LIFO', 'HIGHEST_COST', 'LOWEST_COST']
    """
    return list(_SELECTORS.keys())
