"""Tests to verify portfolio backtest produces equivalent results to single-ticker backtest.

These tests ensure that the new portfolio backtest implementation with
dividend_data, reference_rate_ticker, risk_free_rate_ticker, and
inflation_rate_ticker parameters produces the same results as the proven
single-ticker implementation.
"""

from datetime import date

import pandas as pd

from src.algorithms import BuyAndHoldAlgorithm
from src.models.backtest import run_algorithm_backtest, run_portfolio_backtest


class TestDividendParity:
    """Verify dividend calculations match between single-ticker and portfolio."""

    def test_dividend_parity_quarterly_payments(self):
        """Test that quarterly dividend payments produce equivalent results."""
        # Create simple price data (flat prices)
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        df = pd.DataFrame(
            {
                "Open": [100.0] * len(dates),
                "High": [100.0] * len(dates),
                "Low": [100.0] * len(dates),
                "Close": [100.0] * len(dates),
            },
            index=dates,
        )

        # Create dividend data: 4 quarterly payments of $0.25 each
        div_dates = ["2024-02-09", "2024-05-10", "2024-08-12", "2024-11-08"]
        div_series = pd.Series(
            [0.25, 0.25, 0.25, 0.25],
            index=pd.to_datetime(div_dates),
        )

        # Run single-ticker backtest
        algo1 = BuyAndHoldAlgorithm()
        single_txns, single_summary = run_algorithm_backtest(
            df=df,
            ticker="TEST",
            initial_qty=100,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            algo=algo1,
            dividend_series=div_series,
            simple_mode=True,
        )

        # Run portfolio backtest with equivalent setup
        # Need to use mock provider to inject DataFrame
        import src.data.fetcher as fetcher_module

        original_fetcher = fetcher_module.HistoryFetcher

        class MockFetcher:
            def get_history(self, ticker, start_date, end_date):
                return df

        fetcher_module.HistoryFetcher = MockFetcher

        try:
            portfolio_txns, portfolio_summary = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                portfolio_algo="per-asset:buy-and-hold",
                initial_investment=10_000.0,  # 100 shares × $100 = $10,000
                dividend_data={"TEST": div_series},
                simple_mode=True,
            )

            # Verify dividend metrics match
            assert single_summary["dividend_payment_count"] == 4
            assert portfolio_summary["dividend_payment_count_by_asset"]["TEST"] == 4

            # Total dividends should match within small tolerance
            single_divs = single_summary["total_dividends"]
            portfolio_divs = portfolio_summary["total_dividends"]
            assert abs(single_divs - portfolio_divs) < 1.0, (
                f"Dividend totals don't match: single={single_divs:.2f}, "
                f"portfolio={portfolio_divs:.2f}"
            )

            # Verify dividend transactions match
            single_div_txns = [tx for tx in single_txns if tx.action == "DIVIDEND"]
            portfolio_div_txns = [tx for tx in portfolio_txns if tx.action == "DIVIDEND"]
            assert len(single_div_txns) == len(portfolio_div_txns) == 4

            print("\n[OK] Dividend parity test passed:")
            print(f"  Single-ticker dividends: ${single_divs:.2f}")
            print(f"  Portfolio dividends: ${portfolio_divs:.2f}")
            print(f"  Difference: ${abs(single_divs - portfolio_divs):.2f}")

        finally:
            fetcher_module.HistoryFetcher = original_fetcher

    def test_dividend_parity_monthly_interest(self):
        """Test that monthly interest payments (like BIL) produce equivalent results."""
        # Flat price data for 1 year
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        df = pd.DataFrame(
            {
                "Open": [100.0] * len(dates),
                "High": [100.0] * len(dates),
                "Low": [100.0] * len(dates),
                "Close": [100.0] * len(dates),
            },
            index=dates,
        )

        # 12 monthly interest payments
        monthly_payment = 0.375
        div_dates = [
            "2024-01-05",
            "2024-02-05",
            "2024-03-05",
            "2024-04-05",
            "2024-05-03",
            "2024-06-05",
            "2024-07-05",
            "2024-08-05",
            "2024-09-05",
            "2024-10-04",
            "2024-11-05",
            "2024-12-05",
        ]
        div_series = pd.Series([monthly_payment] * 12, index=pd.to_datetime(div_dates))

        # Single-ticker backtest
        algo1 = BuyAndHoldAlgorithm()
        single_txns, single_summary = run_algorithm_backtest(
            df=df,
            ticker="BIL",
            initial_qty=100,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
            algo=algo1,
            dividend_series=div_series,
            simple_mode=True,
        )

        # Portfolio backtest
        import src.data.fetcher as fetcher_module

        original_fetcher = fetcher_module.HistoryFetcher

        class MockFetcher:
            def get_history(self, ticker, start_date, end_date):
                return df

        fetcher_module.HistoryFetcher = MockFetcher

        try:
            portfolio_txns, portfolio_summary = run_portfolio_backtest(
                allocations={"BIL": 1.0},
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                portfolio_algo="per-asset:buy-and-hold",
                initial_investment=10_000.0,
                dividend_data={"BIL": div_series},
                simple_mode=True,
            )

            # Verify counts match
            assert single_summary["dividend_payment_count"] == 12
            assert portfolio_summary["dividend_payment_count_by_asset"]["BIL"] == 12

            # Verify totals match within tolerance
            single_divs = single_summary["total_dividends"]
            portfolio_divs = portfolio_summary["total_dividends"]
            assert abs(single_divs - portfolio_divs) < 1.0, (
                f"Monthly interest totals don't match: single={single_divs:.2f}, "
                f"portfolio={portfolio_divs:.2f}"
            )

            print("\n[OK] Monthly interest parity test passed:")
            print(f"  Single-ticker total: ${single_divs:.2f}")
            print(f"  Portfolio total: ${portfolio_divs:.2f}")
            print(f"  Difference: ${abs(single_divs - portfolio_divs):.2f}")

        finally:
            fetcher_module.HistoryFetcher = original_fetcher

    def test_dividend_parity_time_weighted_calculation(self):
        """Verify time-weighted averaging produces identical results."""
        # Flat price data
        dates = pd.date_range(start="2024-01-01", end="2024-03-31", freq="D")
        df = pd.DataFrame(
            {
                "Open": [100.0] * len(dates),
                "High": [100.0] * len(dates),
                "Low": [100.0] * len(dates),
                "Close": [100.0] * len(dates),
            },
            index=dates,
        )

        # Single dividend payment
        div_series = pd.Series([1.0], index=pd.to_datetime(["2024-02-15"]))

        # Single-ticker: 200 shares
        algo1 = BuyAndHoldAlgorithm()
        single_txns, single_summary = run_algorithm_backtest(
            df=df,
            ticker="TEST",
            initial_qty=200,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 3, 31),
            algo=algo1,
            dividend_series=div_series,
            simple_mode=True,
        )

        # Portfolio: equivalent to 200 shares
        import src.data.fetcher as fetcher_module

        original_fetcher = fetcher_module.HistoryFetcher

        class MockFetcher:
            def get_history(self, ticker, start_date, end_date):
                return df

        fetcher_module.HistoryFetcher = MockFetcher

        try:
            portfolio_txns, portfolio_summary = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=date(2024, 1, 1),
                end_date=date(2024, 3, 31),
                portfolio_algo="per-asset:buy-and-hold",
                initial_investment=20_000.0,  # 200 shares × $100
                dividend_data={"TEST": div_series},
                simple_mode=True,
            )

            # Both should use same time-weighted calculation
            # Purchase 2024-01-01, dividend 2024-02-15
            # 90-day lookback starts 2023-11-17 (before purchase)
            # Only held for 45 days = 200 × 45/90 = 100 shares avg
            # Dividend: 100 shares × $1.00 = $100
            single_divs = single_summary["total_dividends"]
            portfolio_divs = portfolio_summary["total_dividends"]

            assert abs(single_divs - portfolio_divs) < 0.10, (
                f"Time-weighted dividends don't match: single={single_divs:.2f}, "
                f"portfolio={portfolio_divs:.2f}"
            )

            # Verify both are approximately $100 (time-weighted)
            assert (
                95.0 < single_divs < 105.0
            ), f"Single-ticker dividend should be ~$100, got ${single_divs:.2f}"
            assert (
                95.0 < portfolio_divs < 105.0
            ), f"Portfolio dividend should be ~$100, got ${portfolio_divs:.2f}"

            print("\n[OK] Time-weighted calculation parity test passed:")
            print(f"  Single-ticker: ${single_divs:.2f}")
            print(f"  Portfolio: ${portfolio_divs:.2f}")
            print("  Expected: ~$100 (time-weighted from 200 shares)")

        finally:
            fetcher_module.HistoryFetcher = original_fetcher


if __name__ == "__main__":
    # Run tests with output
    test = TestDividendParity()
    test.test_dividend_parity_quarterly_payments()
    test.test_dividend_parity_monthly_interest()
    test.test_dividend_parity_time_weighted_calculation()
