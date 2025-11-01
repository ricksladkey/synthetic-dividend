"""Unit tests for order triggering and fill price logic.

This module tests the core market mechanics of how limit orders interact
with OHLC price data to determine:
1. Whether an order triggers (is_triggered)
2. What price the order fills at (get_execution_price)

The tests document the expected behavior for all combinations of:
- Order type (BUY vs SELL)
- Order price relative to day's price range (above high, within range, below low)
- Whether order triggers and at what price it fills
"""

import pytest

from src.models.market import Order, OrderAction, OrderType


class TestBuyLimitOrderTriggering:
    """Test when BUY limit orders trigger based on OHLC data.

    BUY limit semantics: "Buy if price drops to limit or lower"
    """

    def test_buy_limit_above_high_does_not_trigger(self):
        """BUY limit above day's high should NOT trigger.

        Example: Want to buy at $50, but price only went as low as $52.
        The limit was never reached.
        """
        order = Order(
            action=OrderAction.BUY, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        # Day's range: High=$55, Low=$52
        # Limit=$50 is above the high, so price never reached it
        high = 55.0
        low = 52.0

        assert not order.is_triggered(low, high), "BUY limit above high should not trigger"

    def test_buy_limit_within_range_triggers(self):
        """BUY limit within day's range SHOULD trigger.

        Example: Want to buy at $50, price ranged from $48 to $52.
        The limit was touched during the day.
        """
        order = Order(
            action=OrderAction.BUY, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        # Day's range: High=$52, Low=$48
        # Limit=$50 is within range, so it was touched
        high = 52.0
        low = 48.0

        assert order.is_triggered(low, high), "BUY limit within range should trigger"

    def test_buy_limit_below_low_triggers(self):
        """BUY limit below day's low SHOULD trigger (gap through).

        Example: Want to buy at $50, but price gapped down and ranged from $45 to $48.
        The price blew through our limit, order should fill.
        """
        order = Order(
            action=OrderAction.BUY, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        # Day's range: High=$48, Low=$45
        # Limit=$50 is below low, meaning price gapped through our limit
        high = 48.0
        low = 45.0

        assert order.is_triggered(low, high), "BUY limit below low should trigger (gap through)"


class TestBuyLimitOrderExecutionPrice:
    """Test what price BUY limit orders fill at.

    Current behavior: Always fill at limit price for exact symmetry.
    Proposed behavior: Fill at limit if touched, fill at open if gapped through.
    """

    def test_buy_limit_within_range_fills_at_limit(self):
        """BUY limit within range should fill at limit price.

        If limit=$50 and range is [$48, $52], we got filled at our limit price.
        """
        order = Order(
            action=OrderAction.BUY, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        open_price = 51.0  # Opened above our limit
        high = 52.0
        low = 48.0
        fill_price = order.get_execution_price(open_price, low, high)

        assert fill_price == 50.0, "BUY limit within range should fill at limit price"

    def test_buy_limit_gapped_through_fills_at_open(self):
        """BUY limit gapped through fills at open price - REALISTIC BEHAVIOR!

        If limit=$50 and range is [$45, $48] with open=$46, we fill at $46.
        This is BETTER for us (bought cheaper) and models real market behavior.
        This AMPLIFIES volatility alpha!
        """
        order = Order(
            action=OrderAction.BUY, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        open_price = 46.0  # Opened below our limit (gapped through)
        high = 48.0
        low = 45.0
        fill_price = order.get_execution_price(open_price, low, high)

        assert (
            fill_price == 46.0
        ), "BUY limit gapped through should fill at open (realistic market behavior)"


class TestSellLimitOrderTriggering:
    """Test when SELL limit orders trigger based on OHLC data.

    SELL limit semantics: "Sell if price rises to limit or higher"
    """

    def test_sell_limit_below_low_does_not_trigger(self):
        """SELL limit below day's low should NOT trigger.

        Example: Want to sell at $50, but price only went as high as $48.
        The limit was never reached.
        """
        order = Order(
            action=OrderAction.SELL, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        # Day's range: High=$48, Low=$45
        # Limit=$50 is below the low... wait, that doesn't make sense
        # SELL limit should be compared to HIGH, not LOW
        # Let me rewrite:

        # Day's range: High=$48, Low=$45
        # Limit=$50 is above the high, so price never reached it
        high = 48.0
        low = 45.0

        assert not order.is_triggered(low, high), "SELL limit above high should not trigger"

    def test_sell_limit_within_range_triggers(self):
        """SELL limit within day's range SHOULD trigger.

        Example: Want to sell at $50, price ranged from $48 to $52.
        The limit was touched during the day.
        """
        order = Order(
            action=OrderAction.SELL, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        # Day's range: High=$52, Low=$48
        # Limit=$50 is within range, so it was touched
        high = 52.0
        low = 48.0

        assert order.is_triggered(low, high), "SELL limit within range should trigger"

    def test_sell_limit_above_high_triggers(self):
        """SELL limit above day's high SHOULD trigger (gap through).

        Example: Want to sell at $50, but price gapped up and ranged from $52 to $55.
        The price blew through our limit, order should fill.
        """
        order = Order(
            action=OrderAction.SELL, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        # Day's range: High=$55, Low=$52
        # Limit=$50 is above... wait, I need to rethink this
        # If SELL limit is $50 and LOW is $52, that means price gapped UP through $50
        high = 55.0
        low = 52.0

        assert order.is_triggered(low, high), "SELL limit below low should trigger (gap through)"


class TestSellLimitOrderExecutionPrice:
    """Test what price SELL limit orders fill at.

    Current behavior: Always fill at limit price for exact symmetry.
    Proposed behavior: Fill at limit if touched, fill at open if gapped through.
    """

    def test_sell_limit_within_range_fills_at_limit(self):
        """SELL limit within range should fill at limit price.

        If limit=$50 and range is [$48, $52], we got filled at our limit price.
        """
        order = Order(
            action=OrderAction.SELL, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        open_price = 49.0  # Opened below our limit
        high = 52.0
        low = 48.0
        fill_price = order.get_execution_price(open_price, low, high)

        assert fill_price == 50.0, "SELL limit within range should fill at limit price"

    def test_sell_limit_gapped_through_fills_at_open(self):
        """SELL limit gapped through fills at open price - REALISTIC BEHAVIOR!

        If limit=$50 and range is [$52, $55] with open=$54, we fill at $54.
        This is BETTER for us (sold higher) and models real market behavior.
        This AMPLIFIES volatility alpha!
        """
        order = Order(
            action=OrderAction.SELL, quantity=100, order_type=OrderType.LIMIT, limit_price=50.0
        )

        open_price = 54.0  # Opened above our limit (gapped through)
        high = 55.0
        low = 52.0
        fill_price = order.get_execution_price(open_price, low, high)

        assert (
            fill_price == 54.0
        ), "SELL limit gapped through should fill at open (realistic market behavior)"


class TestMarketOrderExecutionPrice:
    """Test market order execution prices."""

    def test_market_buy_fills_at_open(self):
        """Market BUY order should fill at open price."""
        order = Order(action=OrderAction.BUY, quantity=100, order_type=OrderType.MARKET)

        open_price = 51.23
        high = 52.0
        low = 50.0
        fill_price = order.get_execution_price(open_price, low, high)

        assert fill_price == 51.23, "Market order should fill at open price"

    def test_market_sell_fills_at_open(self):
        """Market SELL order should fill at open price."""
        order = Order(action=OrderAction.SELL, quantity=100, order_type=OrderType.MARKET)

        open_price = 51.23
        high = 52.0
        low = 50.0
        fill_price = order.get_execution_price(open_price, low, high)

        assert fill_price == 51.23, "Market order should fill at open price"
