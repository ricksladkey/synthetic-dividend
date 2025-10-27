"""Unit tests for price normalization feature.

Price normalization ensures that all backtests using the same rebalance trigger
hit brackets at the same relative positions, making comparisons deterministic
and mathematically convenient.
"""

import math
import pandas as pd
from datetime import date, timedelta

from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest


class TestPriceNormalization:
    """Test price normalization creates deterministic bracket placement."""

    def test_normalization_same_transaction_count(self):
        """
        Different starting prices should produce the same number of transactions
        when normalized, proving they hit equivalent brackets.
        """
        dates = [date(2020, 1, 1) + timedelta(days=i * 30) for i in range(13)]

        # Test with three different starting prices
        test_cases = [50.0, 200.0, 1000.0]
        transaction_counts = []

        for start_price in test_cases:
            # Create price data that doubles (same % growth pattern)
            prices = [start_price * (1 + i / 12) for i in range(13)]

            df = pd.DataFrame(
                {
                    "Date": dates,
                    "Open": prices,
                    "High": [p * 1.01 for p in prices],
                    "Low": [p * 0.99 for p in prices],
                    "Close": prices,
                }
            )
            df.set_index("Date", inplace=True)

            algo = SyntheticDividendAlgorithm(
                rebalance_size=9.05/100.0, profit_sharing=50.0/100.0, buyback_enabled=True
            )

            txns, _ = run_algorithm_backtest(
                df=df,
                ticker="TEST",
                initial_qty=1000,
                start_date=dates[0],
                end_date=dates[-1],
                algo=algo,
                simple_mode=True,
                normalize_prices=True,
            )

            transaction_counts.append(len(txns))

        # All should have the same number of transactions
        assert (
            len(set(transaction_counts)) == 1
        ), f"Transaction counts should match: {transaction_counts}"
        assert (
            transaction_counts[0] > 1
        ), "Should have multiple transactions (not just initial buy)"

    def test_normalization_lands_on_integer_bracket(self):
        """
        Verify that normalized prices land exactly on integer bracket positions.

        For sd8 (9.05% trigger), brackets are at: 1.0 * (1.0905)^n where n is an integer.
        """
        trigger = 0.0905
        start_price = 123.45  # Arbitrary price

        dates = [date(2020, 1, 1) + timedelta(days=i * 30) for i in range(5)]
        prices = [start_price] * 5  # Flat prices

        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": prices,
                "Low": prices,
                "Close": prices,
            }
        )
        df.set_index("Date", inplace=True)

        algo = SyntheticDividendAlgorithm(
            rebalance_size=9.05/100.0, profit_sharing=50.0/100.0, buyback_enabled=True
        )

        txns, _ = run_algorithm_backtest(
            df=df,
            ticker="TEST",
            initial_qty=1000,
            start_date=dates[0],
            end_date=dates[-1],
            algo=algo,
            simple_mode=True,
            normalize_prices=True,
        )

        # Extract normalized price from first transaction
        # Transaction object has .price property
        first_tx = txns[0]
        normalized_price = first_tx.price

        # Calculate bracket number
        n = math.log(normalized_price) / math.log(1 + trigger)

        # Should be very close to an integer (within rounding error)
        assert abs(n - round(n)) < 0.001, f"Bracket {n} should be close to integer"

        # Verify the bracket calculation
        n_int = round(n)
        expected_price = math.pow(1 + trigger, n_int)
        assert (
            abs(normalized_price - expected_price) / expected_price < 0.001
        ), f"Normalized price {normalized_price:.2f} should match bracket price {expected_price:.2f}"

    def test_normalization_relative_progression(self):
        """
        Different starting prices should follow identical relative bracket progressions.

        This is the key property: even though absolute bracket numbers differ,
        the PATTERN of bracket progression is identical.
        """

        def extract_bracket_sequence(txns, trigger):
            """Extract bracket numbers from transaction log."""
            brackets = []
            for tx in txns[1:]:  # Skip initial purchase
                if tx.price > 0:  # Transaction has a price
                    try:
                        n = math.log(tx.price) / math.log(1 + trigger)
                        brackets.append(round(n))
                    except ValueError:
                        pass
            return brackets

        trigger = 0.0905
        dates = [date(2020, 1, 1) + timedelta(days=i * 30) for i in range(13)]

        # Test with different starting prices
        test_cases = [50.0, 200.0, 1000.0]
        relative_sequences = []

        for start_price in test_cases:
            prices = [start_price * (1 + i / 12) for i in range(13)]

            df = pd.DataFrame(
                {
                    "Date": dates,
                    "Open": prices,
                    "High": [p * 1.01 for p in prices],
                    "Low": [p * 0.99 for p in prices],
                    "Close": prices,
                }
            )
            df.set_index("Date", inplace=True)

            algo = SyntheticDividendAlgorithm(
                rebalance_size=9.05/100.0, profit_sharing=50.0/100.0, buyback_enabled=True
            )

            txns, _ = run_algorithm_backtest(
                df=df,
                ticker="TEST",
                initial_qty=1000,
                start_date=dates[0],
                end_date=dates[-1],
                algo=algo,
                simple_mode=True,
                normalize_prices=True,
            )

            # Get bracket sequence
            bracket_seq = extract_bracket_sequence(txns, trigger)

            # Calculate relative progression (offset from first bracket)
            if len(bracket_seq) > 0:
                first_bracket = bracket_seq[0]
                relative = [b - first_bracket for b in bracket_seq]
                relative_sequences.append(relative)

        # All relative sequences should be identical
        assert (
            len(relative_sequences) > 1
        ), "Should have multiple test cases to compare"
        first_rel = relative_sequences[0]

        for i, rel in enumerate(relative_sequences[1:], 1):
            assert (
                rel == first_rel
            ), f"Relative sequence {i} ({rel}) should match first sequence ({first_rel})"

    def test_normalization_disabled_by_default(self):
        """
        Verify that normalization is disabled by default (backward compatibility).

        Without normalization, the starting price should be the original price.
        """
        start_price = 123.45
        dates = [date(2020, 1, 1), date(2020, 2, 1)]
        prices = [start_price, start_price]

        df = pd.DataFrame(
            {
                "Date": dates,
                "Open": prices,
                "High": prices,
                "Low": prices,
                "Close": prices,
            }
        )
        df.set_index("Date", inplace=True)

        algo = SyntheticDividendAlgorithm(
            rebalance_size=9.05/100.0, profit_sharing=50.0/100.0, buyback_enabled=True
        )

        txns, _ = run_algorithm_backtest(
            df=df,
            ticker="TEST",
            initial_qty=1000,
            start_date=dates[0],
            end_date=dates[-1],
            algo=algo,
            simple_mode=True,
            # normalize_prices NOT specified (defaults to False)
        )

        # Extract price from first transaction
        first_tx = txns[0]
        actual_price = first_tx.price

        # Should be the original price (no normalization)
        assert (
            abs(actual_price - start_price) < 0.01
        ), f"Without normalization, price should be {start_price:.2f}, got {actual_price:.2f}"

    def test_normalization_with_different_triggers(self):
        """
        Verify normalization works with different rebalance triggers (sd4, sd8, sd16).
        """
        test_triggers = [
            (4, 18.9207),  # sd4
            (8, 9.05),  # sd8
            (16, 4.427),  # sd16
        ]

        start_price = 100.0
        dates = [date(2020, 1, 1), date(2020, 2, 1)]
        prices = [start_price, start_price * 1.1]

        for sdn, trigger_pct in test_triggers:
            df = pd.DataFrame(
                {
                    "Date": dates,
                    "Open": prices,
                    "High": prices,
                    "Low": prices,
                    "Close": prices,
                }
            )
            df.set_index("Date", inplace=True)

            algo = SyntheticDividendAlgorithm(
                rebalance_size=trigger_pct/100.0,
                profit_sharing=50.0/100.0,
                buyback_enabled=True,
            )

            txns, _ = run_algorithm_backtest(
                df=df,
                ticker="TEST",
                initial_qty=1000,
                start_date=dates[0],
                end_date=dates[-1],
                algo=algo,
                simple_mode=True,
                normalize_prices=True,
            )

            # Extract normalized price
            first_tx = txns[0]
            normalized_price = first_tx.price

            # Calculate bracket number
            trigger_decimal = trigger_pct / 100.0
            n = math.log(normalized_price) / math.log(1 + trigger_decimal)

            # Should land on integer bracket
            assert (
                abs(n - round(n)) < 0.001
            ), f"sd{sdn}: bracket {n} should be close to integer"
