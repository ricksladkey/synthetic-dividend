"""Tests for dividend/interest income tracking in backtests."""
from datetime import date

import pandas as pd
import pytest

from src.models.backtest import BuyAndHoldAlgorithm, run_algorithm_backtest


def test_dividend_income_credited_to_bank():
    """Test that dividend payments are correctly added to bank balance."""
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
    expected_total = 4 * 0.25 * 100  # 4 payments × $0.25/share × 100 shares
    assert summary["total_dividends"] == expected_total, f"Total dividends should be ${expected_total}"

    # Verify bank balance increased by dividend amount
    # With buy-and-hold, bank should = total dividends (no other transactions)
    assert summary["bank"] == expected_total, "Bank should equal total dividends received"

    # Verify transactions show dividend payments
    div_transactions = [t for t in transactions if "DIVIDEND" in t]
    assert len(div_transactions) == 4, "Should have 4 dividend transaction logs"


def test_dividend_income_with_different_share_counts():
    """Test that dividend amount scales with holdings."""
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
    assert summary1["total_dividends"] == 50.0, "50 shares × $1.00 = $50"

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
    assert summary2["total_dividends"] == 200.0, "200 shares × $1.00 = $200"


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
    """Test monthly interest payments similar to BIL money market ETF."""
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
    expected_total = 12 * monthly_payment * 100
    assert abs(summary["total_dividends"] - expected_total) < 0.01, \
        f"Total interest should be ~${expected_total}"
    assert summary["bank"] == pytest.approx(expected_total, rel=1e-6), \
        "Bank should equal total interest received"
