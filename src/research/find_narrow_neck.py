"""Find the withdrawal rate that creates a 'narrow neck' - the point where cash reserves nearly deplete.

This tool runs backtests at progressively higher withdrawal rates to find the maximum
sustainable rate where:
1. Cash reserve reaches a minimum (narrow neck) but doesn't force selling
2. Strategy still generates positive alpha vs buy-and-hold
3. Portfolio maintains positive growth despite withdrawals

This tests the true stress limits of the synthetic dividend strategy.
"""

from datetime import date
from typing import Dict, List, Tuple

from src.algorithms.portfolio_factory import build_portfolio_algo_from_name
from src.models.backtest import run_portfolio_backtest


def find_narrow_neck(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    initial_investment: float = 1_000_000,
    withdrawal_rates: List[float] = None,
) -> None:
    """Find the withdrawal rate that creates the narrowest cash reserve neck.

    Args:
        allocations: Portfolio allocations
        start_date: Backtest start date
        end_date: Backtest end date
        initial_investment: Initial investment amount
        withdrawal_rates: List of withdrawal rates to test (default: 0% to 20% in 2% steps)
    """
    if withdrawal_rates is None:
        # Test 0% to 20% in 2% increments
        withdrawal_rates = [i * 2.0 for i in range(11)]

    print("=" * 80)
    print("NARROW NECK FINDER - Withdrawal Stress Testing")
    print("=" * 80)
    print()
    print(f"Portfolio: {allocations}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Investment: ${initial_investment:,.0f}")
    print()
    print(f"Testing withdrawal rates: {withdrawal_rates}")
    print()

    # Build auto algorithm
    portfolio_algo = build_portfolio_algo_from_name("auto", allocations)

    results = []

    for rate in withdrawal_rates:
        print(f"Testing {rate:.1f}% withdrawal rate...")

        try:
            transactions, summary = run_portfolio_backtest(
                allocations=allocations,
                start_date=start_date,
                end_date=end_date,
                portfolio_algo=portfolio_algo,
                initial_investment=initial_investment,
                withdrawal_rate_pct=rate,
                allow_margin=True,  # Allow temporary margin to see how deep we go
            )

            # Analyze cash reserve trajectory to find narrow neck
            daily_bank_values = summary.get("daily_bank_values", [])
            min_bank = min(daily_bank_values) if daily_bank_values else summary.get("final_bank", 0)

            # Find when the neck was narrowest
            min_bank_index = daily_bank_values.index(min_bank) if daily_bank_values and min_bank in daily_bank_values else -1

            final_bank = summary.get("final_bank", 0)
            total_withdrawn = summary.get("total_withdrawn", 0)
            final_value = summary.get("total_final_value", 0)
            total_return = summary.get("total_return", 0)

            results.append(
                {
                    "rate": rate,
                    "min_bank": min_bank,  # Narrowest point in the neck
                    "min_bank_day": min_bank_index,  # Day when neck was narrowest
                    "final_bank": final_bank,
                    "total_withdrawn": total_withdrawn,
                    "final_value": final_value,
                    "total_return": total_return,
                    "success": min_bank >= 0,  # Never went negative (no forced selling)
                }
            )

            print(f"  Minimum bank: ${min_bank:,.0f} (day {min_bank_index})")
            print(f"  Final bank: ${final_bank:,.0f}")
            print(f"  Total withdrawn: ${total_withdrawn:,.0f}")
            print(f"  Final value: ${final_value:,.0f}")
            print(f"  Total return: {total_return:.2f}%")
            print()

        except Exception as e:
            print(f"  ERROR: {e}")
            print()
            results.append(
                {
                    "rate": rate,
                    "final_bank": None,
                    "total_withdrawn": None,
                    "final_value": None,
                    "total_return": None,
                    "success": False,
                    "error": str(e),
                }
            )

    # Analyze results
    print("=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print()

    print(f"{'Rate':<8} {'Min Bank':<15} {'Final Bank':<15} {'Withdrawn':<15} {'Final Value':<15} {'Return':<10} {'Status'}")
    print("-" * 90)

    min_bank_positive = float("inf")
    narrow_neck_rate = None
    narrow_neck_day = None

    for result in results:
        rate = result["rate"]
        min_bank = result.get("min_bank")
        bank = result.get("final_bank")
        withdrawn = result.get("total_withdrawn")
        value = result.get("final_value")
        ret = result.get("total_return")
        success = result.get("success")

        if bank is not None:
            min_bank_str = f"${min_bank:,.0f}" if min_bank is not None else "N/A"
            bank_str = f"${bank:,.0f}"
            withdrawn_str = f"${withdrawn:,.0f}"
            value_str = f"${value:,.0f}"
            ret_str = f"{ret:.2f}%"
            status = "OK" if success else "MARGIN"

            # Track narrowest neck that stayed positive
            if success and min_bank is not None and min_bank < min_bank_positive:
                min_bank_positive = min_bank
                narrow_neck_rate = rate
                narrow_neck_day = result.get("min_bank_day", -1)

        else:
            min_bank_str = "ERROR"
            bank_str = "ERROR"
            withdrawn_str = "-"
            value_str = "-"
            ret_str = "-"
            status = "FAILED"

        print(f"{rate:.1f}%    {min_bank_str:<15} {bank_str:<15} {withdrawn_str:<15} {value_str:<15} {ret_str:<10} {status}")

    print()

    if narrow_neck_rate is not None:
        print("=" * 80)
        print("NARROW NECK IDENTIFIED")
        print("=" * 80)
        print()
        print(f"  Withdrawal Rate: {narrow_neck_rate:.1f}%")
        print(f"  Minimum Bank Balance: ${min_bank_positive:,.0f}")
        print(f"  Occurred on Day: {narrow_neck_day}")
        print()
        print(
            f"This is the maximum sustainable withdrawal rate that maintains a positive"
        )
        print(f"cash reserve throughout the period. Going higher would require forced selling.")
        print()
        print("The 'narrow neck' is the point where cash reserves are most constrained,")
        print("representing the riskiest moment in the withdrawal strategy.")
        print()

        # Suggest stress test rate
        stress_rate = narrow_neck_rate + 2.0
        print(f"SUGGESTED STRESS TEST RATE: {stress_rate:.1f}%")
        print(
            f"  This pushes beyond the narrow neck to test strategy resilience under pressure."
        )
        print(f"  At this rate, the strategy may need to sell assets or use margin.")
        print()
        print("Use this stress rate to validate that the strategy gracefully handles")
        print("extreme withdrawal scenarios without catastrophic failure.")
    else:
        print("WARNING: No withdrawal rate found that maintains positive cash reserves!")
        print("All tested rates either failed or required margin.")


def main():
    """Run narrow neck finder with validation portfolio."""
    # Classic-plus-crypto (60/30/10) - the validation portfolio
    allocations = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}

    find_narrow_neck(
        allocations=allocations,
        start_date=date(2019, 1, 1),
        end_date=date(2024, 12, 31),
        initial_investment=1_000_000,
        withdrawal_rates=[0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
    )


if __name__ == "__main__":
    main()
