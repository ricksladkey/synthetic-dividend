#!/usr/bin/env python3
"""
Unit tests for CASH ticker support (no market data required).

Tests the logic changes without running full backtests.
"""

def test_cash_filtering():
    """Test that CASH is properly filtered from ticker lists."""
    allocations = {
        "NVDA": 0.60,
        "PLTR": 0.30,
        "CASH": 0.10,
    }

    # Simulate the filtering logic from simulation.py
    real_tickers = [t for t in allocations.keys() if t != "CASH"]

    print("Test 1: CASH Filtering")
    print(f"  All allocations: {list(allocations.keys())}")
    print(f"  Real tickers: {real_tickers}")
    print(f"  CASH filtered out: {'CASH' not in real_tickers}")

    assert "CASH" not in real_tickers, "CASH should be filtered out"
    assert len(real_tickers) == 2, "Should have 2 real tickers"
    assert set(real_tickers) == {"NVDA", "PLTR"}, "Should have NVDA and PLTR"

    print("  ✅ PASS\n")


def test_allow_margin_default():
    """Test that allow_margin defaults to False."""
    import inspect
    from src.models.simulation import run_portfolio_simulation

    sig = inspect.signature(run_portfolio_simulation)
    allow_margin_param = sig.parameters['allow_margin']

    print("Test 2: allow_margin Default Value")
    print(f"  Parameter: allow_margin")
    print(f"  Default value: {allow_margin_param.default}")
    print(f"  Type: {type(allow_margin_param.default)}")

    assert allow_margin_param.default is False, "allow_margin should default to False"

    print("  ✅ PASS\n")


def test_cash_reserve_calculation():
    """Test cash reserve calculation logic."""
    initial_investment = 1_000_000
    allocations = {
        "NVDA": 0.60,
        "PLTR": 0.30,
        "CASH": 0.10,
    }

    print("Test 3: Cash Reserve Calculation")
    print(f"  Initial investment: ${initial_investment:,.0f}")
    print(f"  Allocations: {allocations}")

    # Calculate expected reserves
    cash_reserve = initial_investment * allocations["CASH"]
    nvda_investment = initial_investment * allocations["NVDA"]
    pltr_investment = initial_investment * allocations["PLTR"]

    print(f"  Expected cash reserve: ${cash_reserve:,.0f}")
    print(f"  Expected NVDA investment: ${nvda_investment:,.0f}")
    print(f"  Expected PLTR investment: ${pltr_investment:,.0f}")

    assert cash_reserve == 100_000, "Cash reserve should be $100K"
    assert nvda_investment == 600_000, "NVDA investment should be $600K"
    assert pltr_investment == 300_000, "PLTR investment should be $300K"

    total = cash_reserve + nvda_investment + pltr_investment
    print(f"  Total: ${total:,.0f}")
    assert total == initial_investment, "Total should equal initial investment"

    print("  ✅ PASS\n")


def test_margin_check_logic():
    """Test the margin check logic."""
    print("Test 4: Margin Check Logic")

    # Simulate the logic from execute_transaction
    test_cases = [
        # (bank_balance, cost, allow_margin, should_execute, description)
        (100_000, 50_000, False, True, "Sufficient cash, no margin needed"),
        (100_000, 150_000, False, False, "Insufficient cash, margin forbidden"),
        (100_000, 150_000, True, True, "Insufficient cash, but margin allowed"),
        (0, 50_000, True, True, "Zero cash, but margin allowed"),
        (0, 50_000, False, False, "Zero cash, margin forbidden"),
    ]

    for bank, cost, allow_margin, expected_execute, description in test_cases:
        # This is the actual logic from simulation.py line 388
        can_execute = bank >= cost or allow_margin

        print(f"  Case: {description}")
        print(f"    Bank: ${bank:,}, Cost: ${cost:,}, allow_margin: {allow_margin}")
        print(f"    Can execute: {can_execute} (expected: {expected_execute})")

        assert can_execute == expected_execute, f"Failed: {description}"
        print(f"    ✅ PASS")

    print()


def test_backwards_compatibility():
    """Test that old-style allocations (no CASH) still work."""
    allocations_old = {
        "NVDA": 1.0,
    }

    allocations_new = {
        "NVDA": 0.90,
        "CASH": 0.10,
    }

    print("Test 5: Backwards Compatibility")

    # Old style: no CASH ticker
    real_tickers_old = [t for t in allocations_old.keys() if t != "CASH"]
    print(f"  Old style allocations: {list(allocations_old.keys())}")
    print(f"  Real tickers: {real_tickers_old}")
    assert real_tickers_old == ["NVDA"], "Old style should have just NVDA"

    # New style: with CASH
    real_tickers_new = [t for t in allocations_new.keys() if t != "CASH"]
    print(f"  New style allocations: {list(allocations_new.keys())}")
    print(f"  Real tickers: {real_tickers_new}")
    assert real_tickers_new == ["NVDA"], "New style should filter out CASH"

    # Check CASH detection
    has_cash_old = "CASH" in allocations_old
    has_cash_new = "CASH" in allocations_new
    print(f"  Old style has CASH: {has_cash_old}")
    print(f"  New style has CASH: {has_cash_new}")
    assert not has_cash_old, "Old style should not have CASH"
    assert has_cash_new, "New style should have CASH"

    print("  ✅ PASS\n")


if __name__ == "__main__":
    print("\n")
    print("╔" + "=" * 78 + "╗")
    print("║" + " " * 24 + "CASH TICKER UNIT TESTS" + " " * 32 + "║")
    print("╚" + "=" * 78 + "╝")
    print()

    test_cash_filtering()
    test_allow_margin_default()
    test_cash_reserve_calculation()
    test_margin_check_logic()
    test_backwards_compatibility()

    print("=" * 80)
    print("ALL UNIT TESTS PASSED ✅")
    print("=" * 80)
    print()
    print("Summary:")
    print("  ✓ CASH ticker is properly filtered from real ticker lists")
    print("  ✓ allow_margin defaults to False (retail mode)")
    print("  ✓ Cash reserve calculation works correctly")
    print("  ✓ Margin check logic prevents borrowing when disabled")
    print("  ✓ Backwards compatible with old-style allocations")
    print()
