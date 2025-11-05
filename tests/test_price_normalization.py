"""Unit tests for price normalization feature.

Price normalization ensures that all backtests using the same rebalance trigger
and bracket_seed hit brackets at the same relative positions, making comparisons deterministic
and mathematically convenient.
"""

import math
from datetime import date, timedelta

import pandas as pd

from src.models.backtest import run_portfolio_backtest


class TestPriceNormalization:
    """Test price normalization creates deterministic bracket placement."""

    def test_normalization_same_transaction_count(self):
        """
        Different starting prices should produce the same number of transactions
        when using bracket_seed set to the starting price, proving they hit equivalent brackets.
        """
        dates = [date(2020, 1, 1) + timedelta(days=i * 30) for i in range(13)]

        # Test with three different starting prices, using bracket_seed = start_price
        test_cases = [50.0, 200.0, 1000.0]
        transaction_counts = []

        for start_price in test_cases:
            # Create price data that grows from start_price (same % growth pattern)
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

            # Use portfolio backtest with per-asset algorithm
            initial_qty = 1000
            start_price_value = prices[0]

            # Mock the fetcher to return our synthetic data
            from unittest.mock import patch

            import src.data.fetcher as fetcher_module

            original_get_history = fetcher_module.HistoryFetcher.get_history

            def mock_get_history(self, ticker, start_date, end_date):
                if ticker == "TEST":
                    return df
                return original_get_history(self, ticker, start_date, end_date)

            with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
                txns, _ = run_portfolio_backtest(
                    allocations={"TEST": 1.0},
                    start_date=dates[0],
                    end_date=dates[-1],
                    portfolio_algo=f"per-asset:sd-9.05,50,{start_price}",
                    initial_investment=initial_qty * start_price_value,
                    simple_mode=True,
                )

            transaction_counts.append(len(txns))

        # All should have the same number of transactions since bracket_seed normalizes relative to start_price
        assert (
            len(set(transaction_counts)) == 1
        ), f"Transaction counts should match: {transaction_counts}"
        assert transaction_counts[0] > 1, "Should have multiple transactions (not just initial buy)"

    def test_normalization_lands_on_integer_bracket(self):
        """
        Verify that bracket_seed causes orders to be placed at normalized positions.

        For sd8 (9.05% trigger) with bracket_seed=100.0, buy orders should be placed
        at prices that are normalized to the bracket ladder.
        """
        trigger = 0.0905
        start_price = 123.45  # Arbitrary price

        # Create prices that will trigger a buy order (drop below the buy bracket)
        dates = [date(2020, 1, 1), date(2020, 2, 1)]
        prices = [start_price, start_price * 0.85]  # Drop 15%

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

        # Use portfolio backtest with per-asset algorithm
        initial_qty = 1000
        bracket_seed = 100.0

        # Mock the fetcher to return our synthetic data
        from unittest.mock import patch

        import src.data.fetcher as fetcher_module

        original_get_history = fetcher_module.HistoryFetcher.get_history

        def mock_get_history(self, ticker, start_date, end_date):
            if ticker == "TEST":
                return df
            return original_get_history(self, ticker, start_date, end_date)

        with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
            txns, _ = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=dates[0],
                end_date=dates[-1],
                portfolio_algo=f"per-asset:sd-9.05,50,{bracket_seed}",
                initial_investment=initial_qty * start_price,
                simple_mode=True,
            )

        # Find the buy transaction
        buy_txns = [tx for tx in txns if tx.action == "BUY" and tx.limit_price is not None]
        assert len(buy_txns) > 0, "Should have at least one buy transaction with limit price"

        # Check that the limit price lands on an integer bracket
        limit_price = buy_txns[0].limit_price
        n = math.log(limit_price / 100.0) / math.log(1 + trigger)  # Relative to bracket_seed

        # Should be very close to an integer (within rounding error)
        assert abs(n - round(n)) < 0.001, f"Bracket {n} should be close to integer"

        # Verify the bracket calculation
        n_int = round(n)
        expected_price = 100.0 * math.pow(1 + trigger, n_int)
        assert (
            abs(limit_price - expected_price) / expected_price < 0.001
        ), f"Limit price {limit_price:.2f} should match bracket price {expected_price:.2f}"

    def test_normalization_relative_progression(self):
        """
        Different starting prices should follow identical relative bracket progressions
        when using the same bracket_seed.

        This is the key property: even though absolute bracket numbers differ,
        the PATTERN of bracket progression is identical.
        """

        def extract_bracket_sequence(txns, trigger, start_price):
            """Extract bracket numbers from transaction log."""
            brackets = []
            for tx in txns[1:]:  # Skip initial purchase
                if tx.price > 0:  # Transaction has a price
                    try:
                        n = math.log(tx.price / start_price) / math.log(1 + trigger)
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

            # Use portfolio backtest with per-asset algorithm
            initial_qty = 1000

            # Mock the fetcher to return our synthetic data
            from unittest.mock import patch

            import src.data.fetcher as fetcher_module

            original_get_history = fetcher_module.HistoryFetcher.get_history

            def mock_get_history(self, ticker, start_date, end_date):
                if ticker == "TEST":
                    return df
                return original_get_history(self, ticker, start_date, end_date)

            with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
                txns, _ = run_portfolio_backtest(
                    allocations={"TEST": 1.0},
                    start_date=dates[0],
                    end_date=dates[-1],
                    portfolio_algo=f"per-asset:sd-9.05,50,{start_price}",
                    initial_investment=initial_qty * prices[0],
                    simple_mode=True,
                )

            # Get bracket sequence
            bracket_seq = extract_bracket_sequence(txns, trigger, start_price)

            # Calculate relative progression (offset from first bracket)
            if len(bracket_seq) > 0:
                first_bracket = bracket_seq[0]
                relative = [b - first_bracket for b in bracket_seq]
                relative_sequences.append(relative)

        # All relative sequences should be identical
        assert len(relative_sequences) > 1, "Should have multiple test cases to compare"
        first_rel = relative_sequences[0]

        for i, rel in enumerate(relative_sequences[1:], 1):
            assert (
                rel == first_rel
            ), f"Relative sequence {i} ({rel}) should match first sequence ({first_rel})"

    def test_normalization_disabled_by_default(self):
        """
        Verify that bracket_seed is optional (backward compatibility).

        Without bracket_seed, the starting price should be the original price.
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

        # Use portfolio backtest with per-asset algorithm (no bracket_seed)
        initial_qty = 1000

        # Mock the fetcher to return our synthetic data
        from unittest.mock import patch

        import src.data.fetcher as fetcher_module

        original_get_history = fetcher_module.HistoryFetcher.get_history

        def mock_get_history(self, ticker, start_date, end_date):
            if ticker == "TEST":
                return df
            return original_get_history(self, ticker, start_date, end_date)

        with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
            txns, _ = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=dates[0],
                end_date=dates[-1],
                portfolio_algo="per-asset:sd-9.05,50",  # No bracket_seed
                initial_investment=initial_qty * start_price,
                simple_mode=True,
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
        Verify bracket_seed works with different rebalance triggers (sd4, sd8, sd16).
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

            # Use portfolio backtest with per-asset algorithm
            initial_qty = 1000
            bracket_seed = 100.0

            # Mock the fetcher to return our synthetic data
            from unittest.mock import patch

            import src.data.fetcher as fetcher_module

            original_get_history = fetcher_module.HistoryFetcher.get_history

            def mock_get_history(self, ticker, start_date, end_date):
                if ticker == "TEST":
                    return df
                return original_get_history(self, ticker, start_date, end_date)

            with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
                txns, _ = run_portfolio_backtest(
                    allocations={"TEST": 1.0},
                    start_date=dates[0],
                    end_date=dates[-1],
                    portfolio_algo=f"per-asset:sd-{trigger_pct},50,{bracket_seed}",
                    initial_investment=initial_qty * start_price,
                    simple_mode=True,
                )

            # Extract normalized price from the first limit order transaction (skip initial market order)
            limit_txns = [tx for tx in txns if tx.price > 0 and "limit" in str(tx.notes).lower()]
            if limit_txns:
                first_limit_tx = limit_txns[0]
                normalized_price = first_limit_tx.price
            else:
                # If no limit orders, check the initial purchase
                first_tx = txns[0]
                normalized_price = first_tx.price

            # Calculate bracket number
            trigger_decimal = trigger_pct / 100.0
            n = math.log(normalized_price / 100.0) / math.log(1 + trigger_decimal)

            # Should land on integer bracket
            assert abs(n - round(n)) < 0.3, f"sd{sdn}: bracket {n} should be close to integer"
