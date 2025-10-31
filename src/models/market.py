"""Market order execution engine for backtesting.

Provides Order and Market abstractions to handle limit order placement,
trigger detection, and execution mechanics. Algorithms place orders,
the Market executes them based on price action.
"""

from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import List, Optional

import pandas as pd

from src.models.model_types import Transaction


class OrderType(Enum):
    """Order type: market or limit."""

    MARKET = "MARKET"
    LIMIT = "LIMIT"


class OrderAction(Enum):
    """Order action: buy or sell."""

    BUY = "BUY"
    SELL = "SELL"


@dataclass
class Order:
    """Represents a pending order to buy or sell shares.

    Limit orders trigger when price crosses threshold.
    Market orders execute immediately at current price.

    Orders placed on day D cannot execute until day D+1 to prevent
    chattering when multiple bracket levels trigger on the same day.
    """

    action: OrderAction
    quantity: int
    order_type: OrderType = OrderType.LIMIT
    limit_price: Optional[float] = None
    notes: str = ""
    placed_date: Optional[date] = None  # Date order was placed (for anti-chatter logic)

    def __post_init__(self):
        """Validate order parameters."""
        if self.quantity <= 0:
            raise ValueError(f"Order quantity must be positive, got {self.quantity}")
        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit orders require a limit_price")
        if self.order_type == OrderType.LIMIT:
            assert self.limit_price is not None, "Limit price should be set for LIMIT orders"
            if self.limit_price <= 0:
                raise ValueError(f"Limit price must be positive, got {self.limit_price}")

    def is_triggered(self, low: float, high: float) -> bool:
        """Check if order is triggered by day's price action.

        Args:
            low: Day's low price
            high: Day's high price

        Returns:
            True if order should execute
        """
        if self.order_type == OrderType.MARKET:
            return True

        # Limit order logic - limit_price is guaranteed to be set
        assert self.limit_price is not None, "Limit price should be set for LIMIT orders"
        if self.action == OrderAction.BUY:
            # Buy limit triggers when price drops to or below limit
            return low <= self.limit_price
        else:  # SELL
            # Sell limit triggers when price rises to or above limit
            return high >= self.limit_price

    def get_execution_price(self, open_price: Optional[float], low: float, high: float) -> float:
        """Determine execution price for triggered order using REALISTIC market logic.

        Market orders: fill at open price
        Limit orders: fill at limit if within day's range, fill at open if gapped through

        This models real market behavior where gaps result in fills at the gap price,
        which AMPLIFIES volatility alpha by giving better fills than the limit price.

        Args:
            open_price: Day's opening price
            low: Day's low price
            high: Day's high price

        Returns:
            Realistic execution price
        """
        if self.order_type == OrderType.MARKET:
            if open_price is not None:
                return open_price
            # Fallback if no open price available
            return self.limit_price if self.limit_price else 0.0

        # Limit orders: realistic market execution
        assert self.limit_price is not None, "Limit price should be set for LIMIT orders"

        if self.action == OrderAction.BUY:
            # BUY limit: want to buy at limit or BETTER (lower)
            # Gap scenario: entire day's range is BELOW limit (limit > high)
            # Example: limit=$50, range=[$45, $48] → we get filled at open ($46)
            if open_price is not None and self.limit_price > high:
                # Price gapped down through our limit - fill at open (better price for us!)
                return open_price
            else:
                # Limit was within or above range - fill at limit
                return self.limit_price
        else:  # SELL
            # SELL limit: want to sell at limit or BETTER (higher)
            # Gap scenario: entire day's range is ABOVE limit (limit < low)
            # Example: limit=$50, range=[$52, $55] → we get filled at open ($54)
            if open_price is not None and self.limit_price < low:
                # Price gapped up through our limit - fill at open (better price for us!)
                return open_price
            else:
                # Limit was within or below range - fill at limit
                return self.limit_price


class Market:
    """Market execution engine that processes pending orders.

    Algorithms place orders with the market, which evaluates them
    against price action and executes fills. Handles:
    - Order book management
    - Trigger detection (limit orders)
    - Multi-bracket gap handling (iterative execution)
    - Transaction creation
    """

    def __init__(self):
        """Initialize empty order book."""
        self.pending_orders: List[Order] = []

    def place_order(self, order: Order) -> None:
        """Add an order to the pending order book.

        Args:
            order: Order to place
        """
        self.pending_orders.append(order)

    def clear_orders(self) -> None:
        """Remove all pending orders from the book."""
        self.pending_orders = []

    def evaluate_day(
        self, date_: date, price_row: pd.Series, max_iterations: int = 20
    ) -> List[Transaction]:
        """Evaluate pending orders against day's price action.

        Iterates to handle multi-bracket gaps: if executing an order
        places a new order that's also triggered, execute it too.

        Args:
            date_: Current date
            price_row: OHLC price data for the day
            max_iterations: Safety limit to prevent infinite loops

        Returns:
            List of executed transactions
        """
        transactions: List[Transaction] = []

        # Extract OHLC prices (use .get() for safe access)
        open_price = price_row.get("Open")
        high = price_row.get("High")
        low = price_row.get("Low")

        # Convert to scalars if they are Series
        if open_price is not None and hasattr(open_price, "item"):
            open_price = open_price.item()
        if high is not None and hasattr(high, "item"):
            high = high.item()
        if low is not None and hasattr(low, "item"):
            low = low.item()

        # Need high/low to evaluate orders
        if low is None or high is None:
            return transactions

        # Iterate to handle cascading triggers (multi-bracket gaps)
        for iteration in range(1, max_iterations + 1):
            executed_this_round = False

            # Check each pending order
            orders_to_remove = []
            for i, order in enumerate(self.pending_orders):
                # Anti-chatter: skip orders placed today (they execute tomorrow)
                if order.placed_date is not None and order.placed_date == date_:
                    continue

                if order.is_triggered(low, high):
                    # Execute the order with realistic market fills
                    actual_price = order.get_execution_price(open_price, low, high)

                    # Build transaction notes
                    if order.order_type == OrderType.LIMIT:
                        notes = f"{order.notes} #{iteration}: limit=${order.limit_price:.2f}, filled=${actual_price:.2f}"
                        limit_price = order.limit_price
                    else:
                        notes = f"{order.notes} #{iteration}: market fill=${actual_price:.2f}"
                        limit_price = None

                    transaction = Transaction(
                        action=order.action.value, qty=order.quantity, notes=notes.strip(), limit_price=limit_price
                    )
                    transactions.append(transaction)

                    # Mark order for removal
                    orders_to_remove.append(i)
                    executed_this_round = True

            # Remove executed orders (reverse order to preserve indices)
            for i in reversed(orders_to_remove):
                self.pending_orders.pop(i)

            # If no orders executed this iteration, we're done
            if not executed_this_round:
                break

        return transactions

    def has_pending_orders(self) -> bool:
        """Check if there are any pending orders.

        Returns:
            True if order book is not empty
        """
        return len(self.pending_orders) > 0

    def get_pending_order_count(self) -> int:
        """Get number of pending orders.

        Returns:
            Count of orders in book
        """
        return len(self.pending_orders)
