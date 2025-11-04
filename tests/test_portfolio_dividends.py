"""Tests for dividend/interest payment support in portfolio backtest.

This module verifies that the portfolio backtest correctly handles dividend
payments using time-weighted average holdings calculations.
"""

from datetime import date

import pandas as pd

from src.models.backtest import run_portfolio_backtest


def test_portfolio_dividend_basic():
    """Test basic dividend payment in portfolio backtest."""
    # Create simple price data (flat prices for predictability)
    dates = pd.date_range("2023-01-01", "2023-03-31", freq="D")
    price_df = pd.DataFrame({"Close": [100.0] * len(dates)}, index=dates)

    # Create dividend series (one payment on Feb 15)
    div_dates = pd.DatetimeIndex(["2023-02-15"])
    dividend_series = pd.Series([2.50], index=div_dates)  # $2.50 per share

    # Mock the fetcher to return our test data
    import src.data.fetcher as fetcher_module

    original_fetcher = fetcher_module.HistoryFetcher

    class MockFetcher:
        def get_history(self, ticker, start_date, end_date):
            return price_df

    fetcher_module.HistoryFetcher = MockFetcher

    try:
        # Run portfolio backtest with dividends
        txns, summary = run_portfolio_backtest(
            allocations={"TEST": 1.0},
            start_date=date(2023, 1, 1),
            end_date=date(2023, 3, 31),
            portfolio_algo="per-asset:buy-and-hold",
            initial_investment=10_000.0,
            dividend_data={"TEST": dividend_series},
        )

        # Verify dividend transaction exists
        div_txns = [tx for tx in txns if tx.action == "DIVIDEND"]
        assert len(div_txns) == 1, f"Expected 1 dividend transaction, got {len(div_txns)}"

        div_tx = div_txns[0]
        assert div_tx.ticker == "TEST"
        assert div_tx.price == 2.50

        # Verify dividend is in summary
        assert "total_dividends" in summary
        assert summary["total_dividends"] > 0

        # With 100 shares held from Jan 1, the 90-day lookback from Feb 15 includes
        # only 45 days of holdings (rest of period has zero holdings).
        # Time-weighted average: (100 shares × 45 days) / 90 days = 50 shares
        # Dividend: 50 shares × $2.50 = $125
        expected_dividend_approx = 125.0
        assert abs(summary["total_dividends"] - expected_dividend_approx) < 5.0

    finally:
        # Restore original fetcher
        fetcher_module.HistoryFetcher = original_fetcher


def test_portfolio_dividend_multi_asset():
    """Test dividend payments across multiple assets."""
    dates = pd.date_range("2023-01-01", "2023-06-30", freq="D")
    price_df = pd.DataFrame({"Close": [100.0] * len(dates)}, index=dates)

    # Asset 1: quarterly dividends
    div1_dates = pd.DatetimeIndex(["2023-03-15", "2023-06-15"])
    div1_series = pd.Series([1.50, 1.50], index=div1_dates)

    # Asset 2: monthly interest (like BIL)
    div2_dates = pd.date_range("2023-01-31", "2023-06-30", freq="ME")
    div2_series = pd.Series([0.40] * len(div2_dates), index=div2_dates)

    import src.data.fetcher as fetcher_module

    original_fetcher = fetcher_module.HistoryFetcher

    class MockFetcher:
        def get_history(self, ticker, start_date, end_date):
            return price_df

    fetcher_module.HistoryFetcher = MockFetcher

    try:
        txns, summary = run_portfolio_backtest(
            allocations={"ASSET1": 0.6, "ASSET2": 0.4},
            start_date=date(2023, 1, 1),
            end_date=date(2023, 6, 30),
            portfolio_algo="per-asset:buy-and-hold",
            initial_investment=10_000.0,
            dividend_data={"ASSET1": div1_series, "ASSET2": div2_series},
        )

        # Verify dividend transactions
        div_txns = [tx for tx in txns if tx.action == "DIVIDEND"]
        asset1_divs = [tx for tx in div_txns if tx.ticker == "ASSET1"]
        asset2_divs = [tx for tx in div_txns if tx.ticker == "ASSET2"]

        assert len(asset1_divs) == 2, f"Expected 2 ASSET1 dividends, got {len(asset1_divs)}"
        assert len(asset2_divs) == 6, f"Expected 6 ASSET2 dividends, got {len(asset2_divs)}"

        # Verify per-asset totals in summary
        assert "total_dividends_by_asset" in summary
        assert "ASSET1" in summary["total_dividends_by_asset"]
        assert "ASSET2" in summary["total_dividends_by_asset"]

        # ASSET1: Time-weighted calculation applies (first payment on Mar 15, second on Jun 15)
        # First payment: ~60 shares × (73 days held / 90 days) × $1.50 ≈ $73
        # Second payment: ~60 shares × 90/90 × $1.50 = $90
        # Total: ~$163
        assert summary["total_dividends_by_asset"]["ASSET1"] > 140

        # ASSET2: Similar time-weighting applies to each monthly payment
        # Approximate total across 6 payments: ~$50
        assert summary["total_dividends_by_asset"]["ASSET2"] > 40

        # Total dividends: ~$200+
        total = summary["total_dividends"]
        assert total > 180, f"Expected total dividends > 180, got {total}"

    finally:
        fetcher_module.HistoryFetcher = original_fetcher


def test_portfolio_no_dividends_when_not_provided():
    """Test that portfolio works correctly when no dividend data provided."""
    dates = pd.date_range("2023-01-01", "2023-03-31", freq="D")
    price_df = pd.DataFrame({"Close": [100.0] * len(dates)}, index=dates)

    import src.data.fetcher as fetcher_module

    original_fetcher = fetcher_module.HistoryFetcher

    class MockFetcher:
        def get_history(self, ticker, start_date, end_date):
            return price_df

    fetcher_module.HistoryFetcher = MockFetcher

    try:
        txns, summary = run_portfolio_backtest(
            allocations={"TEST": 1.0},
            start_date=date(2023, 1, 1),
            end_date=date(2023, 3, 31),
            portfolio_algo="per-asset:buy-and-hold",
            initial_investment=10_000.0,
            # No dividend_data parameter
        )

        # Verify no dividend transactions
        div_txns = [tx for tx in txns if tx.action == "DIVIDEND"]
        assert len(div_txns) == 0

        # Verify dividend tracking exists but is zero
        assert summary["total_dividends"] == 0.0

    finally:
        fetcher_module.HistoryFetcher = original_fetcher
