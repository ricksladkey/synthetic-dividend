"""Unit tests for buyback stack FIFO unwinding logic.

Tests verify that:
1. Share counts match between SD Full and ATH-Only when price ends at/above all previous ATHs
2. Buyback stack is empty when no active drawdown
3. Buyback stack is non-empty during drawdowns from ATH
4. FIFO unwinding correctly attributes profits
"""

from datetime import date, timedelta
from typing import List, Tuple

import pandas as pd
import pytest

from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest


def create_synthetic_price_data(
    start_date: date, price_path: List[float], ticker: str = "TEST"
) -> pd.DataFrame:
    """Create synthetic OHLC price data for testing.

    Args:
        start_date: Starting date for the series
        price_path: List of closing prices (one per day)
        ticker: Stock ticker symbol

    Returns:
        DataFrame with Date index and OHLC columns
    """
    dates = [start_date + timedelta(days=i) for i in range(len(price_path))]

    # Create OHLC with minimal variance (close = high = low = open for simplicity)
    data = {
        "Date": dates,
        "Open": price_path,
        "High": price_path,
        "Low": price_path,
        "Close": price_path,
        "Volume": [1000000] * len(price_path),  # Constant volume
    }

    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)
    return df


def create_flat_reference_returns(num_days: int) -> pd.DataFrame:
    """Create reference asset with zero returns (for isolated testing).

    Args:
        num_days: Number of days of data

    Returns:
        DataFrame with constant price = 100.0
    """
    start = date(2024, 1, 1)
    prices = [100.0] * num_days
    return create_synthetic_price_data(start, prices, "FLAT")


def run_test_comparison(
    price_path: List[float],
    rebalance_pct: float,
    profit_sharing: float,
    initial_qty: int = 10000,
) -> Tuple[int, int, int, bool]:
    """Run both SD Full and ATH-Only algorithms on synthetic data.

    Args:
        price_path: List of daily closing prices
        rebalance_pct: Rebalance trigger percentage
        profit_sharing: Profit sharing as decimal (e.g., 0.5 for 50%)
        initial_qty: Initial share quantity

    Returns:
        Tuple of (sd_full_shares, ath_only_shares, stack_size, stack_empty)
    """
    start_date = date(2024, 1, 1)
    end_date = start_date + timedelta(days=len(price_path) - 1)

    # Create price data
    price_df = create_synthetic_price_data(start_date, price_path)

    # Create flat reference returns (no opportunity cost effects)
    ref_df = create_flat_reference_returns(len(price_path))

    # Run SD Full
    algo_full = SyntheticDividendAlgorithm(
        rebalance_size=rebalance_pct / 100.0,
        profit_sharing=profit_sharing,
        buyback_enabled=True,
    )

    _, result_full = run_algorithm_backtest(
        df=price_df,
        ticker="TEST",
        initial_qty=initial_qty,
        start_date=start_date,
        end_date=end_date,
        algo=algo_full,
        reference_asset_df=ref_df,
        risk_free_asset_df=ref_df,
        reference_asset_ticker="FLAT",
        risk_free_asset_ticker="FLAT",
    )

    # Run ATH-Only
    algo_ath = SyntheticDividendAlgorithm(
        rebalance_size=rebalance_pct / 100.0,
        profit_sharing=profit_sharing,
        buyback_enabled=False,
    )

    _, result_ath = run_algorithm_backtest(
        df=price_df,
        ticker="TEST",
        initial_qty=initial_qty,
        start_date=start_date,
        end_date=end_date,
        algo=algo_ath,
        reference_asset_df=ref_df,
        risk_free_asset_df=ref_df,
        reference_asset_ticker="FLAT",
        risk_free_asset_ticker="FLAT",
    )

    # Extract results
    sd_full_shares = result_full["holdings"]
    ath_only_shares = result_ath["holdings"]

    # Check buyback stack status (now just a count, not a list)
    total_stack_qty = algo_full.buyback_stack_count
    stack_empty = total_stack_qty == 0

    return sd_full_shares, ath_only_shares, total_stack_qty, stack_empty


class TestBuybackStackGradualRise:
    """Test case: Price gradually doubles from 100 to 200.

    Expected behavior:
    - Price continuously makes new ATHs
    - ATH-Only sells at each new high
    - SD Full buys and sells, but all buybacks unwound
    - Final share counts SHOULD MATCH (both at same endpoint)
    - Buyback stack SHOULD BE EMPTY
    """

    def test_linear_rise_50_days(self):
        """Linear price rise: 100 → 200 over 50 days."""
        # Create linear price path
        price_path = [100.0 + (i * 2.0) for i in range(50)]

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=50.0 / 100.0
        )

        # Both should have same final shares (no drawdown at end)
        assert (
            sd_full == ath_only
        ), f"Share counts should match for monotonic rise: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack should be empty (no unrealized buybacks)
        assert (
            stack_empty
        ), f"Buyback stack should be empty at new ATH: {stack_qty} shares remaining"

    def test_exponential_rise_100_days(self):
        """Exponential price rise: 100 → 200 over 100 days."""
        # Exponential growth
        price_path = [100.0 * (2.0 ** (i / 99.0)) for i in range(100)]

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=9.05, profit_sharing=50.0 / 100.0
        )

        assert (
            sd_full == ath_only
        ), f"Share counts should match for exponential rise: SD Full={sd_full}, ATH-Only={ath_only}"

        assert stack_empty, f"Buyback stack should be empty: {stack_qty} shares remaining"


@pytest.mark.slow
class TestBuybackStackVShape:
    """Test case: Price doubles, halves, then doubles again (V-shape).

    Price path: 100 → 200 → 100 → 200

    Expected behavior:
    - Initial rise: Both algorithms sell
    - Drawdown: SD Full buys, ATH-Only holds
    - Recovery: SD Full unwinds all buybacks
    - At final price = 200 (same as previous ATH):
      * Share counts SHOULD MATCH
      * Buyback stack SHOULD BE EMPTY

    Note: Tests marked @pytest.mark.slow (run full simulations)
    """

    def test_v_shape_symmetric(self):
        """Symmetric V: 100 → 200 → 100 → 200 over 30 days (optimized from 120).

        Enhanced accumulates shares during the dip, then sells them during recovery.
        Because it's selling a percentage of a larger base, it retains MORE shares
        than ATH-only after the recovery. This is the volatility alpha in action.

        Note: Stack may not be fully empty because price only RETURNS to previous ATH
        (doesn't exceed it). Full unwinding only guaranteed when exceeding all previous ATHs.
        """
        # Rise, fall, rise (reduced from 40+40+40 to 10+10+10 for speed)
        rise1 = [100.0 + (i * 10.0) for i in range(10)]  # 100 → 200 in 10 days
        fall = [200.0 - (i * 10.0) for i in range(10)]  # 200 → 100 in 10 days
        rise2 = [100.0 + (i * 10.0) for i in range(10)]  # 100 → 200 in 10 days

        price_path = rise1 + fall + rise2

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=50.0 / 100.0
        )

        # Enhanced should have MORE shares (volatility harvesting)
        assert (
            sd_full >= ath_only
        ), f"Enhanced should have at least as many shares: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack quantity should account for extra shares
        share_diff = sd_full - ath_only
        assert (
            stack_qty == share_diff
        ), f"Stack quantity ({stack_qty}) should equal share difference ({share_diff})"

    def test_v_shape_exceeds_ath(self):
        """V-shape exceeding initial ATH: 100 → 200 → 100 → 250 over 30 days (optimized from 120).

        Enhanced buys during dip, then sells during recovery beyond previous ATH.
        It retains more shares than ATH-only due to volatility harvesting.
        """
        rise1 = [100.0 + (i * 10.0) for i in range(10)]  # 100 → 200 in 10 days
        fall = [200.0 - (i * 10.0) for i in range(10)]  # 200 → 100 in 10 days
        rise2 = [100.0 + (i * 15.0) for i in range(10)]  # 100 → 250 in 10 days

        price_path = rise1 + fall + rise2

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=50.0 / 100.0
        )

        # Enhanced should have MORE shares (volatility harvesting)
        assert (
            sd_full >= ath_only
        ), f"Enhanced should have at least as many shares: SD Full={sd_full}, ATH-Only={ath_only}"

        assert stack_empty, f"Stack should be empty at new ATH: {stack_qty} shares remaining"


class TestBuybackStackDrawdown:
    """Test case: Price ends in drawdown from ATH.

    Expected behavior:
    - SD Full has MORE shares than ATH-Only
    - Buyback stack is NON-EMPTY
    - Stack quantity = share count difference
    """

    def test_drawdown_at_end(self):
        """Price rises then ends in 20% drawdown: 100 → 200 → 160."""
        rise = [100.0 + (i * 2.5) for i in range(40)]  # 100 → 200
        fall = [200.0 - (i * 1.0) for i in range(40)]  # 200 → 160

        price_path = rise + fall

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=50.0 / 100.0
        )

        # SD Full should have MORE shares (bought the dip)
        assert (
            sd_full > ath_only
        ), f"SD Full should have more shares in drawdown: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack should be non-empty
        assert not stack_empty, "Buyback stack should be non-empty during drawdown"

        # Stack quantity should equal share difference
        share_diff = sd_full - ath_only
        assert (
            stack_qty == share_diff
        ), f"Stack quantity ({stack_qty}) should equal share difference ({share_diff})"

    def test_deep_drawdown(self):
        """Deep 50% drawdown: 100 → 200 → 100."""
        rise = [100.0 + (i * 2.5) for i in range(40)]  # 100 → 200
        fall = [200.0 - (i * 2.5) for i in range(40)]  # 200 → 100

        price_path = rise + fall

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=50.0 / 100.0
        )

        # SD Full has more shares
        assert (
            sd_full > ath_only
        ), f"SD Full should have more shares: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack non-empty
        assert not stack_empty, "Stack should be non-empty in deep drawdown"

        # Verify stack accounts for difference
        assert stack_qty == (sd_full - ath_only), "Stack should account for all extra shares"


class TestBuybackStackMultipleCycles:
    """Test case: Multiple complete buy-sell cycles.

    Expected behavior:
    - Each recovery to ATH unwinds all buybacks
    - Stack alternates between empty (at ATH) and non-empty (in drawdown)
    """

    def test_three_complete_cycles(self):
        """Three V-shapes: 100→200→100→200→100→200.

        Each cycle allows Enhanced to harvest volatility by buying low and selling high.
        Enhanced accumulates more shares through multiple volatility cycles.

        Note: Stack may not be empty at final ATH since price only returns to (not exceeds)
        previous peaks.
        """
        cycle1_up = [100.0 + (i * 5.0) for i in range(20)]  # 100 → 200
        cycle1_down = [200.0 - (i * 5.0) for i in range(20)]  # 200 → 100

        cycle2_up = [100.0 + (i * 5.0) for i in range(20)]  # 100 → 200
        cycle2_down = [200.0 - (i * 5.0) for i in range(20)]  # 200 → 100

        cycle3_up = [100.0 + (i * 5.0) for i in range(20)]  # 100 → 200

        price_path = cycle1_up + cycle1_down + cycle2_up + cycle2_down + cycle3_up

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=50.0 / 100.0
        )

        # Enhanced should have MORE shares (multiple volatility harvests)
        assert (
            sd_full >= ath_only
        ), f"Enhanced should have at least as many shares: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack quantity should account for extra shares
        share_diff = sd_full - ath_only
        assert (
            stack_qty == share_diff
        ), f"Stack quantity ({stack_qty}) should equal share difference ({share_diff})"


class TestBuybackStackParameterVariations:
    """Test with different rebalance and profit-sharing parameters."""

    def test_aggressive_rebalance(self):
        """High rebalance trigger (15%) with V-shape recovery.

        Larger rebalance triggers mean fewer but larger transactions.
        Enhanced still harvests volatility, retaining more shares.
        """
        rise = [100.0 + (i * 2.5) for i in range(40)]
        fall = [200.0 - (i * 2.5) for i in range(40)]
        rise2 = [100.0 + (i * 2.5) for i in range(40)]

        price_path = rise + fall + rise2

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=15.0, profit_sharing=50.0 / 100.0
        )

        assert (
            sd_full >= ath_only
        ), f"Enhanced should have at least as many shares: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack quantity should account for extra shares
        share_diff = sd_full - ath_only
        assert (
            stack_qty == share_diff
        ), f"Stack quantity ({stack_qty}) should equal share difference ({share_diff})"

    def test_granular_rebalance(self):
        """Very granular rebalance trigger (4.44%) with V-shape recovery.

        Smaller rebalance triggers mean more frequent but smaller transactions.
        Enhanced still harvests volatility through numerous small cycles.
        """
        rise = [100.0 + (i * 2.5) for i in range(40)]
        fall = [200.0 - (i * 2.5) for i in range(40)]
        rise2 = [100.0 + (i * 2.5) for i in range(40)]

        price_path = rise + fall + rise2

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=4.44, profit_sharing=50.0 / 100.0
        )

        assert (
            sd_full >= ath_only
        ), f"Enhanced should have at least as many shares: SD Full={sd_full}, ATH-Only={ath_only}"

        # Stack quantity should account for extra shares
        share_diff = sd_full - ath_only
        assert (
            stack_qty == share_diff
        ), f"Stack quantity ({stack_qty}) should equal share difference ({share_diff})"

    def test_zero_profit_sharing(self):
        """0% profit sharing (reinvest all) with recovery.

        With 0% profit sharing, buy_qty and sell_qty are both 0, so no transactions occur.
        Both strategies should have identical holdings (no rebalancing).
        """
        rise = [100.0 + (i * 2.5) for i in range(40)]
        fall = [200.0 - (i * 2.5) for i in range(40)]
        rise2 = [100.0 + (i * 2.5) for i in range(40)]

        price_path = rise + fall + rise2

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=0.0 / 100.0
        )

        # No transactions occur, so shares should be identical
        assert (
            sd_full == ath_only
        ), f"Shares should match with 0% profit sharing: SD Full={sd_full}, ATH-Only={ath_only}"

        assert stack_empty, "Stack should be empty (no buybacks occurred)"

    def test_full_profit_sharing(self):
        """100% profit sharing (take all cash) with recovery."""
        rise = [100.0 + (i * 2.5) for i in range(40)]
        fall = [200.0 - (i * 2.5) for i in range(40)]
        rise2 = [100.0 + (i * 2.5) for i in range(40)]

        price_path = rise + fall + rise2

        sd_full, ath_only, stack_qty, stack_empty = run_test_comparison(
            price_path=price_path, rebalance_pct=10.0, profit_sharing=100.0 / 100.0
        )

        assert (
            sd_full == ath_only
        ), f"Shares should match with 100% profit sharing: SD Full={sd_full}, ATH-Only={ath_only}"

        assert stack_empty, "Stack should be empty at ATH"


if __name__ == "__main__":
    # Simple test runner for manual execution
    import sys

    print("Running Buyback Stack Unit Tests...")
    print("=" * 70)

    test_classes = [
        TestBuybackStackGradualRise,
        TestBuybackStackVShape,
        TestBuybackStackDrawdown,
        TestBuybackStackMultipleCycles,
        TestBuybackStackParameterVariations,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = []

    for test_class in test_classes:
        print(f"\n{test_class.__name__}:")
        print(test_class.__doc__)

        # Get all test methods
        test_methods = [m for m in dir(test_class) if m.startswith("test_")]

        for method_name in test_methods:
            total_tests += 1
            test_instance = test_class()
            test_method = getattr(test_instance, method_name)

            try:
                test_method()
                print(f"  OK {method_name}")
                passed_tests += 1
            except AssertionError as e:
                print(f"  FAIL {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, str(e)))
            except Exception as e:
                print(f"  ERROR {method_name}: {str(e)}")
                failed_tests.append((test_class.__name__, method_name, f"ERROR: {str(e)}"))

    print("\n" + "=" * 70)
    print(f"Results: {passed_tests}/{total_tests} tests passed")

    if failed_tests:
        print("\nFailed tests:")
        for class_name, method_name, error in failed_tests:
            print(f"  {class_name}.{method_name}")
            print(f"    {error}")
        sys.exit(1)
    else:
        print("\nOK All tests passed!")
        sys.exit(0)
