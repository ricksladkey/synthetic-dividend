"""Tests for dividend/interest income tracking in backtests."""
from datetime import date

import pandas as pd
import pytest

from src.models.backtest import BuyAndHoldAlgorithm, run_algorithm_backtest


def test_dividend_income_credited_to_bank():
    """Test that dividend payments use time-weighted average holdings.
    
    This tests the mathematically correct (IRS-approved) dividend calculation
    that accounts for actual holding periods during the dividend accrual period.
    """
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

    # Run backtest with buy-and-hold: 100 shares
    algo = BuyAndHoldAlgorithm()
    transactions, summary = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo=algo,
        dividend_series=div_series,
        simple_mode=True,
    )

    # Verify dividend tracking
    assert summary["dividend_payment_count"] == 4, "Should have 4 dividend payments"
    
    # Time-weighted calculation:
    # Purchase: 2024-01-01, held 100 shares continuously
    # Div 1 (2024-02-09): 90-day lookback starts 2023-11-11 (before we owned shares!)
    #   → Only held for 39 days (Jan 1 to Feb 9) = 100 × 39/90 = 43.33 shares avg
    # Div 2 (2024-05-10): 90-day lookback starts 2024-02-09 (we owned shares!)
    #   → Held full 91 days = 100 shares avg (lookback overlaps with div 1)
    # Div 3 (2024-08-12): 90-day lookback starts 2024-05-14
    #   → Held full 91 days = 100 shares avg
    # Div 4 (2024-11-08): 90-day lookback starts 2024-08-10
    #   → Held full 91 days = 100 shares avg
    
    # This is CORRECT: you only get dividends for the days you held shares!
    # The "simple" snapshot approach was mathematically wrong.
    
    # Actual time-weighted total should be less than snapshot (100 × 4 × 0.25 = 100)
    assert summary["total_dividends"] < 100.0, "Time-weighted should be less than snapshot"
    assert summary["total_dividends"] > 80.0, "But should still be substantial (held most of period)"

    # Verify bank balance increased by dividend amount
    # With buy-and-hold, bank should = total dividends (no other transactions)
    assert summary["bank"] == summary["total_dividends"], "Bank should equal total dividends received"

    # Verify dividends were added to total return
    assert summary["total"] > summary["end_value"], "Total should include bank (dividends)"

    # Verify transactions show dividend payments
    div_transactions = [t for t in transactions if t.action == "DIVIDEND"]
    assert len(div_transactions) == 4, "Should have 4 dividend transaction logs"


def test_dividend_income_with_different_share_counts():
    """Test that time-weighted dividend calculation accounts for holding period."""
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

    # Single dividend payment: $1.00 per share
    div_series = pd.Series([1.0], index=pd.to_datetime(["2024-02-15"]))

    # Test with 50 shares
    algo1 = BuyAndHoldAlgorithm()
    _, summary1 = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=50,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        algo=algo1,
        dividend_series=div_series,
        simple_mode=True,
    )
    # Purchase 2024-01-01, dividend 2024-02-15
    # 90-day lookback starts 2023-11-17 (before purchase)
    # Only held for 45 days (Jan 1 to Feb 15) = 50 × 45/90 = 25 shares avg
    assert summary1["total_dividends"] < 50.0, "Time-weighted should be less than 50 shares × $1"
    assert summary1["total_dividends"] > 20.0, "But should be ~half of full amount"

    # Test with 200 shares
    algo2 = BuyAndHoldAlgorithm()
    _, summary2 = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=200,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 3, 31),
        algo=algo2,
        dividend_series=div_series,
        simple_mode=True,
    )
    # Same timeline: 200 × 45/90 = 100 shares avg
    assert summary2["total_dividends"] < 200.0, "Time-weighted should be less than 200 shares × $1"
    assert summary2["total_dividends"] > 80.0, "But should be ~half of full amount"
    
    # Verify scaling: 200 shares should get 4x dividends vs 50 shares
    assert abs(summary2["total_dividends"] / summary1["total_dividends"] - 4.0) < 0.01, \
        "Dividend should scale linearly with holdings"


def test_no_dividends_when_series_empty():
    """Test that backtest works correctly when no dividend data provided."""
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

    algo = BuyAndHoldAlgorithm()
    _, summary = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo=algo,
        dividend_series=None,  # No dividends
        simple_mode=True,
    )

    assert summary["total_dividends"] == 0.0, "Should have zero dividends"
    assert summary["dividend_payment_count"] == 0, "Should have zero dividend payments"
    assert summary["bank"] == 0.0, "Bank should be zero with no dividends and no trades"


def test_monthly_interest_payments_like_bil():
    """Test monthly interest payments with time-weighted averaging."""
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

    # 12 monthly interest payments (simulating BIL)
    # Approximate monthly payment for ~4.5% annual yield
    monthly_payment = 0.375  # roughly 4.5% / 12
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

    # 100 shares of money market ETF
    algo = BuyAndHoldAlgorithm()
    _, summary = run_algorithm_backtest(
        df=df,
        ticker="BIL",
        initial_qty=100,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo=algo,
        dividend_series=div_series,
        simple_mode=True,
    )

    assert summary["dividend_payment_count"] == 12, "Should have 12 monthly payments"
    
    # Time-weighted: First payment (Jan 5) only had shares for 4 days of 90-day period
    # Later payments will be closer to full amount as holding period increases
    # Total should be less than snapshot (12 × 0.375 × 100 = 450) but still substantial
    snapshot_total = 12 * monthly_payment * 100
    assert summary["total_dividends"] < snapshot_total, \
        f"Time-weighted should be less than snapshot ${snapshot_total}"
    assert summary["total_dividends"] > 0.75 * snapshot_total, \
        f"But should be >75% of snapshot (held most of the year)"

    # Bank balance should equal total dividends (buy-and-hold, no other transactions)
    assert summary["bank"] == pytest.approx(summary["total_dividends"], rel=1e-6), \
        "Bank should equal total interest received"
