"""Test that multi-bracket gaps create multiple separate stack entries."""

from datetime import date
import pandas as pd
from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm

def test_two_bracket_gap_creates_two_stack_entries():
    """Verify that gapping down 2 brackets creates 2 separate stack entries."""
    
    # Create algorithm with buyback enabled
    # Using 9.15% rebalance, 50% profit sharing (standard params)
    algo = SyntheticDividendAlgorithm(
        rebalance_size=9.15/100.0,
        profit_sharing=50/100.0,
        buyback_enabled=True
    )
    
    # Initial purchase at $100
    algo.on_new_holdings(holdings=100, current_price=100.0)
    
    # Verify initial state
    assert len(algo.buyback_stack) == 0, "Stack should start empty"
    
    # Day 1: Gap down where price opens LOW and stays there
    # We start at $100, and want to gap down to trigger 2 buy brackets
    # With 9.15% rebalance:
    #   First bracket: $100 / 1.0915 = $91.62
    #   After fill at $91.62, next bracket: $91.62 / 1.0915 = $83.95  
    #   After fill at $83.95, next bracket: $83.95 / 1.0915 = $76.91
    #
    # To trigger exactly 2 brackets: gap to between $83.95 and $91.62
    # Let's use $86 (triggers $91.62 bracket, but not yet the $83.95 bracket on second iteration)
    #
    # Actually, the issue is that if we set High=86, it won't gap enough.
    # We need the gap itself to cross multiple brackets.
    #
    # The real scenario: overnight gap down from $100 to $86
    # In practice, this would show as: previous_close=$100, open=$86, low=$86, high=$86
    # But we're only evaluating one day at a time.
    #
    # Let's think differently: we want to test the ITERATION logic.
    # If open=$86, then the order at $91.62 triggers immediately.
    # After that fill, new orders are placed based on $86.
    # New buy order would be at $86 / 1.0915 = $78.79
    # For that to ALSO trigger, we need low to reach $78.79
    #
    # So: Open=$86 (triggers first bracket), Low=$78 (triggers second bracket after first executes)
    price_data = pd.Series({
        'Open': 86.0,   # Gaps down from $100, triggers first buy bracket
        'High': 90.0,   # Doesn't reach sell brackets
        'Low': 78.0,    # Drops further, should trigger second buy bracket
        'Close': 80.0,
    })
    
    txns = algo.on_day(
        date_=date(2024, 1, 2),
        price_row=price_data,
        holdings=100,
        bank=10000.0,
        history=pd.DataFrame()
    )
    
    # Should have executed 2 buy transactions
    buy_txns = [t for t in txns if t.action == "BUY"]
    print(f"Executed {len(buy_txns)} buy transactions:")
    total_buy_qty = 0
    for i, txn in enumerate(buy_txns, 1):
        print(f"  Buy #{i}: qty={txn.qty}, notes={txn.notes}")
        total_buy_qty += txn.qty
    print(f"Total buy quantity: {total_buy_qty}")
    
    # Check if there were any sells that unwound the stack
    sell_txns = [t for t in txns if t.action == "SELL"]
    total_sell_qty = 0
    if sell_txns:
        print(f"\nExecuted {len(sell_txns)} sell transactions:")
        for i, txn in enumerate(sell_txns, 1):
            print(f"  Sell #{i}: qty={txn.qty}, notes={txn.notes}")
            total_sell_qty += txn.qty
        print(f"Total sell quantity: {total_sell_qty}")
    
    # Check buyback stack
    print(f"\nBuyback stack has {len(algo.buyback_stack)} entries:")
    for i, (price, qty) in enumerate(algo.buyback_stack, 1):
        print(f"  Entry #{i}: price=${price:.2f}, qty={qty}")
    
    # VERIFY: Should have 2 separate stack entries (not 1 combined)
    assert len(algo.buyback_stack) == 2, \
        f"Expected 2 stack entries for 2-bracket gap, got {len(algo.buyback_stack)}"
    
    # VERIFY: Each entry should have the "normal" quantity
    # (not one entry with double quantity)
    qty1 = algo.buyback_stack[0][1]
    qty2 = algo.buyback_stack[1][1]
    
    print(f"\nStack entry quantities: {qty1} and {qty2}")
    assert qty1 == qty2, f"Both entries should have same qty, got {qty1} and {qty2}"
    
    # VERIFY: Prices should be different (one per bracket)
    price1 = algo.buyback_stack[0][0]
    price2 = algo.buyback_stack[1][0]
    
    print(f"Stack entry prices: ${price1:.2f} and ${price2:.2f}")
    assert price1 != price2, "Entries should have different prices"
    assert abs(price1 - price2) > 0.5, "Prices should be ~1 bracket apart"
    
    print("\n✅ CONFIRMED: Multi-bracket gap creates multiple separate stack entries!")
    print("   This ensures EXACT symmetry when unwinding.")

if __name__ == "__main__":
    test_two_bracket_gap_creates_two_stack_entries()
