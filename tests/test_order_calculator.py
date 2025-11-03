"""Unit tests for order calculator tool.

Tests verify that the order calculator produces correct results with and without bracket seed.
"""

import math
import unittest

from src.tools.order_calculator import calculate_orders_for_manual_entry


class TestOrderCalculator(unittest.TestCase):
    """Test order calculator functionality."""

    def test_without_bracket_seed(self):
        """Test order calculator without bracket seed."""
        holdings = 1000
        buy_price, buy_qty, sell_price, sell_qty = calculate_orders_for_manual_entry(
            ticker="NVDA",
            holdings=holdings,
            last_transaction_price=120.50,
            current_price=125.30,
            sdn=8,
            profit_sharing_pct=50,
            bracket_seed=None,
        )

        # Verify quantities are reasonable
        self.assertGreater(buy_qty, 0)
        self.assertGreater(sell_qty, 0)
        self.assertLess(buy_qty, holdings)
        self.assertLess(sell_qty, holdings)

        # Verify prices are reasonable relative to last transaction
        self.assertLess(buy_price, 120.50)  # Buy below last transaction
        self.assertGreater(sell_price, 120.50)  # Sell above last transaction

    def test_with_bracket_seed_changes_prices(self):
        """Test that bracket seed changes order prices but not quantities."""
        # Without seed
        buy_price_no_seed, buy_qty_no_seed, sell_price_no_seed, sell_qty_no_seed = (
            calculate_orders_for_manual_entry(
                ticker="NVDA",
                holdings=1000,
                last_transaction_price=120.50,
                current_price=125.30,
                sdn=8,
                profit_sharing_pct=50,
                bracket_seed=None,
            )
        )

        # With seed
        buy_price_with_seed, buy_qty_with_seed, sell_price_with_seed, sell_qty_with_seed = (
            calculate_orders_for_manual_entry(
                ticker="NVDA",
                holdings=1000,
                last_transaction_price=120.50,
                current_price=125.30,
                sdn=8,
                profit_sharing_pct=50,
                bracket_seed=100.0,
            )
        )

        # Quantities should be identical
        self.assertEqual(buy_qty_no_seed, buy_qty_with_seed)
        self.assertEqual(sell_qty_no_seed, sell_qty_with_seed)

        # Prices should be different (aligned to bracket ladder)
        self.assertNotEqual(buy_price_no_seed, buy_price_with_seed)
        self.assertNotEqual(sell_price_no_seed, sell_price_with_seed)

    def test_bracket_seed_changes_results(self):
        """Test that bracket seed produces different results than no seed."""
        # Get results with and without seed
        buy_no_seed, qty_buy_no_seed, sell_no_seed, qty_sell_no_seed = (
            calculate_orders_for_manual_entry(
                ticker="NVDA",
                holdings=1000,
                last_transaction_price=120.50,
                current_price=125.30,
                sdn=8,
                profit_sharing_pct=50,
                bracket_seed=None,
            )
        )

        buy_with_seed, qty_buy_with_seed, sell_with_seed, qty_sell_with_seed = (
            calculate_orders_for_manual_entry(
                ticker="NVDA",
                holdings=1000,
                last_transaction_price=120.50,
                current_price=125.30,
                sdn=8,
                profit_sharing_pct=50,
                bracket_seed=100.0,
            )
        )

        # Quantities should be the same
        self.assertEqual(qty_buy_no_seed, qty_buy_with_seed)
        self.assertEqual(qty_sell_no_seed, qty_sell_with_seed)

    def test_bracket_seed_large_distance(self):
        """Test bracket seed with large distance between seed and last price."""
        # Use seed far from last price to test large bracket calculations
        buy_price, buy_qty, sell_price, sell_qty = calculate_orders_for_manual_entry(
            ticker="TEST",
            holdings=1000,
            last_transaction_price=100.0,
            current_price=100.0,
            sdn=8,
            profit_sharing_pct=50,
            bracket_seed=1.0,
        )

        # For sd8, rebalance_size = 2^(1/8) - 1 ≈ 0.090508
        r = (2.0 ** (1.0 / 8)) - 1.0

        # With seed=1.0, brackets should be 1.0 * (1+r)^n
        # For last_price=100, find n such that 1.0 * (1+r)^n ≈ 100

        n = round(math.log(100.0) / math.log(1 + r))

        # Buy should be one bracket down: (1+r)^(n-1)
        expected_buy = 1.0 * (1 + r) ** (n - 1)
        # Sell should be one bracket up: (1+r)^(n+1)
        expected_sell = 1.0 * (1 + r) ** (n + 1)

        # Allow small floating point tolerance
        self.assertAlmostEqual(buy_price, expected_buy, places=2)
        self.assertAlmostEqual(sell_price, expected_sell, places=2)

        # Quantities should still be reasonable
        self.assertGreater(buy_qty, 0)
        self.assertGreater(sell_qty, 0)
