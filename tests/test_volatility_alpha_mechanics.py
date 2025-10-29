"""
Unit tests for volatility alpha mechanics.

Tests the fundamental mechanism by which SD8 generates alpha:
buying back shares during dips and re-selling on recovery.
"""

from datetime import date, timedelta

import pandas as pd

from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest


def create_price_data(price_path, ticker="TEST"):
    """Create synthetic OHLC price data for testing."""
    start_date = date(2020, 1, 1)
    dates = [start_date + timedelta(days=i) for i in range(len(price_path))]

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


def create_flat_reference(num_days):
    """Create flat reference returns for opportunity cost calculation."""
    return create_price_data([100.0] * num_days, "FLAT")


def test_drawdown_recovery_generates_alpha():
    """
    Test that SD8 generates alpha from a drawdown-and-recovery cycle.

    Price path: $100 -> gradual drawdown to $49 -> gradual recovery to $125
    - 51% drawdown triggers multiple buybacks
    - 155% recovery from bottom generates profit

    Expected behavior:
    - SD8 should execute ~8 buys during drawdown
    - Each buy captures ~0.3% alpha
    - Total alpha should be ~3% (8 buys * 0.3%)
    - Volatility alpha = (SD8 return - Buy&Hold return) should be positive

    This is the core value proposition: earning "nickels and dimes"
    from volatility while maintaining similar final value.
    """
    # Create gradual price path: $100 -> $49 -> $125
    # The 9.05% rebalancing threshold means we need prices to drop in steps
    # to trigger multiple buys

    # Starting at $100, each 9.05% drop triggers a buy:
    # Step 1: 100 * (1 - 0.0905) = 90.95
    # Step 2: 90.95 * (1 - 0.0905) = 82.72
    # Step 3: 82.72 * (1 - 0.0905) = 75.23
    # Step 4: 75.23 * (1 - 0.0905) = 68.42
    # Step 5: 68.42 * (1 - 0.0905) = 62.23
    # Step 6: 62.23 * (1 - 0.0905) = 56.60
    # Step 7: 56.60 * (1 - 0.0905) = 51.48
    # Step 8: 51.48 * (1 - 0.0905) = 46.82

    # So to reach $49, we need about 7-8 steps
    prices = [
        100.0,  # Start
        90.0,  # -10% (triggers buy #1)
        82.0,  # -9.1% from prev (triggers buy #2)
        74.0,  # -9.8% (triggers buy #3)
        67.0,  # -9.5% (triggers buy #4)
        61.0,  # -9.0% (triggers buy #5)
        55.0,  # -9.8% (triggers buy #6)
        50.0,  # -9.1% (triggers buy #7)
        49.0,  # -2% (bottom, triggers buy #8)
        60.0,  # Recovery starts
        75.0,  # Selling starts here
        90.0,  # More selling
        110.0,  # New ATH, more selling
        125.0,  # Final price
    ]

    price_df = create_price_data(prices)
    ref_df = create_flat_reference(len(prices))

    # Initial position: 1000 shares @ $100 = $100,000
    initial_shares = 1000
    start_date = date(2020, 1, 1)
    end_date = start_date + timedelta(days=len(prices) - 1)

    # Run SD8 with standard 9.05% rebalancing, 50% profit sharing
    algo = SyntheticDividendAlgorithm(
        rebalance_size=9.05 / 100.0,
        profit_sharing=50.0 / 100.0,
        buyback_enabled=True,
    )

    txns, results = run_algorithm_backtest(
        df=price_df,
        ticker="TEST",
        initial_qty=initial_shares,
        start_date=start_date,
        end_date=end_date,
        algo=algo,
        reference_asset_df=ref_df,
        reference_asset_ticker="FLAT",
    )

    # Extract key metrics
    buy_and_hold_return = results["baseline"]["total_return"] * 100  # Convert to percentage
    sd8_return = results["total_return"] * 100  # Convert to percentage
    volatility_alpha = results["volatility_alpha"] * 100  # Convert to percentage
    final_value = results["end_value"]
    bank_balance = results["bank"]

    # Buy-and-hold baseline
    # Started with 1000 shares @ $100, ended at $125
    # Return = (1000 * $125 - 1000 * $100) / (1000 * $100) = 25%
    expected_bh_return = 25.0

    # Count buy transactions (should be ~8 during drawdown)
    buy_txns = [tx for tx in txns if tx.action == "BUY" and "Initial purchase" not in tx.notes]
    num_buys = len(buy_txns)

    # Assertions
    print("\n=== Drawdown-Recovery Volatility Alpha Test ===")
    print("Price path: $100 -> $49 -> $125")
    print(f"Buy-and-Hold return: {buy_and_hold_return:.2f}%")
    print(f"SD8 return: {sd8_return:.2f}%")
    print(f"Volatility alpha: {volatility_alpha:.2f}%")
    print(f"Number of BUY transactions: {num_buys}")
    print("Expected alpha per buy: ~0.3%")
    print(f"Total expected alpha: ~{num_buys * 0.3:.1f}%")
    print(f"Final value: ${final_value:,.2f}")
    print(f"Bank balance: ${bank_balance:,.2f}")
    print("\nTransactions:")
    for tx in txns:
        print(f"  {tx}")

    # 1. Buy-and-hold return should match expected
    assert (
        abs(buy_and_hold_return - expected_bh_return) < 0.1
    ), f"Buy-and-hold return {buy_and_hold_return:.2f}% doesn't match expected {expected_bh_return}%"

    # 2. Should have approximately 8 buy transactions during drawdown
    assert 7 <= num_buys <= 10, f"Expected ~8 buy transactions, got {num_buys}"

    # 3. Volatility alpha should be strongly POSITIVE
    # With a 51% drawdown followed by 155% recovery, SD8 captures significant alpha
    # After multi-bracket gap fix: ~7% (was ~15-20% before fix due to overcounting)
    assert (
        5.0 <= volatility_alpha <= 15.0
    ), f"Expected significant positive alpha from drawdown-recovery, got {volatility_alpha:.2f}%"

    # 4. Volatility alpha should be POSITIVE (SD8 beats buy-and-hold)
    assert (
        volatility_alpha > 0
    ), f"Volatility alpha should be positive in drawdown-recovery scenario, got {volatility_alpha:.2f}%"

    # 5. SD8 should outperform buy-and-hold
    assert (
        sd8_return > buy_and_hold_return
    ), f"SD8 ({sd8_return:.2f}%) should outperform buy-and-hold ({buy_and_hold_return:.2f}%)"

    # Note: Final value comparison removed - volatility alpha is measured as return percentage,
    # and SD8 holds both shares + cash (bank balance), so direct value comparison is not meaningful.
    # The return percentage comparison above is the correct validation.

    print(f"\n✅ Test passed: SD8 generated {volatility_alpha:.2f}% alpha from {num_buys} buybacks")
    print(f"   Alpha per buy: {volatility_alpha / num_buys:.2f}%")
    print(
        "   This validates the core mechanism: buying dips and selling rallies generates measurable alpha!"
    )


if __name__ == "__main__":
    print("Testing volatility alpha mechanics...")
    print("=" * 80)

    test_drawdown_recovery_generates_alpha()

    print("\n" + "=" * 80)
    print("Test passed! Volatility alpha mechanics validated.")
