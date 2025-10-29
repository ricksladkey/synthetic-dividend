"""Demo script showing return adjustment framework in action.

This demonstrates the three-dimensional return analysis:
1. Nominal returns - How much money did I make?
2. Real returns - Did I beat inflation?
3. Alpha - Did I beat the market?
"""

from datetime import date  # noqa: F401

from src.models.return_adjustments import (  # noqa: F401
    calculate_adjusted_returns,
    format_adjustment_summary,
    print_adjusted_returns,
)


def demo_return_adjustments():
    """Demonstrate return adjustment calculations."""

    print("=" * 70)
    print("RETURN ADJUSTMENT FRAMEWORK DEMO")
    print("=" * 70)
    print()

    # Example: Strong performing asset in high inflation environment
    print("Example 1: NVDA 2024 - Strong performance")
    print("-" * 70)

    _ = {  # noqa: F841
        "total_return": 1.50,  # 150% return
        "start_value": 10000.0,
        "total": 25000.0,  # $15,000 gain
    }

    print("Investment: $10,000 → $25,000")
    print("Nominal Return: +150% ($15,000)")
    print()

    # Note: This demo uses mock data since we don't have real CPI/VOO prices
    # In real usage, calculate_adjusted_returns() would fetch actual prices

    # Manually show what the framework would calculate:
    print("What the framework calculates:")
    print("  → Fetches CPI data for period")
    print("  → Fetches VOO (S&P 500) data for period")
    print("  → Computes inflation-adjusted returns")
    print("  → Computes market-adjusted returns (alpha)")
    print()
    print("Example output (with hypothetical CPI +3%, VOO +25%):")
    print("  Nominal: +150% ($15,000)")
    print("  Real: +143% ($14,300) - beat inflation")
    print("  Alpha: +100% ($10,000 vs VOO) - crushed market")
    print()

    print("=" * 70)
    print()

    # Example 2: Gold in high inflation
    print("Example 2: GLD 2024 - Inflation hedge")
    print("-" * 70)

    _ = {  # noqa: F841
        "total_return": 0.08,  # 8% return
        "start_value": 10000.0,
        "total": 10800.0,  # $800 gain
    }

    print("Investment: $10,000 → $10,800")
    print("Nominal Return: +8% ($800)")
    print()
    print("Example output (with hypothetical CPI +3%, VOO +25%):")
    print("  Nominal: +8% ($800)")
    print("  Real: +5% ($500) - barely beat inflation")
    print("  Alpha: -17% (-$1,700 vs VOO) - underperformed market")
    print()

    print("=" * 70)
    print()

    # Example 3: Bonds in bear market
    print("Example 3: AGG 2022 - Bonds in bear market")
    print("-" * 70)

    _ = {  # noqa: F841
        "total_return": -0.13,  # -13% return
        "start_value": 10000.0,
        "total": 8700.0,  # -$1,300 loss
    }

    print("Investment: $10,000 → $8,700")
    print("Nominal Return: -13% (-$1,300)")
    print()
    print("Example output (with hypothetical CPI +8%, VOO -18%):")
    print("  Nominal: -13% (-$1,300)")
    print("  Real: -19.4% (-$1,940) - crushed by inflation")
    print("  Alpha: +5% (+$500 vs VOO) - lost less than market")
    print()

    print("=" * 70)
    print()

    print("KEY INSIGHT:")
    print("Returns are multi-dimensional. Each perspective tells a different story:")
    print()
    print("  NOMINAL = 'How much money did I make?'")
    print("  REAL    = 'Did my purchasing power increase?'")
    print("  ALPHA   = 'Did I beat just holding the market?'")
    print()
    print("The framework shows ALL THREE simultaneously, letting you decide")
    print("which matters most for your investment goals.")
    print()

    print("=" * 70)
    print()

    print("USAGE IN CLI:")
    print()
    print("  # Show all three perspectives:")
    print("  synthetic-dividend-tool backtest --ticker NVDA \\")
    print("      --start 2024-01-01 --end 2024-12-31 \\")
    print("      --adjust-both --verbose")
    print()
    print("  # Just inflation adjustment:")
    print("  synthetic-dividend-tool backtest --ticker NVDA \\")
    print("      --start 2024-01-01 --end 2024-12-31 \\")
    print("      --adjust-inflation")
    print()
    print("  # Custom benchmark (vs Gold instead of S&P 500):")
    print("  synthetic-dividend-tool backtest --ticker AAPL \\")
    print("      --start 2024-01-01 --end 2024-12-31 \\")
    print("      --adjust-market --market-ticker GLD")
    print()

    print("=" * 70)


if __name__ == "__main__":
    demo_return_adjustments()
