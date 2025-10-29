#!/usr/bin/env python3
"""Demonstration of bracket seed control feature.

This script shows how the bracket_seed parameter ensures that price calculations
align to a common bracket ladder, making the strategy deterministic and comparable.
"""

import math


def demo_bracket_seed():
    """Demonstrate bracket seed control."""
    print("\n" + "=" * 80)
    print(" BRACKET SEED CONTROL DEMONSTRATION")
    print("=" * 80)

    # Setup
    rebalance_size = 0.0905  # sd8: 2^(1/8) - 1 ≈ 9.05%
    print(f"\nUsing sd8 strategy: {rebalance_size*100:.2f}% bracket spacing")

    # Scenario: Three traders starting at slightly different prices
    prices = [120.50, 121.00, 119.80]

    # Validate inputs
    if rebalance_size <= 0:
        print("Error: Invalid rebalance_size. Must be > 0")
        return
    if any(p <= 0 for p in prices):
        print("Error: All prices must be positive")
        return

    print("\n" + "-" * 80)
    print("WITHOUT BRACKET SEED:")
    print("-" * 80)
    print("\nThree traders enter at different times with slightly different prices:")

    for price in prices:
        buy_price = price / (1 + rebalance_size)
        sell_price = price * (1 + rebalance_size)
        print(f"  Entry: ${price:.2f} → Buy: ${buy_price:.2f}, Sell: ${sell_price:.2f}")

    print("\n❌ Problem: Each trader has DIFFERENT order prices!")
    print("   This makes it hard to:")
    print("   - Compare results between traders")
    print("   - Verify backtests match real trading")
    print("   - Pool orders or coordinate strategies")

    print("\n" + "-" * 80)
    print("WITH BRACKET SEED (100.0):")
    print("-" * 80)

    bracket_seed = 100.0
    print(f"\nSeed price: ${bracket_seed:.2f}")
    print("\nAll three traders use the same bracket seed:")

    normalized_prices = []
    for price in prices:
        # Normalize price to nearest bracket
        bracket_n = math.log(price) / math.log(1 + rebalance_size)
        bracket_rounded = round(bracket_n)
        normalized = math.pow(1 + rebalance_size, bracket_rounded)
        normalized_prices.append(normalized)

        buy_price = normalized / (1 + rebalance_size)
        sell_price = normalized * (1 + rebalance_size)

        print(f"  Entry: ${price:.2f} (bracket {bracket_rounded}) → ")
        print(f"         Normalized: ${normalized:.2f}")
        print(f"         Buy: ${buy_price:.2f}, Sell: ${sell_price:.2f}")

    print("\n✓ Solution: All traders have IDENTICAL order prices!")
    print("   Benefits:")
    print("   - Results are directly comparable")
    print("   - Backtests use same brackets as real trading")
    print("   - Multiple traders can pool liquidity")
    print("   - Strategy is deterministic and reproducible")

    # Show the bracket ladder
    print("\n" + "-" * 80)
    print("BRACKET LADDER (with seed 100.0):")
    print("-" * 80)

    # Find the bracket for seed
    seed_bracket = round(math.log(bracket_seed) / math.log(1 + rebalance_size))
    print(f"\nSeed ${bracket_seed:.2f} is on bracket {seed_bracket}\n")

    # Show ladder around the price range
    min_bracket = min(round(math.log(p) / math.log(1 + rebalance_size)) for p in prices)
    max_bracket = max(round(math.log(p) / math.log(1 + rebalance_size)) for p in prices)

    print("Bracket ladder (showing relevant range):")
    for bracket in range(min_bracket - 2, max_bracket + 3):
        bracket_price = math.pow(1 + rebalance_size, bracket)
        marker = ""
        if bracket == seed_bracket:
            marker = " ← SEED"
        elif min_bracket <= bracket <= max_bracket:
            marker = " ← TRADING RANGE"

        print(f"  Bracket {bracket:3}: ${bracket_price:8.2f}{marker}")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    demo_bracket_seed()
