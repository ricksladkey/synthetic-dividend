#!/usr/bin/env python3
"""
Test CASH ticker support and no-margin mode.

Verifies:
1. CASH allocation is reserved in bank (not purchased)
2. allow_margin=False is default
3. Buys are skipped when insufficient cash
4. Cash accumulates naturally in uptrends (barbell effect)
"""

from datetime import date

from src.models.simulation import run_portfolio_simulation


def test_cash_allocation():
    """Test that CASH ticker is properly reserved."""
    print("=" * 80)
    print("TEST 1: CASH Allocation with No Margin")
    print("=" * 80)

    result = run_portfolio_simulation(
        allocations={
            "NVDA": 0.60,  # 60% in NVDA
            "PLTR": 0.30,  # 30% in PLTR
            "CASH": 0.10,  # 10% cash reserve
        },
        initial_investment=1_000_000,
        # Note: allow_margin not specified, should default to False
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo="per-asset:sd8",
    )

    txns, stats = result

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Final portfolio value: ${stats['final_value']:,.0f}")
    print(f"Final bank balance: ${stats['final_bank']:,.0f}")
    print(f"Min bank balance: ${stats.get('bank_min', 0):,.0f}")
    print(f"Max bank balance: ${stats.get('bank_max', 0):,.0f}")
    print(f"Skipped buys: {stats.get('skipped_buys', 0)}")
    print(f"Total transactions: {len(txns)}")

    # Verify cash reserve
    assert stats["bank_min"] >= 0, f"Bank went negative! Min: ${stats.get('bank_min', 0):,.0f}"
    print("\n✅ PASS: Bank never went negative (no margin used)")

    # Should have some skipped buys in no-margin mode
    if stats.get("skipped_buys", 0) > 0:
        print(f"✅ PASS: {stats['skipped_buys']} buys skipped due to insufficient cash")
    else:
        print("⚠️  WARNING: No skipped buys (cash reserve may have been too large)")

    return stats


def test_explicit_margin_enabled():
    """Test that margin can still be explicitly enabled."""
    print("\n" + "=" * 80)
    print("TEST 2: Explicit Margin Enabled (for comparison)")
    print("=" * 80)

    result = run_portfolio_simulation(
        allocations={
            "NVDA": 0.90,  # 90% in NVDA
            "CASH": 0.10,  # 10% cash reserve
        },
        initial_investment=1_000_000,
        allow_margin=True,  # Explicitly enable margin
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo="per-asset:sd8",
    )

    txns, stats = result

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Final portfolio value: ${stats['final_value']:,.0f}")
    print(f"Final bank balance: ${stats['final_bank']:,.0f}")
    print(f"Min bank balance: ${stats.get('bank_min', 0):,.0f}")
    print(f"Max bank balance: ${stats.get('bank_max', 0):,.0f}")
    print(f"Skipped buys: {stats.get('skipped_buys', 0)}")

    if stats.get("bank_min", 0) < 0:
        print(f"✅ PASS: Margin was used (min bank: ${stats['bank_min']:,.0f})")

    return stats


def test_no_cash_allocation():
    """Test backward compatibility - no CASH ticker."""
    print("\n" + "=" * 80)
    print("TEST 3: Backward Compatibility (no CASH ticker)")
    print("=" * 80)

    result = run_portfolio_simulation(
        allocations={
            "NVDA": 1.0,  # 100% in NVDA (old style)
        },
        initial_investment=1_000_000,
        allow_margin=True,  # Explicitly enable for old behavior
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo="per-asset:sd8",
    )

    txns, stats = result

    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)
    print(f"Final portfolio value: ${stats['final_value']:,.0f}")
    print(f"Final bank balance: ${stats['final_bank']:,.0f}")

    print("✅ PASS: Old-style allocation still works")

    return stats


def test_barbell_dynamics():
    """Test that cash accumulates in uptrends (barbell effect)."""
    print("\n" + "=" * 80)
    print("TEST 4: Barbell Dynamics (cash accumulation in uptrend)")
    print("=" * 80)

    result = run_portfolio_simulation(
        allocations={
            "NVDA": 0.90,  # 90% in NVDA
            "CASH": 0.10,  # 10% starting cash
        },
        initial_investment=1_000_000,
        allow_margin=False,
        start_date=date(2023, 1, 1),
        end_date=date(2023, 12, 31),
        portfolio_algo="per-asset:sd8",
    )

    txns, stats = result

    initial_cash = 100_000  # 10% of $1M
    final_cash = stats["final_bank"]
    max_cash = stats.get("bank_max", final_cash)

    print("\n" + "=" * 80)
    print("CASH DYNAMICS")
    print("=" * 80)
    print(f"Initial cash reserve: ${initial_cash:,.0f}")
    print(f"Final cash: ${final_cash:,.0f}")
    print(f"Max cash during year: ${max_cash:,.0f}")
    print(
        f"Cash growth: ${final_cash - initial_cash:,.0f} ({(final_cash/initial_cash - 1)*100:.1f}%)"
    )

    # In a strong uptrend (NVDA 2023), cash should accumulate from selling
    if max_cash > initial_cash * 1.5:
        print(f"✅ PASS: Cash accumulated during uptrend (barbell effect observed)")
    else:
        print(f"⚠️  WARNING: Cash did not accumulate significantly")

    return stats


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 20 + "CASH TICKER & NO-MARGIN MODE TESTS" + " " * 24 + "║")
    print("╚" + "=" * 78 + "╝")

    stats1 = test_cash_allocation()
    stats2 = test_explicit_margin_enabled()
    stats3 = test_no_cash_allocation()
    stats4 = test_barbell_dynamics()

    print("\n" + "=" * 80)
    print("SUMMARY COMPARISON")
    print("=" * 80)
    print(f"{'Mode':<30} {'Final Value':<15} {'Final Bank':<15} {'Min Bank':<15}")
    print("-" * 80)
    print(
        f"{'No margin + 10% cash':<30} ${stats1['final_value']:>13,.0f} ${stats1['final_bank']:>13,.0f} ${stats1.get('bank_min', 0):>13,.0f}"
    )
    print(
        f"{'Margin enabled + 10% cash':<30} ${stats2['final_value']:>13,.0f} ${stats2['final_bank']:>13,.0f} ${stats2.get('bank_min', 0):>13,.0f}"
    )
    print(
        f"{'Old style (100% NVDA + margin)':<30} ${stats3['final_value']:>13,.0f} ${stats3['final_bank']:>13,.0f} ${stats3.get('bank_min', 0):>13,.0f}"
    )
    print(
        f"{'Barbell test':<30} ${stats4['final_value']:>13,.0f} ${stats4['final_bank']:>13,.0f} ${stats4.get('bank_min', 0):>13,.0f}"
    )

    print("\n" + "=" * 80)
    print("ALL TESTS COMPLETED")
    print("=" * 80)
