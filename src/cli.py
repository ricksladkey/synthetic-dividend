#!/usr/bin/env python3
"""Unified command-line interface for the Synthetic Dividend toolkit.

This is the main entry point for all CLI operations, providing a unified
interface that works across platforms (Windows, macOS, Linux).

Usage:
    python -m src.cli [command] [options]

Available commands:
    backtest     - Run a single backtest simulation
    compare      - Run batch comparison of multiple strategies
    research     - Run research experiments (optimal rebalancing, volatility alpha)
    test         - Run the test suite
    analyze      - Run analysis tools (volatility alpha, etc.)
    gui          - Launch the graphical user interface

Examples:
    python -m src.cli backtest NVDA 2024-10-22 2025-10-22 sd-9.05,50
    python -m src.cli compare NVDA 2024-10-22 2025-10-22 buy-and-hold sd-9.05,50
    python -m src.cli research volatility-alpha --ticker NVDA --start 2023-01-01 --end 2023-12-31
    python -m src.cli test
    python -m src.cli analyze volatility-alpha --ticker NVDA --start 2023-01-01 --end 2023-12-31
"""

import argparse
import sys
from typing import List, Optional


def list_portfolios() -> None:
    """Print all available named portfolios with their allocations."""
    print("=" * 80)
    print("AVAILABLE NAMED PORTFOLIOS")
    print("=" * 80)
    print()
    print("Use --allocations with a portfolio name instead of JSON for convenience.")
    print()

    portfolios = [
        (
            "CLASSIC PORTFOLIOS",
            [
                ("classic", "60% VOO, 40% BIL", "Traditional 60/40 stocks/bonds"),
                ("classic-70,30", "70% VOO, 30% BIL", "More aggressive allocation"),
                ("classic-80,20", "80% VOO, 20% BIL", "High equity allocation"),
            ],
        ),
        (
            "CRYPTO PORTFOLIOS",
            [
                (
                    "classic-plus-crypto",
                    "60% VOO, 30% BIL, 10% BTC-USD",
                    "60/30/10 validation portfolio",
                ),
                (
                    "classic-plus-crypto-50,30,20",
                    "50% VOO, 30% BIL, 20% BTC-USD",
                    "Higher crypto allocation",
                ),
                (
                    "crypto-heavy",
                    "40% BTC-USD, 20% ETH-USD, 30% VOO, 10% BIL",
                    "Crypto-focused portfolio",
                ),
            ],
        ),
        (
            "FAMOUS PORTFOLIOS",
            [
                ("buffet", "90% VOO, 10% BIL", "Warren Buffett recommendation"),
                ("buffet-95,5", "95% VOO, 5% BIL", "More aggressive Buffett"),
                (
                    "all-weather",
                    "40% VOO, 15% TLT, 15% IEF, 7.5% GLD, 7.5% DBC, 15% BIL",
                    "Ray Dalio's All Weather",
                ),
                ("three-fund", "40% VTI, 30% VXUS, 30% BND", "Bogleheads three-fund"),
                (
                    "golden-butterfly",
                    "20% VOO, 20% SHY, 20% TLT, 20% GLD, 20% BIL",
                    "Tyler's Golden Butterfly",
                ),
            ],
        ),
        (
            "GROWTH PORTFOLIOS",
            [
                ("tech-growth", "60% QQQ, 40% VOO", "Tech-heavy growth"),
                ("tech-growth-70,30", "70% QQQ, 30% VOO", "More aggressive tech"),
                ("high-growth", "30% NVDA, 40% QQQ, 30% VOO", "High-growth tech"),
            ],
        ),
    ]

    for category, portfolio_list in portfolios:
        print(category)
        print("-" * 80)
        for name, allocation, description in portfolio_list:
            print(f"  {name:<35} {description}")
            print(f"    {allocation}")
        print()

    print("CUSTOM PARAMETERS")
    print("-" * 80)
    print("  Many portfolios support custom parameters:")
    print()
    print("    classic-X,Y        -> X% VOO, Y% BIL")
    print("    classic-plus-crypto-X,Y,Z  -> X% VOO, Y% BIL, Z% BTC-USD")
    print("    buffet-X,Y         -> X% VOO, Y% BIL")
    print("    tech-growth-X,Y    -> X% QQQ, Y% VOO")
    print()

    print("EXAMPLES")
    print("-" * 80)
    print("  # Use named portfolio")
    print("  --allocations classic")
    print()
    print("  # Use named portfolio with custom parameters")
    print("  --allocations buffet-95,5")
    print()
    print("  # Use custom JSON allocations")
    print('  --allocations \'{"NVDA": 0.4, "VOO": 0.6}\'')
    print()
    print("=" * 80)


def list_algorithms() -> None:
    """Print all available portfolio algorithms with detailed descriptions."""
    print("=" * 80)
    print("AVAILABLE PORTFOLIO ALGORITHMS")
    print("=" * 80)
    print()
    print("NOTE: To see available named portfolios (classic, buffet, etc.),")
    print("      use --list-portfolios")
    print()

    print("PORTFOLIO-LEVEL ALGORITHMS")
    print("-" * 80)
    print("These algorithms manage the entire portfolio as a unit, rebalancing to")
    print("maintain target allocations.")
    print()

    algorithms = [
        (
            "quarterly-rebalance",
            "Rebalance quarterly (Mar/Jun/Sep/Dec)",
            "Traditional 60/40 portfolios",
        ),
        ("quarterly-rebalance:2,5,8,11", "Custom rebalance months", "Rebalance in Feb/May/Aug/Nov"),
        ("monthly-rebalance", "Rebalance every month", "More aggressive rebalancing"),
        (
            "annual-rebalance",
            "Rebalance once per year (December)",
            "Tax-efficient, minimal trading",
        ),
    ]

    for name, desc, use_case in algorithms:
        print(f"  {name:<35} {desc}")
        print(f"    Use case: {use_case}")
        print()

    print("PER-ASSET ALGORITHMS")
    print("-" * 80)
    print("These algorithms apply to individual assets with a shared cash pool,")
    print("allowing different strategies per asset.")
    print()

    per_asset_algos = [
        ("per-asset:sd4", "18.92%", "High volatility (BTC, MSTR)", "Apply SD4 to all assets"),
        ("per-asset:sd6", "12.25%", "Growth stocks (NVDA, GOOG)", "Apply SD6 to all assets"),
        ("per-asset:sd8", "9.05%", "Tech stocks, indices", "Apply SD8 to all assets (balanced)"),
        ("per-asset:sd10", "7.18%", "Indices, low-vol stocks", "Apply SD10 to all assets"),
        ("per-asset:sd8,75", "9.05%", "High cash extraction", "SD8 with 75% profit sharing"),
        ("per-asset:buy-and-hold", "N/A", "Baseline comparison", "Buy and hold all assets"),
    ]

    for name, trigger, best_for, desc in per_asset_algos:
        print(f"  {name:<35} {desc}")
        print(f"    Trigger: {trigger:<10} Best for: {best_for}")
        print()

    print("AUTO-SELECTION ALGORITHM (RECOMMENDED)")
    print("-" * 80)
    print("  auto")
    print("    Intelligently selects optimal per-asset strategy based on volatility:")
    print()
    print("    Asset Classification:")
    print("      - Crypto (BTC-USD, ETH-USD)      -> SD4  (18.92% trigger)")
    print("      - High-growth tech (NVDA, PLTR)  -> SD6  (12.25% trigger)")
    print("      - Indices (VOO, SPY, QQQ)        -> SD8  (9.05% trigger)")
    print("      - Bonds/cash (BIL, SHY, AGG)     -> buy-and-hold")
    print("      - Unknown tickers                -> SD10 (7.18% trigger, conservative)")
    print()
    print("    This is the DEFAULT and RECOMMENDED algorithm for portfolio backtests.")
    print()

    print("PROFIT SHARING GUIDE")
    print("-" * 80)
    print("  Profit sharing controls balance between cash flow and position growth:")
    print()
    print("    0%    - 100% accumulation (buy MORE on strength)")
    print("    25%   - Mostly growth (3:1 growth to cash)")
    print("    50%   - BALANCED (default, equal growth and cash)")
    print("    75%   - High income (3:1 cash to growth)")
    print("    100%  - Maximum income (all profits to cash)")
    print("    >100% - De-risking (reduce position)")
    print()

    print("EXAMPLES")
    print("-" * 80)
    print("  # Auto algorithm (recommended)")
    print("  --algo auto")
    print()
    print("  # Quarterly rebalancing (traditional 60/40)")
    print("  --algo quarterly-rebalance")
    print()
    print("  # Apply SD8 to all assets")
    print('  --algo "per-asset:sd8"')
    print()
    print("  # SD6 with 75% profit sharing (aggressive cash extraction)")
    print('  --algo "per-asset:sd6,75"')
    print()
    print("=" * 80)


def test_command(args: List[str]) -> int:
    """Run the test suite."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest", "-v", "--cov=src", "--cov-report=term-missing"]
    if args:
        cmd.extend(args)
    return subprocess.call(cmd)


def test_sd_command(args: List[str]) -> int:
    """Test SD strategy on NVDA."""
    from src.run_model import main as backtest_main

    return backtest_main(["NVDA", "10/22/2024", "10/22/2025", "sd-9.05,50"] + args)


def test_buy_and_hold_command(args: List[str]) -> int:
    """Test buy-and-hold strategy on NVDA."""
    from src.run_model import main as backtest_main

    return backtest_main(["NVDA", "10/22/2024", "10/22/2025", "buy-and-hold"] + args)


def test_batch_comparison_command(args: List[str]) -> int:
    """Run batch comparison test."""
    from src.compare.batch_comparison import main as compare_main

    return compare_main(["NVDA", "10/22/2024", "10/22/2025", "buy-and-hold", "sd-9.05,50"] + args)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    if argv is None:
        argv = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Synthetic Dividend Toolkit - Unified CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    # Add top-level list flags
    parser.add_argument(
        "--list-algorithms",
        action="store_true",
        help="List all available portfolio algorithms with descriptions",
    )
    parser.add_argument(
        "--list-portfolios",
        action="store_true",
        help="List all available named portfolios with allocations",
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["backtest", "compare", "research", "test", "analyze", "gui"],
        help="Command to execute",
    )

    # Parse arguments
    args, remaining_args = parser.parse_known_args(argv)

    # Handle list commands
    if args.list_algorithms:
        list_algorithms()
        return 0
    elif args.list_portfolios:
        list_portfolios()
        return 0

    # Parse just the command first
    if not args.command:
        parser.print_help()
        return 1

    command = args.command

    # Route to appropriate module based on command
    if command == "backtest":
        from src.run_model import main as backtest_main

        return backtest_main(remaining_args)
    elif command == "compare":
        from src.compare.batch_comparison import main as compare_main

        return compare_main(remaining_args)
    elif command == "research":
        # Handle subcommands for research
        if remaining_args and remaining_args[0] == "volatility-alpha":
            from src.research.volatility_alpha import main as vol_alpha_main

            return vol_alpha_main(remaining_args[1:])
        elif remaining_args and remaining_args[0] == "optimal-rebalancing":
            from src.research.optimal_rebalancing import main as opt_rebal_main

            return opt_rebal_main(remaining_args[1:])
        else:
            print("Research subcommands: volatility-alpha, optimal-rebalancing")
            return 1
    elif command == "analyze":
        # Handle subcommands for analysis
        if remaining_args and remaining_args[0] == "volatility-alpha":
            from src.research.volatility_alpha import main as vol_alpha_main

            return vol_alpha_main(remaining_args[1:])
        else:
            print("Analysis subcommands: volatility-alpha")
            return 1
    elif command == "test":
        import subprocess

        # Run pytest with coverage
        cmd = [sys.executable, "-m", "pytest", "-v", "--cov=src", "--cov-report=term-missing"]
        if remaining_args:
            cmd.extend(remaining_args)
        return subprocess.call(cmd)
    elif command == "gui":
        from src.main import main as gui_main

        return gui_main(remaining_args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
