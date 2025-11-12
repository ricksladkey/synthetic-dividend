#!/usr/bin/env python3
"""
Test synthetic dividend algorithm on perfectly-behaved synthetic price patterns.

This verifies the algorithm behavior from first principles using simple,
predictable price sequences.
"""

import sys
from datetime import date, timedelta
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.algorithms.factory import build_algo_from_name
from src.models.backtest import run_algorithm_backtest


def create_synthetic_data(prices: list, days_per_level: int = 30) -> pd.DataFrame:
    """
    Create synthetic OHLC data from a list of price levels.

    Args:
        prices: List of price levels (e.g., [100, 200, 300, 200, 300, 400])
        days_per_level: Number of days to spend at each price level

    Returns:
        DataFrame with OHLC data
    """
    dates = []
    opens = []
    highs = []
    lows = []
    closes = []

    start_date = date(2023, 1, 1)
    current_date = start_date

    for i, price in enumerate(prices):
        # Add transition from previous price to current price
        if i > 0:
            prev_price = prices[i - 1]
            # Linear interpolation over 5 days
            for j in range(5):
                t = (j + 1) / 5.0
                interp_price = prev_price + (price - prev_price) * t
                dates.append(current_date)
                opens.append(interp_price * 0.995)  # Slight intraday variation
                highs.append(interp_price * 1.005)
                lows.append(interp_price * 0.995)
                closes.append(interp_price)
                current_date += timedelta(days=1)

        # Stay at this price level for days_per_level
        for _ in range(days_per_level):
            dates.append(current_date)
            opens.append(price * 0.998)
            highs.append(price * 1.002)
            lows.append(price * 0.998)
            closes.append(price)
            current_date += timedelta(days=1)

    df = pd.DataFrame(
        {
            "Open": opens,
            "High": highs,
            "Low": lows,
            "Close": closes,
        },
        index=pd.DatetimeIndex(dates),
    )

    return df


def test_pattern(name: str, prices: list, sdn_values: list = [4, 6, 8, 12, 16, 20, 24, 32]):
    """
    Test a price pattern with various sdN parameters.

    Args:
        name: Pattern name for display
        prices: List of price levels
        sdn_values: SDN parameters to test
    """
    print(f"\n{'='*70}")
    print(f"Pattern: {name}")
    print(f"Price sequence: {' -> '.join(map(str, prices))}")
    print(f"{'='*70}\n")

    df = create_synthetic_data(prices, days_per_level=30)
    start_date = df.index[0].date()
    end_date = df.index[-1].date()

    results = []

    for sd_n in sdn_values:
        strategy = f"sd{sd_n}"
        algo = build_algo_from_name(strategy)

        try:
            transactions, summary = run_algorithm_backtest(
                df=df,
                ticker="SYNTHETIC",
                initial_qty=1000,
                start_date=start_date,
                end_date=end_date,
                algo=algo,
            )

            # Extract metrics
            total_return_pct = summary.get("total_return", 0) * 100
            transaction_count = len([t for t in transactions if t.action in ["BUY", "SELL"]])

            # Get alpha metrics
            realized_alpha = 0.0
            unrealized_alpha = 0.0
            total_alpha = 0.0
            stack_size = 0

            if hasattr(algo, "realized_volatility_alpha"):
                realized_alpha = algo.realized_volatility_alpha
            if hasattr(algo, "unrealized_stack_alpha"):
                unrealized_alpha = algo.unrealized_stack_alpha
            if hasattr(algo, "total_volatility_alpha"):
                total_alpha = algo.total_volatility_alpha
            if hasattr(algo, "buyback_stack_count"):
                stack_size = algo.buyback_stack_count

            # Calculate trigger percentage
            trigger_pct = (2 ** (1 / sd_n) - 1) * 100

            print(
                f"  sd{sd_n:2d} (trigger={trigger_pct:5.2f}%): "
                f"return={total_return_pct:7.2f}%, "
                f"realized={realized_alpha:6.2f}%, "
                f"unrealized={unrealized_alpha:6.2f}%, "
                f"txns={transaction_count:4d}, "
                f"stack={stack_size:5d}"
            )

            results.append(
                {
                    "sd_n": sd_n,
                    "trigger_pct": trigger_pct,
                    "total_return_pct": total_return_pct,
                    "realized_alpha": realized_alpha,
                    "unrealized_alpha": unrealized_alpha,
                    "total_alpha": total_alpha,
                    "transaction_count": transaction_count,
                    "stack_size": stack_size,
                }
            )

        except Exception as e:
            print(f"  sd{sd_n:2d}: ERROR - {e}")

    # Find best by realized alpha
    if results:
        best = max(results, key=lambda r: r["realized_alpha"])
        print(f"\n  ➜ Best REALIZED alpha: sd{best['sd_n']} with {best['realized_alpha']:.2f}%")
        print(
            f"     Trigger: {best['trigger_pct']:.2f}%, Transactions: {best['transaction_count']}"
        )

    return results


def main():
    print("=" * 70)
    print("FIRST PRINCIPLES TEST: Synthetic Price Patterns")
    print("=" * 70)

    # Test 1: Choppy uptrend
    choppy_up_results = test_pattern(
        name="Choppy Uptrend",
        prices=[100, 200, 300, 200, 300, 400],
    )

    # Test 2: Perfect consolidation oscillation
    consolidation_results = test_pattern(
        name="Consolidation (Perfect Oscillation)",
        prices=[100, 200, 100, 200, 100, 200],
    )

    # Test 3: Simple 2x doubling
    simple_double_results = test_pattern(
        name="Simple 2x Doubling",
        prices=[100, 200],
    )

    # Test 4: Smooth uptrend (no chop)
    smooth_up_results = test_pattern(
        name="Smooth Uptrend (No Chop)",
        prices=[100, 120, 140, 160, 180, 200],
    )

    print(f"\n{'='*70}")
    print("ANALYSIS SUMMARY")
    print(f"{'='*70}")
    print("\nKey Insights:")
    print("- Consolidation pattern should maximize realized alpha (perfect mean reversion)")
    print("- Choppy uptrend should favor moderate SDN (balance trend + chop)")
    print("- Smooth uptrend should minimize alpha (pure trend, no volatility to harvest)")
    print("- Transaction count should increase dramatically with tighter triggers")


if __name__ == "__main__":
    main()
