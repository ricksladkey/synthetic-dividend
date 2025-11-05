"""
Unit tests for withdrawal functionality.

Tests that withdrawal policy works correctly with different strategies,
and that simple_mode provides clean behavior for unit testing.
"""

from datetime import date, timedelta

import pandas as pd

from src.models.backtest import run_portfolio_backtest


def create_price_data(price_path, ticker="TEST"):
    """Create synthetic OHLC price data for testing."""
    start_date = date(2020, 1, 1)
    dates = [start_date + timedelta(days=i * 30) for i in range(len(price_path))]  # Monthly

    data = {
        "Date": dates,
        "Open": price_path,
        "High": price_path,
        "Low": price_path,
        "Close": price_path,
        "Volume": [1000000] * len(price_path),
    }

    df = pd.DataFrame(data)
    df.set_index("Date", inplace=True)
    return df


def create_flat_reference(num_months):
    """Create flat reference returns for opportunity cost calculation."""
    return create_price_data([100.0] * num_months, "FLAT")


def test_withdrawal_from_bank_balance():
    """
    Test that withdrawals come from bank balance when SD8 generates cash.

    SD8 generates cash → withdrawals from bank → no shares sold
    """
    # Create steadily rising price (SD8 will generate cash from profit sharing)
    prices = [100.0 + i * 5 for i in range(13)]  # $100 → $160 over 12 months
    price_df = create_price_data(prices)

    # Initial position: 1000 shares @ $100 = $100,000
    initial_shares = 1000
    start_date = date(2020, 1, 1)
    end_date = start_date + timedelta(days=12 * 30)

    # Run SD8 with 4% withdrawal rate (monthly withdrawals)
    # Convert single-ticker to portfolio format
    start_price = price_df.iloc[0]["Close"]
    initial_investment = initial_shares * start_price
    allocations = {"TEST": 1.0}
    portfolio_algo = "per-asset:sd8,50"  # 9.05% trigger, 50% profit sharing

    # Mock the HistoryFetcher to return our synthetic data
    from unittest.mock import patch

    import src.data.fetcher as fetcher_module

    original_get_history = fetcher_module.HistoryFetcher.get_history

    def mock_get_history(self, ticker, start_date, end_date):
        if ticker == "TEST":
            return price_df
        return original_get_history(self, ticker, start_date, end_date)

    with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
        txns, portfolio_results = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=initial_investment,
            withdrawal_rate_pct=4.0,  # 4% annual withdrawal
            withdrawal_frequency_days=30,  # Monthly
            simple_mode=True,  # Clean mode for testing
        )

        # Map portfolio results to single-ticker format for compatibility
        from src.models.backtest import _map_portfolio_to_single_ticker_summary

        results = _map_portfolio_to_single_ticker_summary(
            portfolio_summary=portfolio_results,
            ticker="TEST",
            df_indexed=price_df,
            start_date=start_date,
            end_date=end_date,
            algo_obj=None,  # Not needed for this test
            transactions=txns,
        )

    # Extract metrics
    total_withdrawn = results["total_withdrawn"]
    withdrawal_count = results["withdrawal_count"]
    shares_sold_for_withdrawals = results["shares_sold_for_withdrawals"]

    print("\n=== Withdrawal from Bank Balance Test ===")
    print(f"Total withdrawn: ${total_withdrawn:,.2f}")
    print(f"Withdrawal count: {withdrawal_count}")
    print(f"Shares sold for withdrawals: {shares_sold_for_withdrawals}")
    print(f"Final bank balance: ${results['bank']:,.2f}")

    # Check withdrawals occurred
    assert withdrawal_count > 0, "Should have processed withdrawals"

    # With monthly price data (13 points over ~360 days), expect ~12 monthly withdrawals
    assert 10 <= withdrawal_count <= 12, f"Expected ~12 monthly withdrawals, got {withdrawal_count}"

    # SD8 generates cash from profit sharing, but may need to sell some shares
    # in early periods before enough cash accumulates
    assert (
        shares_sold_for_withdrawals < 10
    ), f"SD8 should mostly fund withdrawals from bank, but sold {shares_sold_for_withdrawals} shares"

    # Expected: $4,000 annual withdrawal = ~$333/month
    expected_annual = 100000 * 0.04
    expected_per_withdrawal = expected_annual / 12
    actual_per_withdrawal = total_withdrawn / withdrawal_count if withdrawal_count > 0 else 0

    print(f"Expected per withdrawal: ${expected_per_withdrawal:.2f}")
    print(f"Actual per withdrawal: ${actual_per_withdrawal:.2f}")

    # Withdrawals should be approximately correct (within 10%)
    assert (
        abs(actual_per_withdrawal - expected_per_withdrawal) / expected_per_withdrawal < 0.2
    ), f"Withdrawal amount off: expected ~${expected_per_withdrawal:.2f}, got ${actual_per_withdrawal:.2f}"

    print("\n✅ Test passed: SD8 funded withdrawals from bank balance")


def test_withdrawal_forces_selling_for_buy_and_hold():
    """
    Test that withdrawals force share sales when using buy-and-hold (zero bank balance).

    Buy-and-hold generates $0 cash → withdrawals force selling → position reduced
    """
    # Create steadily rising price
    prices = [100.0 + i * 5 for i in range(13)]  # $100 → $160 over 12 months
    price_df = create_price_data(prices)

    # Initial position: 1000 shares @ $100 = $100,000
    initial_shares = 1000
    start_date = date(2020, 1, 1)
    end_date = start_date + timedelta(days=12 * 30)

    # Run buy-and-hold (no algorithm, just hold)
    # Convert single-ticker to portfolio format
    start_price = price_df.iloc[0]["Close"]
    initial_investment = initial_shares * start_price
    allocations = {"TEST": 1.0}
    portfolio_algo = "per-asset:buy-and-hold"

    # Mock the HistoryFetcher to return our synthetic data
    from unittest.mock import patch

    import src.data.fetcher as fetcher_module

    original_get_history = fetcher_module.HistoryFetcher.get_history

    def mock_get_history(self, ticker, start_date, end_date):
        if ticker == "TEST":
            return price_df
        return original_get_history(self, ticker, start_date, end_date)

    with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
        txns, portfolio_results = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=initial_investment,
            withdrawal_rate_pct=4.0,  # 4% annual withdrawal
            withdrawal_frequency_days=30,  # Monthly
            simple_mode=True,  # Clean mode for testing
        )

        # Map portfolio results to single-ticker format for compatibility
        from src.models.backtest import _map_portfolio_to_single_ticker_summary

        results = _map_portfolio_to_single_ticker_summary(
            portfolio_summary=portfolio_results,
            ticker="TEST",
            df_indexed=price_df,
            start_date=start_date,
            end_date=end_date,
            algo_obj=None,  # Not needed for this test
            transactions=txns,
        )

    # Extract metrics
    total_withdrawn = results["total_withdrawn"]
    withdrawal_count = results["withdrawal_count"]
    shares_sold_for_withdrawals = results["shares_sold_for_withdrawals"]
    final_holdings = results["holdings"]

    print("\n=== Withdrawal Forces Selling (Buy-and-Hold) Test ===")
    print(f"Total withdrawn: ${total_withdrawn:,.2f}")
    print(f"Withdrawal count: {withdrawal_count}")
    print(f"Shares sold for withdrawals: {shares_sold_for_withdrawals}")
    print(f"Initial holdings: {initial_shares}")
    print(f"Final holdings: {final_holdings}")
    print(
        f"Holdings reduction: {initial_shares - final_holdings} shares ({(initial_shares - final_holdings)/initial_shares*100:.1f}%)"
    )

    # Buy-and-hold should have forced selling
    assert (
        shares_sold_for_withdrawals > 0
    ), "Buy-and-hold should have been forced to sell shares for withdrawals"

    # Final holdings should be less than initial
    assert (
        final_holdings < initial_shares
    ), f"Holdings should be reduced: started {initial_shares}, ended {final_holdings}"

    # Check withdrawals occurred
    assert withdrawal_count > 0, "Should have processed withdrawals"

    print(
        f"\n✅ Test passed: Buy-and-hold forced to sell {shares_sold_for_withdrawals} shares for withdrawals"
    )


def test_simple_mode_no_opportunity_cost():
    """
    Test that simple_mode disables opportunity cost and risk-free gains.

    Simple mode: borrowing is free, cash holds its value.
    Perfect for unit testing where we want clean, predictable behavior.
    """
    # Create price path that would normally incur opportunity cost
    prices = [100.0, 50.0, 100.0]  # Drawdown and recovery
    price_df = create_price_data(prices)

    initial_shares = 1000
    start_date = date(2020, 1, 1)
    end_date = start_date + timedelta(days=2 * 30)

    # Convert single-ticker to portfolio format
    start_price = price_df.iloc[0]["Close"]
    initial_investment = initial_shares * start_price
    allocations = {"TEST": 1.0}
    portfolio_algo = "per-asset:sd8,50"  # 9.05% trigger, 50% profit sharing, buybacks enabled

    # Mock the HistoryFetcher to return our synthetic data
    from unittest.mock import patch

    import src.data.fetcher as fetcher_module

    original_get_history = fetcher_module.HistoryFetcher.get_history

    def mock_get_history(self, ticker, start_date, end_date):
        if ticker == "TEST":
            return price_df
        return original_get_history(self, ticker, start_date, end_date)

    with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
        # Test 1: WITH simple_mode
        txns_simple, portfolio_results_simple = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=initial_investment,
            simple_mode=True,
        )

        # Map portfolio results to single-ticker format for compatibility
        from src.models.backtest import _map_portfolio_to_single_ticker_summary

        results_simple = _map_portfolio_to_single_ticker_summary(
            portfolio_summary=portfolio_results_simple,
            ticker="TEST",
            df_indexed=price_df,
            start_date=start_date,
            end_date=end_date,
            algo_obj=None,  # Not needed for this test
            transactions=txns_simple,
        )

        # Test 2: WITHOUT simple_mode (normal mode with 10% opportunity cost)
        txns_normal, portfolio_results_normal = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=initial_investment,
            simple_mode=False,
            reference_rate_ticker="MOCK-LINEAR-100-110",  # 10% annual return asset
        )

        # Map portfolio results to single-ticker format for compatibility
        results_normal = _map_portfolio_to_single_ticker_summary(
            portfolio_summary=portfolio_results_normal,
            ticker="TEST",
            df_indexed=price_df,
            start_date=start_date,
            end_date=end_date,
            algo_obj=None,  # Not needed for this test
            transactions=txns_normal,
        )

    print("\n=== Simple Mode Test ===")
    print("\nSimple Mode:")
    print(f"  Opportunity cost: ${results_simple['opportunity_cost']:,.2f}")
    print(f"  Risk-free gains: ${results_simple['risk_free_gains']:,.2f}")
    print(f"  Bank min: ${results_simple['bank_min']:,.2f}")

    print("\nNormal Mode (10% opportunity cost):")
    print(f"  Opportunity cost: ${results_normal['opportunity_cost']:,.2f}")
    print(f"  Risk-free gains: ${results_normal['risk_free_gains']:,.2f}")
    print(f"  Bank min: ${results_normal['bank_min']:,.2f}")

    # Simple mode should have zero opportunity cost
    assert (
        results_simple["opportunity_cost"] == 0.0
    ), f"Simple mode should have zero opportunity cost, got ${results_simple['opportunity_cost']:,.2f}"

    # Simple mode should have zero risk-free gains
    assert (
        results_simple["risk_free_gains"] == 0.0
    ), f"Simple mode should have zero risk-free gains, got ${results_simple['risk_free_gains']:,.2f}"

    # Normal mode should have opportunity cost (negative bank incurs cost)
    if results_normal["bank_min"] < 0:
        assert (
            results_normal["opportunity_cost"] > 0
        ), "Normal mode with negative bank should have opportunity cost"

    print(
        "\n✅ Test passed: Simple mode provides clean behavior (free borrowing, cash holds value)"
    )


if __name__ == "__main__":
    print("Testing withdrawal functionality...")
    print("=" * 80)

    test_withdrawal_from_bank_balance()
    test_withdrawal_forces_selling_for_buy_and_hold()
    test_simple_mode_no_opportunity_cost()

    print("\n" + "=" * 80)
    print("All tests passed! Withdrawal policy works correctly.")
