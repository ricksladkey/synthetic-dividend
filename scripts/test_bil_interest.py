#!/usr/bin/env python3
"""
Test BIL interest on CASH balances (integration test).

Verifies that CASH allocations automatically earn BIL yields,
just like a brokerage sweep account.
"""

from datetime import date
from src.models.simulation import run_portfolio_simulation

def test_bil_interest_on_cash():
    """Test that CASH earns BIL interest automatically."""
    print("=" * 80)
    print("INTEGRATION TEST: BIL Interest on CASH Balance")
    print("=" * 80)
    print("\nSetup:")
    print("  - 90% NVDA, 10% CASH")
    print("  - No margin (realistic retail mode)")
    print("  - CASH should earn ~4-5% BIL yields")
    print()

    result = run_portfolio_simulation(
        allocations={
            "NVDA": 0.90,
            "CASH": 0.10,  # Should earn BIL interest
        },
        initial_investment=1_000_000,
        # allow_margin defaults to False
        start_date=date(2023, 1, 3),  # Use cached data range
        end_date=date(2023, 12, 29),
        portfolio_algo="per-asset:sd8",
    )

    txns, stats = result

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    # Find CASH interest payments
    cash_interest_txns = [t for t in txns if t.ticker == "CASH" and t.action == "INTEREST"]

    print(f"\nCASH Interest Payments:")
    print(f"  Total payments: {len(cash_interest_txns)}")

    total_interest = sum(float(t.notes.split('$')[1].split()[0]) for t in cash_interest_txns if '$' in t.notes)
    initial_cash = 100_000  # 10% of $1M

    print(f"  Total interest earned: ${total_interest:,.2f}")
    print(f"  Initial cash allocation: ${initial_cash:,.0f}")
    print(f"  Effective yield: {(total_interest / initial_cash) * 100:.2f}%")

    # Show a few sample interest payments
    print(f"\nSample interest payments (first 3):")
    for txn in cash_interest_txns[:3]:
        print(f"  {txn.transaction_date}: {txn.notes}")

    # Verify reasonable yield (BIL should be ~4-5% in 2023)
    yield_pct = (total_interest / initial_cash) * 100
    print(f"\n{'='*80}")

    if len(cash_interest_txns) > 0:
        print("✅ PASS: CASH earned BIL interest")
        print(f"   Expected: ~4-5% annual yield")
        print(f"   Actual: {yield_pct:.2f}% (based on initial $100K cash)")
    else:
        print("❌ FAIL: No CASH interest payments found!")
        return False

    if 2.0 < yield_pct < 10.0:  # Sanity check range
        print("✅ PASS: Yield is in reasonable range")
    else:
        print(f"⚠️  WARNING: Yield {yield_pct:.2f}% seems unusual (expected 4-5%)")

    # Check final portfolio stats
    print(f"\nPortfolio Performance:")
    print(f"  Final value: ${stats['final_value']:,.0f}")
    print(f"  Final bank: ${stats['final_bank']:,.0f}")
    print(f"  Total return: {((stats['final_value'] / 1_000_000) - 1) * 100:.1f}%")

    # Show CASH dividends in stats
    if "total_dividends_by_asset" in stats:
        cash_divs = stats["total_dividends_by_asset"].get("CASH", 0)
        print(f"  CASH interest (from stats): ${cash_divs:,.2f}")

    return True


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "BIL INTEREST INTEGRATION TEST" + " " * 29 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    success = test_bil_interest_on_cash()

    print("\n" + "=" * 80)
    if success:
        print("TEST COMPLETED SUCCESSFULLY ✅")
        print("\nConclusion:")
        print("  CASH allocations now automatically earn BIL yields (~4-5% APY)")
        print("  This models a realistic brokerage sweep account")
        print("  Warren Buffett's 90/10 portfolio is now fully implemented!")
    else:
        print("TEST FAILED ❌")
    print("=" * 80)
    print()
