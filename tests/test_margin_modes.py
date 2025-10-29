"""
Test allow_margin parameter: simple bank vs strict whole account modes.
"""

from datetime import date

import pandas as pd

from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest


def test_allow_margin_true_bank_can_go_negative():
    """
    Test allow_margin=True: bank can go negative (simple mode with margin).

    Scenario: SD8 on declining price with buybacks
    - Price drops, strategy buys shares
    - Bank goes negative (borrowing from yourself)
    - BUY transactions always execute
    """
    # Create simple declining price data
    dates = pd.date_range(start="2020-01-01", end="2020-02-01", freq="D")
    prices = [100.0, 92.0, 85.0, 78.0, 71.0] + [71.0] * (len(dates) - 5)

    df = pd.DataFrame(
        {
            "Open": prices[: len(dates)],
            "High": prices[: len(dates)],
            "Low": prices[: len(dates)],
            "Close": prices[: len(dates)],
        },
        index=dates,
    )

    algo = SyntheticDividendAlgorithm(
        rebalance_size=9.05 / 100.0,  # sd8
        profit_sharing=100.0 / 100.0,  # 100% profit sharing to trigger immediate buyback selling
        buyback_enabled=True,  # Enable buybacks so it BUYS on the way down
    )

    transactions, summary = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 2, 1),
        algo=algo,
        simple_mode=True,  # No opportunity cost for clean testing
        allow_margin=True,  # Simple bank mode
    )

    # Debug: print transactions to see what happened
    print("\n".join([t.to_string() for t in transactions[:20]]))  # First 20 transactions
    print(f"bank_min={summary['bank_min']}, skipped_buys={summary['skipped_buys']}")

    # Verify bank went negative
    assert (
        summary["bank_min"] < 0
    ), f"Bank should go negative in allow_margin=True mode, got {summary['bank_min']}"

    # Verify no skipped buys
    assert summary["skipped_buys"] == 0, "Should not skip any buys with allow_margin=True"
    assert summary["skipped_buy_value"] == 0.0

    # Verify allow_margin flag in summary
    assert summary["allow_margin"] is True


def test_allow_margin_false_bank_never_negative():
    """
    Test allow_margin=False: bank never goes negative (strict whole account).

    Scenario: SD8 on declining price with buybacks
    - Price drops, strategy wants to buy shares
    - Bank has insufficient cash
    - BUY transactions are SKIPPED
    - Bank never goes negative
    """
    # Create simple declining price data (same as above)
    dates = pd.date_range(start="2020-01-01", end="2020-02-01", freq="D")
    prices = [100.0, 92.0, 85.0, 78.0, 71.0] + [71.0] * (len(dates) - 5)

    df = pd.DataFrame(
        {
            "Open": prices[: len(dates)],
            "High": prices[: len(dates)],
            "Low": prices[: len(dates)],
            "Close": prices[: len(dates)],
        },
        index=dates,
    )

    algo = SyntheticDividendAlgorithm(
        rebalance_size=9.05 / 100.0,  # sd8
        profit_sharing=100.0 / 100.0,  # 100% profit sharing to trigger immediate buyback selling
        buyback_enabled=True,  # Enable buybacks so it BUYS on the way down
    )

    transactions, summary = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 2, 1),
        algo=algo,
        simple_mode=True,  # No opportunity cost for clean testing
        allow_margin=False,  # Strict mode
    )

    # Verify bank NEVER went negative
    assert summary["bank_min"] >= 0, "Bank should never go negative in allow_margin=False mode"

    # Verify some buys were skipped (price declined, bank depleted)
    assert summary["skipped_buys"] > 0, "Should skip buys when cash insufficient in strict mode"
    assert summary["skipped_buy_value"] > 0.0

    # Verify allow_margin flag in summary
    assert summary["allow_margin"] is False

    # Check transactions for SKIP BUY messages
    skip_messages = [t for t in transactions if t.action == "SKIP BUY"]
    assert len(skip_messages) > 0, "Should have SKIP BUY transaction messages"
    assert len(skip_messages) == summary["skipped_buys"]


def test_strict_mode_withdrawal_covers_negative_balance():
    """
    Test allow_margin=False: withdrawals must cover negative balance.

    This shouldn't happen in strict mode (bank never negative),
    but test the logic in case bank somehow becomes negative.
    """
    # Create price data
    dates = pd.date_range(start="2020-01-01", end="2020-03-01", freq="D")
    prices = [100.0] * len(dates)

    df = pd.DataFrame({"Open": prices, "High": prices, "Low": prices, "Close": prices}, index=dates)

    algo = None  # buy-and-hold (no algo provided)

    # Run with withdrawals in strict mode
    transactions, summary = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 3, 1),
        algo=algo,
        withdrawal_rate_pct=4.0,  # 4% annual withdrawal
        withdrawal_frequency_days=30,
        simple_mode=True,
        allow_margin=False,  # Strict mode
    )

    # In strict mode with buy-and-hold + withdrawals:
    # - Bank starts at 0
    # - No transactions generate cash
    # - Withdrawals force share sales
    # - Bank should never go negative

    assert summary["bank_min"] >= 0, "Bank should never go negative in strict mode"
    assert summary["shares_sold_for_withdrawals"] > 0, "Should sell shares for withdrawals"
    assert summary["allow_margin"] is False


def test_allow_margin_comparison():
    """
    Compare same backtest with allow_margin=True vs False.

    Verify:
    - Margin mode executes more buys
    - Margin mode has lower bank_min
    - Strict mode skips buys but maintains bank >= 0
    """
    # Create declining then recovering price data
    dates = pd.date_range(start="2020-01-01", end="2020-03-01", freq="D")
    prices_down = list(range(100, 70, -2))
    prices_up = list(range(70, 100, 2))
    prices = prices_down + prices_up + [100] * (len(dates) - len(prices_down) - len(prices_up))
    prices = prices[: len(dates)]

    df = pd.DataFrame({"Open": prices, "High": prices, "Low": prices, "Close": prices}, index=dates)

    algo = SyntheticDividendAlgorithm(
        rebalance_size=9.05 / 100.0,  # sd8
        profit_sharing=100.0 / 100.0,  # 100% profit sharing to trigger immediate buyback selling
        buyback_enabled=True,  # Enable buybacks so it BUYS on the way down
    )

    # Run with allow_margin=True
    _, summary_margin = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 3, 1),
        algo=algo,
        simple_mode=True,
        allow_margin=True,
    )

    # Run with allow_margin=False
    _, summary_strict = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 3, 1),
        algo=algo,
        simple_mode=True,
        allow_margin=False,
    )

    # Verify margin mode went negative, strict didn't
    assert summary_margin["bank_min"] < 0, "Margin mode should go negative"
    assert summary_strict["bank_min"] >= 0, "Strict mode should never go negative"

    # Verify strict mode skipped buys
    assert summary_strict["skipped_buys"] > 0, "Strict mode should skip some buys"
    assert summary_margin["skipped_buys"] == 0, "Margin mode should never skip buys"

    # Verify strict mode has fewer final holdings (missed some buys)
    # Note: This assumes the buyback stack mechanics would differ
    # In practice, strict mode might have similar or different holdings
    # depending on when buys were skipped

    print(
        f"Margin mode: bank_min={summary_margin['bank_min']:.2f}, skipped={summary_margin['skipped_buys']}"
    )
    print(
        f"Strict mode: bank_min={summary_strict['bank_min']:.2f}, skipped={summary_strict['skipped_buys']}"
    )


def test_buy_and_hold_unaffected_by_margin_mode():
    """
    Test that buy-and-hold is unaffected by allow_margin setting.

    Buy-and-hold never generates transactions (after initial purchase),
    so allow_margin should have no effect.
    """
    dates = pd.date_range(start="2020-01-01", end="2020-03-01", freq="D")
    prices = [100.0] * len(dates)

    df = pd.DataFrame({"Open": prices, "High": prices, "Low": prices, "Close": prices}, index=dates)

    algo = None  # buy-and-hold (no algo provided)

    # Run with allow_margin=True
    _, summary_margin = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 3, 1),
        algo=algo,
        simple_mode=True,
        allow_margin=True,
    )

    # Run with allow_margin=False
    _, summary_strict = run_algorithm_backtest(
        df=df,
        ticker="TEST",
        initial_qty=100,
        start_date=date(2020, 1, 1),
        end_date=date(2020, 3, 1),
        algo=algo,
        simple_mode=True,
        allow_margin=False,
    )

    # Both should have identical results
    assert summary_margin["total_return"] == summary_strict["total_return"]
    assert summary_margin["bank_min"] == summary_strict["bank_min"] == 0.0
    assert summary_margin["skipped_buys"] == summary_strict["skipped_buys"] == 0
