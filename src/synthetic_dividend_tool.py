"""
Synthetic Dividend Tool - Unified CLI Interface

A swiss army knife tool that provides a single entry point for all
synthetic dividend operations.

Usage:
    synthetic-dividend-tool <command> [options]

Commands:
    run                   Run backtests, research, and comparisons
    analyze               Analyze results and generate reports
    dump                  Dump transaction history without visualization
    order                 Calculate order recommendations
    test                  Run test suite

Use 'synthetic-dividend-tool <command> --help' for command-specific options.
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


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""

    parser = argparse.ArgumentParser(
        prog="synthetic-dividend-tool",
        description="Synthetic Dividend Algorithm - Unified CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # List all available portfolio algorithms
    synthetic-dividend-tool --list-algorithms

    # Run backtest on NVDA
    synthetic-dividend-tool run backtest --ticker NVDA --start 2023-01-01 --end 2024-01-01

    # Run portfolio backtest with auto algorithm (recommended)
    synthetic-dividend-tool run portfolio --allocations '{"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}' --algo auto --start 2019-01-01 --end 2024-12-31

    # Backtest with market adjustment (vs VOO)
    synthetic-dividend-tool run backtest --ticker GLD --start 2024-01-01 --end 2024-12-31 --adjust-market --verbose

    # Complete return analysis (nominal + real + alpha)
    synthetic-dividend-tool run backtest --ticker AAPL --start 2024-01-01 --end 2024-12-31 --adjust-both --verbose

    # Run optimal rebalancing research
    synthetic-dividend-tool run research optimal-rebalancing --output results.csv

    # Compare algorithms
    synthetic-dividend-tool run compare algorithms --ticker SPY --start 2023-01-01 --end 2024-01-01

    # Batch comparison across assets
    synthetic-dividend-tool run compare batch --tickers NVDA AAPL GLD --strategies sd8 sd16 --start 2024-01-01 --end 2025-01-01

    # Auto-analyze volatility and suggest optimal SD
    synthetic-dividend-tool analyze volatility-alpha --ticker GLD --start 2024-01-01 --end 2025-01-01

    # Analyze gap bonus
    synthetic-dividend-tool analyze gap-bonus --input research_phase1_1year_core.csv

    # Get daily candle data for NVDA
    synthetic-dividend-tool run ticker --ticker NVDA --start 2024-01-01 --end 2024-12-31

    # Get weekly aggregated candle data for SPY
    synthetic-dividend-tool run ticker --ticker SPY --start 2023-01-01 --end 2024-12-31 --interval weekly

    # Get monthly candle data and save to file
    synthetic-dividend-tool run ticker --ticker AAPL --start 2020-01-01 --end 2024-12-31 --interval monthly --output apple_monthly.csv

    # Run tests
    synthetic-dividend-tool test

    # Calculate orders
    synthetic-dividend-tool order --ticker NVDA --holdings 1000

    # Dump transaction history without visualization
    synthetic-dividend-tool dump --ticker NVDA --start 2024-01-01 --end 2025-01-01 --output nvda_transactions.txt

For detailed help on any command:
    synthetic-dividend-tool <command> --help
        """,
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

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # ========================================================================
    # RUN command (unified backtests, research, and comparisons)
    # ========================================================================
    run_parser = subparsers.add_parser(
        "run",
        help="Run backtests, research, and comparisons",
        description="Execute backtests, research studies, and comparison analyses",
    )
    run_subparsers = run_parser.add_subparsers(dest="run_type", help="Run type")

    # ========================================================================
    # run backtest
    # ========================================================================
    run_backtest_parser = run_subparsers.add_parser(
        "backtest",
        help="Run backtest on a single asset",
        description="Execute backtest using synthetic dividend algorithm",
    )
    run_backtest_parser.add_argument("--ticker", required=True, help="Asset ticker symbol")
    run_backtest_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    run_backtest_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    run_backtest_parser.add_argument(
        "--initial-investment",
        type=float,
        default=1_000_000,
        help="Initial investment amount (default: 1,000,000)",
    )
    run_backtest_parser.add_argument(
        "--initial-qty",
        type=int,
        help="Initial quantity in shares (alternative to --initial-investment)",
    )
    run_backtest_parser.add_argument(
        "--algorithm",
        default="sd8",
        help='Algorithm name (e.g., "sd8", "sd4-75", "buy-and-hold", default: "sd8")',
    )
    run_backtest_parser.add_argument("--output", help="Output file for results (CSV)")
    run_backtest_parser.add_argument(
        "--pdf-report", help="Generate PDF report (provide output path)"
    )
    run_backtest_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # Return adjustment options
    run_backtest_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Show inflation-adjusted (real) returns"
    )
    run_backtest_parser.add_argument(
        "--adjust-market", action="store_true", help="Show market-adjusted returns (alpha)"
    )
    run_backtest_parser.add_argument(
        "--adjust-both", action="store_true", help="Show both inflation and market adjustments"
    )
    run_backtest_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    run_backtest_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # ========================================================================
    # run portfolio
    # ========================================================================
    run_portfolio_parser = run_subparsers.add_parser(
        "portfolio",
        help="Run portfolio backtests",
        description="Execute multi-asset portfolio backtests with algorithmic strategies",
    )
    run_portfolio_parser.add_argument(
        "--allocations",
        required=True,
        help='Asset allocations as JSON string, e.g., \'{"NVDA": 0.4, "VOO": 0.6}\'',
    )
    run_portfolio_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    run_portfolio_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    run_portfolio_parser.add_argument(
        "--initial-investment",
        type=float,
        default=1_000_000,
        help="Initial investment amount (default: 1,000,000)",
    )
    run_portfolio_parser.add_argument(
        "--algo",
        default="auto",
        help='Algorithm to use: "auto" (default), "quarterly-rebalance", "per-asset:sd8", etc.',
    )
    run_portfolio_parser.add_argument(
        "--cash-interest-rate",
        type=float,
        default=0.0,
        help="Annual interest rate on cash reserves (default: 0.0, typical: 5.0 for money market)",
    )
    run_portfolio_parser.add_argument("--output", help="Output file for detailed results (JSON)")
    run_portfolio_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # ========================================================================
    # run research
    # ========================================================================
    run_research_parser = run_subparsers.add_parser(
        "research", help="Run research studies", description="Execute various research analyses"
    )
    run_research_subparsers = run_research_parser.add_subparsers(
        dest="research_type", help="Research type"
    )

    # run research optimal-rebalancing
    run_optimal_parser = run_research_subparsers.add_parser(
        "optimal-rebalancing", help="Find optimal rebalancing parameters"
    )
    run_optimal_parser.add_argument(
        "--start", default="2023-10-23", help="Start date (default: 2023-10-23)"
    )
    run_optimal_parser.add_argument(
        "--end", default="2024-10-23", help="End date (default: 2024-10-23)"
    )
    run_optimal_parser.add_argument(
        "--profit-pct", type=float, default=50.0, help="Profit sharing %% (default: 50)"
    )
    run_optimal_parser.add_argument(
        "--initial-qty", type=int, default=10000, help="Initial quantity (default: 10000)"
    )
    run_optimal_parser.add_argument(
        "--ticker", help="Specific ticker (optional, tests all if omitted)"
    )
    run_optimal_parser.add_argument("--asset-class", help="Specific asset class (optional)")
    run_optimal_parser.add_argument("--output", required=True, help="Output CSV file")

    # Return adjustment options
    run_optimal_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    run_optimal_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    run_optimal_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    run_optimal_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    run_optimal_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # run research volatility-alpha
    run_volatility_parser = run_research_subparsers.add_parser(
        "volatility-alpha", help="Analyze volatility alpha across assets"
    )
    run_volatility_parser.add_argument("--start", default="2023-10-23", help="Start date")
    run_volatility_parser.add_argument("--end", default="2024-10-23", help="End date")
    run_volatility_parser.add_argument("--output", required=True, help="Output CSV file")

    # Return adjustment options
    run_volatility_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    run_volatility_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    run_volatility_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    run_volatility_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    run_volatility_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # run research asset-classes
    run_asset_class_parser = run_research_subparsers.add_parser(
        "asset-classes", help="Analyze performance by asset class"
    )
    run_asset_class_parser.add_argument("--start", required=True, help="Start date")
    run_asset_class_parser.add_argument("--end", required=True, help="End date")
    run_asset_class_parser.add_argument("--output", required=True, help="Output CSV file")

    # Return adjustment options
    run_asset_class_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    run_asset_class_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    run_asset_class_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    run_asset_class_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    run_asset_class_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # ========================================================================
    # run compare
    # ========================================================================
    run_compare_parser = run_subparsers.add_parser(
        "compare", help="Compare strategies or algorithms", description="Run comparison analyses"
    )
    run_compare_subparsers = run_compare_parser.add_subparsers(
        dest="compare_type", help="Comparison type"
    )

    # run compare algorithms
    run_algo_compare_parser = run_compare_subparsers.add_parser(
        "algorithms", help="Compare different algorithm configurations"
    )
    run_algo_compare_parser.add_argument("--ticker", required=True, help="Asset ticker")
    run_algo_compare_parser.add_argument("--start", required=True, help="Start date")
    run_algo_compare_parser.add_argument("--end", required=True, help="End date")
    run_algo_compare_parser.add_argument("--output", help="Output file")

    # run compare strategies
    run_strategy_compare_parser = run_compare_subparsers.add_parser(
        "strategies", help="Compare different trading strategies"
    )
    run_strategy_compare_parser.add_argument("--ticker", required=True, help="Asset ticker")
    run_strategy_compare_parser.add_argument("--start", required=True, help="Start date")
    run_strategy_compare_parser.add_argument("--end", required=True, help="End date")
    run_strategy_compare_parser.add_argument("--output", help="Output file")

    # run compare batch
    run_batch_compare_parser = run_compare_subparsers.add_parser(
        "batch", help="Run batch comparison across multiple assets/strategies"
    )
    run_batch_compare_parser.add_argument(
        "--tickers", nargs="+", required=True, help="List of tickers"
    )
    run_batch_compare_parser.add_argument(
        "--strategies", nargs="+", required=True, help="List of strategies (e.g., sd8 sd16)"
    )
    run_batch_compare_parser.add_argument("--start", required=True, help="Start date")
    run_batch_compare_parser.add_argument("--end", required=True, help="End date")
    run_batch_compare_parser.add_argument("--output", help="Output CSV file")

    # Return adjustment options
    run_batch_compare_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    run_batch_compare_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    run_batch_compare_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    run_batch_compare_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    run_batch_compare_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # run compare table
    run_table_parser = run_compare_subparsers.add_parser("table", help="Generate comparison table")
    run_table_parser.add_argument("--input", required=True, help="Input CSV file")

    # ========================================================================
    # run ticker
    # ========================================================================
    run_ticker_parser = run_subparsers.add_parser(
        "ticker",
        help="Get aggregated candle data for a ticker",
        description="Retrieve OHLC candle data aggregated by time interval",
        epilog="""
Examples:
    # Get daily candle data for NVDA
    synthetic-dividend-tool run ticker --ticker NVDA --start 2024-01-01 --end 2024-01-31

    # Get weekly aggregated data for SPY
    synthetic-dividend-tool run ticker --ticker SPY --start 2023-01-01 --end 2024-12-31 --interval weekly

    # Get monthly data and save to CSV file
    synthetic-dividend-tool run ticker --ticker AAPL --start 2020-01-01 --end 2024-12-31 --interval monthly --output apple_monthly.csv
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run_ticker_parser.add_argument("--ticker", required=True, help="Asset ticker symbol")
    run_ticker_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    run_ticker_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    run_ticker_parser.add_argument(
        "--interval",
        choices=["daily", "weekly", "monthly"],
        default="daily",
        help="Aggregation interval (default: daily)",
    )
    run_ticker_parser.add_argument(
        "--output", help="Output file for results (CSV). If not specified, prints to stdout"
    )

    # ========================================================================
    # ANALYZE command
    # ========================================================================
    analyze_parser = subparsers.add_parser(
        "analyze",
        help="Analyze results and generate reports",
        description="Analysis and reporting tools",
    )
    analyze_subparsers = analyze_parser.add_subparsers(dest="analyze_type", help="Analysis type")

    # analyze volatility-alpha (auto-suggest SD parameters)
    volatility_alpha_parser = analyze_subparsers.add_parser(
        "volatility-alpha", help="Auto-analyze asset and suggest optimal SD parameter"
    )
    volatility_alpha_parser.add_argument("--ticker", required=True, help="Asset ticker")
    volatility_alpha_parser.add_argument("--start", required=True, help="Start date")
    volatility_alpha_parser.add_argument("--end", required=True, help="End date")
    volatility_alpha_parser.add_argument(
        "--initial-qty", type=int, default=100, help="Initial quantity (default: 100)"
    )
    volatility_alpha_parser.add_argument(
        "--plot", action="store_true", help="Generate price chart with transactions"
    )
    volatility_alpha_parser.add_argument(
        "--sd-n", type=int, help="Override auto-suggested SD parameter"
    )
    volatility_alpha_parser.add_argument(
        "--profit-pct", type=float, help="Override profit sharing %% (default: 50)"
    )

    # Return adjustment options
    volatility_alpha_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Show inflation-adjusted returns"
    )
    volatility_alpha_parser.add_argument(
        "--adjust-market", action="store_true", help="Show market-adjusted returns"
    )
    volatility_alpha_parser.add_argument(
        "--adjust-both", action="store_true", help="Show both adjustments"
    )
    volatility_alpha_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    volatility_alpha_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # analyze gap-bonus
    gap_parser = analyze_subparsers.add_parser("gap-bonus", help="Analyze gap bonus impact")
    gap_parser.add_argument("--input", required=True, help="Research CSV file")
    gap_parser.add_argument("--output", help="Output file (optional)")

    # analyze coverage
    coverage_parser = analyze_subparsers.add_parser("coverage", help="Analyze coverage ratios")
    coverage_parser.add_argument("--input", required=True, help="Research CSV file")

    # ========================================================================
    # ORDER command
    # ========================================================================
    order_parser = subparsers.add_parser(
        "order",
        help="Calculate order recommendations",
        description="Calculate buy/sell order recommendations for current market conditions",
    )
    order_parser.add_argument("--ticker", required=True, help="Asset ticker")
    order_parser.add_argument("--holdings", type=int, required=True, help="Current holdings")
    order_parser.add_argument(
        "--algorithm",
        default="sd8",
        help='Algorithm name (e.g., "sd8", "sd-9.15,50", default: "sd8")',
    )
    order_parser.add_argument(
        "--ath", type=float, help="Current ATH (optional, will fetch if omitted)"
    )
    order_parser.add_argument(
        "--current-price", type=float, help="Current price (optional, will fetch if omitted)"
    )

    # ========================================================================
    # DUMP command
    # ========================================================================
    dump_parser = subparsers.add_parser(
        "dump",
        help="Dump transaction history without visualization",
        description="Export detailed transaction history for backtests without creating charts",
    )
    dump_parser.add_argument("--ticker", required=True, help="Asset ticker symbol")
    dump_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    dump_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    dump_parser.add_argument(
        "--initial-qty", type=int, default=10000, help="Initial quantity (default: 10000)"
    )
    dump_parser.add_argument(
        "--algorithm",
        default="sd8",
        help='Algorithm name (e.g., "sd8", "sd-9.15,50", "sd-ath-only-9.15,50", default: "sd8")',
    )
    dump_parser.add_argument("--output", required=True, help="Output file for transaction history")
    dump_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # ========================================================================
    # TEST command
    # ========================================================================
    test_parser = subparsers.add_parser(
        "test", help="Run test suite", description="Execute pytest test suite"
    )
    test_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    test_parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    test_parser.add_argument("--file", help="Specific test file to run")
    test_parser.add_argument("--test", help="Specific test to run")

    return parser


def run_portfolio(args) -> int:
    """Execute portfolio backtest command."""
    import json
    from datetime import datetime

    from src.algorithms.portfolio_definitions import parse_portfolio_name
    from src.algorithms.portfolio_factory import build_portfolio_algo_from_name
    from src.models.backtest import run_portfolio_backtest

    try:
        # Parse allocations: try as named portfolio first, then JSON
        allocations_str = args.allocations.strip()

        # Try to parse as JSON first (starts with '{')
        if allocations_str.startswith("{"):
            try:
                allocations = json.loads(allocations_str)
                print("Parsed allocations from JSON")
            except json.JSONDecodeError:
                print("Error: Invalid JSON format for allocations")
                return 1
        else:
            # Try as named portfolio
            try:
                allocations = parse_portfolio_name(allocations_str)
            except ValueError as e:
                # If not a valid portfolio name, try JSON as fallback
                try:
                    allocations = json.loads(allocations_str)
                    print("Parsed allocations from JSON")
                except json.JSONDecodeError:
                    print(f"Error: {e}")
                    return 1

        # Validate allocations sum to ~1.0
        total_alloc = sum(allocations.values())
        if abs(total_alloc - 1.0) > 0.01:
            print(f"Error: Allocations must sum to 1.0, got {total_alloc:.3f}")
            return 1

        # Parse dates
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()

        print("Running portfolio backtest...")
        print(f"Period: {start_date} to {end_date}")
        print(f"Initial investment: ${args.initial_investment:,.0f}")
        print(f"Algorithm: {args.algo}")
        print("Allocations:")
        for ticker, alloc in allocations.items():
            print(f"  {ticker}: {alloc*100:.1f}%")
        print()

        # Build portfolio algorithm
        portfolio_algo = build_portfolio_algo_from_name(args.algo, allocations)

        # Run the backtest
        transactions, summary = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=args.initial_investment,
            cash_interest_rate_pct=args.cash_interest_rate,
        )

        # Print results
        print("RESULTS:")
        print(f"Final portfolio value: ${summary['total_final_value']:,.0f}")
        print(f"Total return: {summary['total_return']:.2f}%")
        print(f"Annualized return: {summary['annualized_return']:.2f}%")
        if summary.get("cash_interest_earned", 0) > 0:
            print(
                f"Cash interest earned: ${summary['cash_interest_earned']:,.2f} ({summary['cash_interest_rate_pct']:.2f}% APY)"
            )
        print()
        print("Asset breakdown:")
        for ticker, data in summary["assets"].items():
            print(f"  {ticker}: ${data['final_value']:,.0f} ({data['total_return']:.2f}%)")

        # Save detailed results if requested
        if args.output:
            import json

            output_data = {
                "summary": summary,
                "transactions": [
                    {
                        "action": t.action,
                        "ticker": t.ticker,
                        "qty": t.qty,
                        "price": t.price,
                        "date": str(t.transaction_date),
                    }
                    for t in transactions[:100]
                ],  # Limit transactions for file size
                "metadata": {
                    "command": "portfolio",
                    "allocations": allocations,
                    "start_date": str(start_date),
                    "end_date": str(end_date),
                    "initial_investment": args.initial_investment,
                    "algo": args.algo,
                    "run_date": str(datetime.now()),
                },
            }

            with open(args.output, "w") as f:
                json.dump(output_data, f, indent=2, default=str)
            print(f"\nDetailed results saved to {args.output}")

        return 0

    except json.JSONDecodeError as e:
        print(f"Error parsing allocations JSON: {e}")
        print('Example: \'{"NVDA": 0.4, "VOO": 0.6}\'')
        return 1
    except Exception as e:
        print(f"Error running portfolio backtest: {e}")
        return 1


def run_unified(args) -> int:
    """Execute unified run command (backtest, portfolio, research, compare, ticker)."""

    if args.run_type == "backtest":
        return run_backtest(args)
    elif args.run_type == "portfolio":
        return run_portfolio(args)
    elif args.run_type == "research":
        if not args.research_type:
            from argparse import ArgumentParser

            parser = ArgumentParser()
            subparsers = parser.add_subparsers()
            subparsers.add_parser("research")
            parser.parse_args(["run", "research", "--help"])
            return 1
        return run_research(args)
    elif args.run_type == "compare":
        if not args.compare_type:
            from argparse import ArgumentParser

            parser = ArgumentParser()
            subparsers = parser.add_subparsers()
            subparsers.add_parser("compare")
            parser.parse_args(["run", "compare", "--help"])
            return 1
        return run_compare(args)
    elif args.run_type == "ticker":
        return run_ticker(args)
    else:
        print(f"Unknown run type: {args.run_type}")
        return 1


def run_backtest(args) -> int:
    """Execute backtest command."""
    from datetime import datetime

    from src.data.fetcher import HistoryFetcher
    from src.models.backtest import run_algorithm_backtest

    try:
        # Parse dates
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()

        if args.verbose:
            print(f"Running backtest: {args.ticker} from {start_date} to {end_date}")

        # Fetch price data
        fetcher = HistoryFetcher()
        df = fetcher.get_history(args.ticker, start_date, end_date)

        if df is None or df.empty:
            print(f"Error: No data available for {args.ticker}")
            return 1

        # Calculate initial quantity from investment amount
        first_price = df.iloc[0]["Close"]

        if args.initial_qty:
            # User specified shares
            initial_qty = args.initial_qty
            initial_investment = initial_qty * first_price
        else:
            # User specified dollars (default)
            initial_investment = args.initial_investment
            initial_qty = int(initial_investment / first_price)

        if args.verbose:
            print(
                f"Initial purchase: {initial_qty} shares @ ${first_price:.2f} = ${initial_investment:,.2f}"
            )

        # Parse algorithm name (e.g., "sd8", "sd4-75", "buy-and-hold")
        from src.algorithms.factory import build_algo_from_name

        algo = build_algo_from_name(args.algorithm)

        # Run backtest
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=args.ticker,
            initial_qty=initial_qty,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )

        # Enhance summary with additional fields for PDF report
        summary["initial_investment"] = initial_investment
        summary["final_price"] = summary.get("end_price", 0)
        summary["final_holdings"] = summary.get("holdings", 0)
        summary["final_bank"] = summary.get("bank", 0)
        summary["final_portfolio_value"] = summary.get("total", 0)
        summary["total_return_pct"] = summary.get("total_return", 0) * 100  # Convert to percentage
        summary["annualized_return_pct"] = (
            summary.get("annualized", 0) * 100
        )  # Convert to percentage

        # Print summary
        print("\nBACKTEST SUMMARY:")
        print(f"Algorithm: {args.algorithm}")
        print(f"Initial investment: ${initial_investment:,.2f} ({initial_qty} shares)")
        print(f"Final portfolio value: ${summary.get('final_portfolio_value', 0):,.2f}")
        print(f"Final holdings: {summary.get('final_holdings', 0)} shares")
        print(f"Final bank: ${summary.get('final_bank', 0):,.2f}")
        print(f"Total return: {summary.get('total_return_pct', 0):.2f}%")
        print(f"Annualized return: {summary.get('annualized_return_pct', 0):.2f}%")
        print(f"Total transactions: {len(transactions)}")

        # Generate PDF report if requested
        if args.pdf_report:
            from src.reports import create_backtest_pdf_report

            # Prepare summary with additional metadata
            summary["algorithm_name"] = args.algorithm
            summary["buy_count"] = len([tx for tx in transactions if tx.action == "BUY"])
            summary["sell_count"] = len([tx for tx in transactions if tx.action == "SELL"])
            summary["transaction_count"] = len(transactions)

            pdf_path = create_backtest_pdf_report(
                ticker=args.ticker,
                transactions=transactions,
                summary=summary,
                price_data=df,
                output_path=args.pdf_report,
            )

            print(f"\nPDF report generated: {pdf_path}")

        # Save CSV if requested
        if args.output:
            import csv

            with open(args.output, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Date", "Action", "Qty", "Price", "Notes"])
                for tx in transactions:
                    writer.writerow(
                        [tx.transaction_date, tx.action, tx.qty, f"${tx.price:.2f}", tx.notes]
                    )
            print(f"Transaction log saved: {args.output}")

        return 0

    except Exception as e:
        print(f"Error running backtest: {e}")
        import traceback

        traceback.print_exc()
        return 1


def run_research(args) -> int:
    """Execute research command."""

    if args.research_type == "optimal-rebalancing":
        from src.research import optimal_rebalancing

        # Build arguments
        research_args = [
            "--start",
            args.start,
            "--end",
            args.end,
            "--profit-pct",
            str(args.profit_pct),
            "--initial-qty",
            str(args.initial_qty),
            "--output",
            args.output,
        ]

        if args.ticker:
            research_args.extend(["--ticker", args.ticker])
        if args.asset_class:
            research_args.extend(["--asset-class", args.asset_class])

        sys.argv = ["optimal_rebalancing.py"] + research_args
        optimal_rebalancing.main()
        return 0

    elif args.research_type == "volatility-alpha":
        from src.research import volatility_alpha

        research_args = ["--start", args.start, "--end", args.end, "--output", args.output]

        sys.argv = ["volatility_alpha.py"] + research_args
        volatility_alpha.main()
        return 0

    elif args.research_type == "asset-classes":
        from src.research import asset_classes

        research_args = ["--start", args.start, "--end", args.end, "--output", args.output]

        sys.argv = ["asset_classes.py"] + research_args
        asset_classes.main()
        return 0

    else:
        print(f"Unknown research type: {args.research_type}")
        print("Use 'synthetic-dividend-tool research --help' for available research types")
        return 1


def run_compare(args) -> int:
    """Execute compare command."""

    if args.compare_type == "algorithms":
        pass

        print("Running algorithm comparison...")
        # Would integrate with src.compare.runner
        return 0

    elif args.compare_type == "strategies":
        pass

        print(f"Comparing strategies for {args.ticker}...")
        # Would integrate with strategy comparison
        return 0

    elif args.compare_type == "batch":
        pass

        print(f"Running batch comparison: {args.tickers} with {args.strategies}...")
        # Would integrate with batch_comparison
        return 0

    elif args.compare_type == "table":
        pass

        print(f"Generating comparison table from {args.input}...")
        # Would integrate with src.compare.table
        return 0

    else:
        print(f"Unknown comparison type: {args.compare_type}")
        return 1


def run_ticker(args) -> int:
    """Execute ticker command to get aggregated candle data."""
    from datetime import datetime

    import pandas as pd

    from src.data.asset import Asset

    try:
        # Parse dates
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()

        # Fetch price data
        asset = Asset(args.ticker)
        df = asset.get_prices(start_date, end_date)

        if df.empty:
            print(
                f"No data found for ticker {args.ticker} in date range {args.start} to {args.end}"
            )
            return 1

        # Aggregate data based on interval
        if args.interval == "daily":
            # Daily data is already in the right format
            result_df = df.copy()
        elif args.interval == "weekly":
            # Resample to weekly (end of week)
            agg_dict = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
            if "Volume" in df.columns:
                agg_dict["Volume"] = "sum"
            result_df = df.resample("W").agg(agg_dict)
        elif args.interval == "monthly":
            # Resample to monthly (end of month)
            agg_dict = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
            if "Volume" in df.columns:
                agg_dict["Volume"] = "sum"
            result_df = df.resample("ME").agg(agg_dict)
        else:
            print(f"Invalid interval: {args.interval}. Must be 'daily', 'weekly', or 'monthly'")
            return 1

        # Format output with required columns: Date, Ticker, O, C, L, H
        output_df = pd.DataFrame(
            {
                "Date": result_df.index.strftime("%Y-%m-%d"),
                "Ticker": args.ticker,
                "O": result_df["Open"].round(2),
                "C": result_df["Close"].round(2),
                "L": result_df["Low"].round(2),
                "H": result_df["High"].round(2),
            }
        )

        # Output results
        if args.output:
            output_df.to_csv(args.output, index=False)
            print(f"Results saved to {args.output}")
        else:
            # Print to stdout
            print(output_df.to_csv(index=False))

        return 0

    except Exception as e:
        print(f"Error retrieving ticker data: {e}")
        return 1


def run_analyze(args) -> int:
    """Execute analyze command."""

    if args.analyze_type == "volatility-alpha":
        import os
        import subprocess

        # Build command for analyze-volatility-alpha
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "src",
            "tools",
            "volatility_alpha_analyzer.py",
        )

        cmd = [sys.executable, script_path, args.ticker, args.start, args.end]

        if args.initial_qty:
            cmd.extend(["--initial-qty", str(args.initial_qty)])
        if args.plot:
            cmd.append("--plot")
        if args.sd_n:
            cmd.extend(["--sd-n", str(args.sd_n)])
        if args.profit_pct:
            cmd.extend(["--profit-pct", str(args.profit_pct)])

        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    elif args.analyze_type == "gap-bonus":
        import os
        import subprocess

        # Run our analysis script with proper Python interpreter
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "tools", "analyze_gap_bonus.py"
        )
        cmd = [sys.executable, script_path]
        result = subprocess.run(cmd, capture_output=False)
        return result.returncode

    elif args.analyze_type == "coverage":
        print(f"Analyzing coverage ratios from {args.input}...")
        # Would implement coverage analysis
        return 0

    else:
        print(f"Unknown analysis type: {args.analyze_type}")
        return 1


def run_order(args) -> int:
    """Execute order calculation command."""

    print(f"Calculating orders for {args.ticker}...")
    print(f"Holdings: {args.holdings}")
    print(f"Algorithm: {args.algorithm}")

    # Would integrate with order_calculator
    return 0


def run_dump(args) -> int:
    """Execute dump transaction history command."""
    from datetime import datetime
    from typing import List

    from src.algorithms.factory import build_algo_from_name
    from src.data.asset import Asset
    from src.models.backtest import run_algorithm_backtest

    try:
        # Parse dates
        start_date = datetime.strptime(args.start, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end, "%Y-%m-%d").date()

        if args.verbose:
            print(f"Dumping transactions for {args.ticker} from {args.start} to {args.end}")
            print(f"Algorithm: {args.algorithm}")

        # Load price history
        df = Asset(args.ticker).get_prices(start_date, end_date)
        if df.empty:
            print(f"Error: No price data found for {args.ticker} in the given date range.")
            return 1

        # Build algorithm
        algo = build_algo_from_name(args.algorithm)

        # Run backtest
        txs, summary = run_algorithm_backtest(
            df,
            args.ticker,
            initial_qty=args.initial_qty,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )

        # Write transactions to file
        tx_lines: List[str] = []
        for t in txs:
            # If already a string, use it directly
            if isinstance(t, str):
                tx_lines.append(t)
                continue
            # Prefer a to_string() method if available
            to_string = getattr(t, "to_string", None)
            if callable(to_string):
                tx_lines.append(to_string())
                continue
            # Fallback: try common attributes
            action = getattr(t, "action", getattr(t, "transaction_type", None))
            date_attr = getattr(t, "transaction_date", getattr(t, "purchase_date", None))
            qty = getattr(t, "qty", getattr(t, "shares", None))
            price = getattr(t, "price", getattr(t, "purchase_price", None))
            ticker_attr = getattr(t, "ticker", None)
            if (
                date_attr is not None
                and action is not None
                and qty is not None
                and price is not None
            ):
                try:
                    date_str = date_attr.isoformat()
                except Exception:
                    date_str = str(date_attr)
                # Standardized format
                tx_lines.append(
                    f"{date_str} {action.upper()} {qty} @ {price:.2f} {ticker_attr or ''}".strip()
                )
                continue
            # Last resort: use str()
            tx_lines.append(str(t))

        with open(args.output, "w") as f:
            for line in tx_lines:
                f.write(line + "\n")

        if args.verbose:
            print(f"Wrote {len(tx_lines)} transactions to {args.output}")
            print("Summary:")
            for k, v in summary.items():
                print(f"  {k}: {v}")
        else:
            print(f"Transaction history dumped to {args.output} ({len(tx_lines)} transactions)")

        return 0

    except Exception as e:
        print(f"Error dumping transactions: {e}")
        return 1


def run_test(args) -> int:
    """Execute test suite."""
    import subprocess

    cmd = [sys.executable, "-m", "pytest"]

    if args.verbose:
        cmd.append("-v")

    if args.coverage:
        cmd.extend(["--cov=src", "--cov-report=html"])

    if args.file:
        cmd.append(args.file)

    if args.test:
        cmd.extend(["-k", args.test])

    result = subprocess.run(cmd)
    return result.returncode


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point."""

    parser = create_parser()

    if argv is None:
        argv = sys.argv[1:]

    # Show help if no command provided
    if not argv:
        parser.print_help()
        return 0

    args = parser.parse_args(argv)

    # Handle --list-algorithms flag
    if hasattr(args, "list_algorithms") and args.list_algorithms:
        list_algorithms()
        return 0

    # Handle --list-portfolios flag
    if hasattr(args, "list_portfolios") and args.list_portfolios:
        list_portfolios()
        return 0

    # Dispatch to appropriate handler
    if args.command == "run":
        if not args.run_type:
            parser.parse_args(["run", "--help"])
            return 1
        return run_unified(args)

    elif args.command == "analyze":
        if not args.analyze_type:
            parser.parse_args(["analyze", "--help"])
            return 1
        return run_analyze(args)

    elif args.command == "order":
        return run_order(args)

    elif args.command == "dump":
        return run_dump(args)

    elif args.command == "test":
        return run_test(args)

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
