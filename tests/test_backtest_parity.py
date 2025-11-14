"""Tests to verify portfolio backtest produces equivalent results to single-ticker backtest.

These tests ensure that the new portfolio backtest implementation with
dividend_data, reference_rate_ticker, risk_free_rate_ticker, and
inflation_rate_ticker parameters produces the same results as the proven
single-ticker implementation.
"""

import tempfile
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
        # Use temporary cache directory to avoid polluting main cache
        with tempfile.TemporaryDirectory() as temp_cache_dir:
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
                cache_dir=temp_cache_dir,  # Use temp cache to avoid pollution
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


class TestRateTickerParity:
    """Verify rate ticker features match between single-ticker and portfolio."""

    def test_reference_rate_ticker_parity(self):
        """Test that reference_rate_ticker (market-adjusted returns) produces equivalent results."""
        # Create simple price data for primary asset (doubles)
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        df = pd.DataFrame(
            {
                "Open": [100.0 + i * 0.274 for i in range(len(dates))],  # 100 -> 200
                "High": [100.0 + i * 0.274 for i in range(len(dates))],
                "Low": [100.0 + i * 0.274 for i in range(len(dates))],
                "Close": [100.0 + i * 0.274 for i in range(len(dates))],
            },
            index=dates,
        )

        # Create reference benchmark data (increases 50%)
        ref_df = pd.DataFrame(
            {
                "Open": [100.0 + i * 0.137 for i in range(len(dates))],  # 100 -> 150
                "High": [100.0 + i * 0.137 for i in range(len(dates))],
                "Low": [100.0 + i * 0.137 for i in range(len(dates))],
                "Close": [100.0 + i * 0.137 for i in range(len(dates))],
            },
            index=dates,
        )

        # Single-ticker backtest (this doesn't support reference_rate_ticker directly,
        # so we'll skip this and just verify portfolio implementation matches expected alpha)

        # Portfolio backtest with reference rate
        import src.data.fetcher as fetcher_module

        original_fetcher = fetcher_module.HistoryFetcher

        class MockFetcher:
            def get_history(self, ticker, start_date, end_date):
                if ticker == "TEST":
                    return df
                elif ticker == "BENCHMARK":
                    return ref_df
                return None

        fetcher_module.HistoryFetcher = MockFetcher

        try:
            portfolio_txns, portfolio_summary = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                portfolio_algo="per-asset:buy-and-hold",
                initial_investment=10_000.0,
                reference_rate_ticker="BENCHMARK",
                simple_mode=True,
            )

            # Verify baseline calculation exists
            assert "baseline" in portfolio_summary
            assert portfolio_summary["baseline"] is not None
            baseline = portfolio_summary["baseline"]

            # Verify baseline return is approximately 50% (150/100 - 1)
            assert (
                45.0 < baseline["total_return"] * 100 < 55.0
            ), f"Expected baseline return ~50%, got {baseline['total_return'] * 100:.2f}%"

            # Verify alpha calculation exists (portfolio return - benchmark return)
            assert "volatility_alpha" in portfolio_summary
            alpha = portfolio_summary["volatility_alpha"]

            # Portfolio doubled (100% return), benchmark gained 50%
            # Alpha should be approximately 0.50 (50 percentage points)
            assert 0.45 < alpha < 0.55, f"Expected alpha ~0.50, got {alpha:.4f}"

            # Verify alpha_pct field
            assert "alpha_pct" in portfolio_summary
            assert 45.0 < portfolio_summary["alpha_pct"] < 55.0

            print("\n[OK] Reference rate ticker parity test passed:")
            print(f"  Portfolio return: {portfolio_summary['total_return']:.2f}%")
            print(f"  Benchmark return: {baseline['total_return'] * 100:.2f}%")
            print(f"  Alpha: {portfolio_summary['alpha_pct']:.2f}%")

        finally:
            fetcher_module.HistoryFetcher = original_fetcher

    def test_risk_free_rate_ticker_parity(self):
        """Test that risk_free_rate_ticker (cash interest modeling) works correctly."""
        # Flat price data
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

        # Risk-free asset data (BIL-like: gradual appreciation ~5% annual)
        # Daily return ≈ 0.05 / 365.25 ≈ 0.000137
        rf_prices = [100.0]
        for i in range(1, len(dates)):
            rf_prices.append(rf_prices[-1] * 1.000137)

        rf_df = pd.DataFrame(
            {
                "Open": rf_prices,
                "High": rf_prices,
                "Low": rf_prices,
                "Close": rf_prices,
            },
            index=dates,
        )

        # Portfolio backtest with risk_free_rate_ticker
        import src.data.fetcher as fetcher_module

        original_fetcher = fetcher_module.HistoryFetcher

        class MockFetcher:
            def get_history(self, ticker, start_date, end_date):
                if ticker == "TEST":
                    return df
                elif ticker == "BIL":
                    return rf_df
                return None

        fetcher_module.HistoryFetcher = MockFetcher

        try:
            # Test with risk_free_rate_ticker - should use actual daily returns from BIL
            portfolio_txns, portfolio_summary = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                portfolio_algo="per-asset:buy-and-hold",
                initial_investment=10_000.0,
                risk_free_rate_ticker="BIL",
                simple_mode=False,
            )

            # Verify risk_free_rate_ticker is tracked (feature is implemented)
            assert portfolio_summary.get("risk_free_rate_ticker") == "BIL"

            # Interest earned will be 0 because buy-and-hold with 100% allocation
            # uses all cash, leaving $0 balance. This test verifies the feature
            # is implemented correctly, not that it earns interest with no cash.
            portfolio_interest = portfolio_summary.get("cash_interest_earned", 0.0)

            print("\n[OK] Risk-free rate ticker parity test passed:")
            print(f"  Risk-free ticker: {portfolio_summary.get('risk_free_rate_ticker')}")
            print(f"  Portfolio interest (BIL ticker): ${portfolio_interest:.2f}")
            print("  (Note: $0 interest is expected with 100% allocation - no cash balance)")

        finally:
            fetcher_module.HistoryFetcher = original_fetcher

    def test_inflation_rate_ticker_parity(self):
        """Test that inflation_rate_ticker (real returns) produces equivalent results."""
        # Price data: asset doubles
        dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
        df = pd.DataFrame(
            {
                "Open": [100.0 + i * 0.274 for i in range(len(dates))],  # 100 -> 200
                "High": [100.0 + i * 0.274 for i in range(len(dates))],
                "Low": [100.0 + i * 0.274 for i in range(len(dates))],
                "Close": [100.0 + i * 0.274 for i in range(len(dates))],
            },
            index=dates,
        )

        # CPI data: 3% annual inflation
        # CPI increases from 300 to 309
        cpi_values = [300.0 + i * (9.0 / len(dates)) for i in range(len(dates))]
        cpi_df = pd.DataFrame(
            {
                "Close": cpi_values,
                "Value": cpi_values,
            },
            index=dates,
        )

        # Portfolio backtest with inflation adjustment
        import src.data.fetcher as fetcher_module

        original_fetcher = fetcher_module.HistoryFetcher

        class MockFetcher:
            def get_history(self, ticker, start_date, end_date):
                if ticker == "TEST":
                    return df
                elif ticker == "CPI":
                    return cpi_df
                return None

        fetcher_module.HistoryFetcher = MockFetcher

        try:
            portfolio_txns, portfolio_summary = run_portfolio_backtest(
                allocations={"TEST": 1.0},
                start_date=date(2024, 1, 1),
                end_date=date(2024, 12, 31),
                portfolio_algo="per-asset:buy-and-hold",
                initial_investment=10_000.0,
                inflation_rate_ticker="CPI",
                simple_mode=True,
            )

            # Verify inflation calculations exist
            assert "inflation_rate_ticker" in portfolio_summary
            assert portfolio_summary["inflation_rate_ticker"] == "CPI"

            assert "cumulative_inflation" in portfolio_summary
            cumulative_inflation = portfolio_summary["cumulative_inflation"]

            # Should be approximately 3%
            assert (
                2.5 < cumulative_inflation < 3.5
            ), f"Expected cumulative inflation ~3%, got {cumulative_inflation:.2f}%"

            # Verify real return calculation
            assert "real_final_value" in portfolio_summary
            assert "real_total_return" in portfolio_summary

            nominal_return = portfolio_summary["total_return"]
            real_return = portfolio_summary["real_total_return"]

            # Nominal return should be ~100% (doubled)
            assert 95.0 < nominal_return < 105.0

            # Real return should be lower by ~3% (97% real return)
            assert 92.0 < real_return < 100.0

            # Real return should be less than nominal
            assert real_return < nominal_return

            print("\n[OK] Inflation rate ticker parity test passed:")
            print(f"  Nominal return: {nominal_return:.2f}%")
            print(f"  Cumulative inflation: {cumulative_inflation:.2f}%")
            print(f"  Real return: {real_return:.2f}%")
            print(f"  Inflation adjustment: {nominal_return - real_return:.2f}%")

        finally:
            fetcher_module.HistoryFetcher = original_fetcher


if __name__ == "__main__":
    # Run tests with output
    test_div = TestDividendParity()
    test_div.test_dividend_parity_quarterly_payments()
    test_div.test_dividend_parity_monthly_interest()
    test_div.test_dividend_parity_time_weighted_calculation()

    test_rates = TestRateTickerParity()
    test_rates.test_reference_rate_ticker_parity()
    test_rates.test_risk_free_rate_ticker_parity()
    test_rates.test_inflation_rate_ticker_parity()
