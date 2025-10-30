"""
Synthetic Dividend Tool - Unified CLI Interface

A swiss army knife tool that provides a single entry point for all
synthetic dividend operations.

Usage:
    synthetic-dividend-tool <command> [options]

Commands:
    backtest              Run backtest on single asset
    research              Run research studies (optimal rebalancing, volatility alpha)
    compare               Compare strategies or algorithms
    analyze               Analyze results and generate reports
    order                 Calculate order recommendations
    test                  Run test suite

Use 'synthetic-dividend-tool <command> --help' for command-specific options.
"""

import argparse
import sys
from typing import List, Optional


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""

    parser = argparse.ArgumentParser(
        prog="synthetic-dividend-tool",
        description="Synthetic Dividend Algorithm - Unified CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run backtest on NVDA
    synthetic-dividend-tool backtest --ticker NVDA --start 2023-01-01 --end 2024-01-01

    # Backtest with inflation adjustment
    synthetic-dividend-tool backtest --ticker NVDA --start 2024-01-01 --end 2024-12-31 --adjust-inflation --verbose

    # Backtest with market adjustment (vs VOO)
    synthetic-dividend-tool backtest --ticker GLD --start 2024-01-01 --end 2024-12-31 --adjust-market --verbose

    # Complete return analysis (nominal + real + alpha)
    synthetic-dividend-tool backtest --ticker AAPL --start 2024-01-01 --end 2024-12-31 --adjust-both --verbose

    # Auto-analyze volatility and suggest optimal SD
    synthetic-dividend-tool analyze volatility-alpha --ticker GLD --start 2024-01-01 --end 2025-01-01

    # Run optimal rebalancing research
    synthetic-dividend-tool research optimal-rebalancing --output results.csv

    # Compare algorithms
    synthetic-dividend-tool compare algorithms --ticker SPY --start 2023-01-01 --end 2024-01-01

    # Batch comparison across assets
    synthetic-dividend-tool compare batch --tickers NVDA AAPL GLD --strategies sd8 sd16 --start 2024-01-01 --end 2025-01-01

    # Analyze gap bonus
    synthetic-dividend-tool analyze gap-bonus --input research_phase1_1year_core.csv

    # Run tests
    synthetic-dividend-tool test

    # Calculate orders
    synthetic-dividend-tool order --ticker NVDA --holdings 1000

For detailed help on any command:
    synthetic-dividend-tool <command> --help
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # ========================================================================
    # PORTFOLIO command
    # ========================================================================
    portfolio_parser = subparsers.add_parser(
        "portfolio",
        help="Run portfolio backtests",
        description="Execute multi-asset portfolio backtests with algorithmic strategies",
    )
    portfolio_parser.add_argument(
        "--allocations",
        required=True,
        help='Asset allocations as JSON string, e.g., \'{"NVDA": 0.4, "VOO": 0.6}\'',
    )
    portfolio_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    portfolio_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    portfolio_parser.add_argument(
        "--initial-investment",
        type=float,
        default=1_000_000,
        help="Initial investment amount (default: 1,000,000)",
    )
    portfolio_parser.add_argument(
        "--algo",
        default="auto",
        help='Algorithm: "auto" (default), "quarterly-rebalance", "per-asset:sd8", etc.',
    )
    portfolio_parser.add_argument("--output", help="Output file for detailed results (JSON)")
    portfolio_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # ========================================================================
    # BACKTEST command
    backtest_parser = subparsers.add_parser(
        "backtest",
        help="Run backtest on a single asset",
        description="Execute backtest using synthetic dividend algorithm",
    )
    backtest_parser.add_argument("--ticker", required=True, help="Asset ticker symbol")
    backtest_parser.add_argument("--start", required=True, help="Start date (YYYY-MM-DD)")
    backtest_parser.add_argument("--end", required=True, help="End date (YYYY-MM-DD)")
    backtest_parser.add_argument(
        "--initial-qty", type=int, default=1000, help="Initial quantity (default: 1000)"
    )
    backtest_parser.add_argument("--sd-n", type=int, default=8, help="SD-N value (default: 8)")
    backtest_parser.add_argument(
        "--profit-pct", type=float, default=50.0, help="Profit sharing %% (default: 50)"
    )
    backtest_parser.add_argument(
        "--ath-only", action="store_true", help="Use ATH-only mode (no buybacks)"
    )
    backtest_parser.add_argument("--output", help="Output file for results (CSV)")
    backtest_parser.add_argument("--verbose", action="store_true", help="Verbose output")

    # Return adjustment options
    backtest_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Show inflation-adjusted (real) returns"
    )
    backtest_parser.add_argument(
        "--adjust-market", action="store_true", help="Show market-adjusted returns (alpha)"
    )
    backtest_parser.add_argument(
        "--adjust-both", action="store_true", help="Show both inflation and market adjustments"
    )
    backtest_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    backtest_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # ========================================================================
    # RESEARCH command
    # ========================================================================
    research_parser = subparsers.add_parser(
        "research", help="Run research studies", description="Execute various research analyses"
    )
    research_subparsers = research_parser.add_subparsers(dest="research_type", help="Research type")

    # research optimal-rebalancing
    optimal_parser = research_subparsers.add_parser(
        "optimal-rebalancing", help="Find optimal rebalancing parameters"
    )
    optimal_parser.add_argument(
        "--start", default="2023-10-23", help="Start date (default: 2023-10-23)"
    )
    optimal_parser.add_argument(
        "--end", default="2024-10-23", help="End date (default: 2024-10-23)"
    )
    optimal_parser.add_argument(
        "--profit-pct", type=float, default=50.0, help="Profit sharing %% (default: 50)"
    )
    optimal_parser.add_argument(
        "--initial-qty", type=int, default=10000, help="Initial quantity (default: 10000)"
    )
    optimal_parser.add_argument("--ticker", help="Specific ticker (optional, tests all if omitted)")
    optimal_parser.add_argument("--asset-class", help="Specific asset class (optional)")
    optimal_parser.add_argument("--output", required=True, help="Output CSV file")

    # Return adjustment options
    optimal_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    optimal_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    optimal_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    optimal_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    optimal_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # research volatility-alpha
    volatility_parser = research_subparsers.add_parser(
        "volatility-alpha", help="Analyze volatility alpha across assets"
    )
    volatility_parser.add_argument("--start", default="2023-10-23", help="Start date")
    volatility_parser.add_argument("--end", default="2024-10-23", help="End date")
    volatility_parser.add_argument("--output", required=True, help="Output CSV file")

    # Return adjustment options
    volatility_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    volatility_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    volatility_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    volatility_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    volatility_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # research asset-classes
    asset_class_parser = research_subparsers.add_parser(
        "asset-classes", help="Analyze performance by asset class"
    )
    asset_class_parser.add_argument("--start", required=True, help="Start date")
    asset_class_parser.add_argument("--end", required=True, help="End date")
    asset_class_parser.add_argument("--output", required=True, help="Output CSV file")

    # Return adjustment options
    asset_class_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    asset_class_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    asset_class_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    asset_class_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    asset_class_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # ========================================================================
    # COMPARE command
    # ========================================================================
    compare_parser = subparsers.add_parser(
        "compare", help="Compare strategies or algorithms", description="Run comparison analyses"
    )
    compare_subparsers = compare_parser.add_subparsers(dest="compare_type", help="Comparison type")

    # compare algorithms
    algo_compare_parser = compare_subparsers.add_parser(
        "algorithms", help="Compare different algorithm configurations"
    )
    algo_compare_parser.add_argument("--ticker", required=True, help="Asset ticker")
    algo_compare_parser.add_argument("--start", required=True, help="Start date")
    algo_compare_parser.add_argument("--end", required=True, help="End date")
    algo_compare_parser.add_argument("--output", help="Output file")

    # compare strategies
    strategy_compare_parser = compare_subparsers.add_parser(
        "strategies", help="Compare different trading strategies"
    )
    strategy_compare_parser.add_argument("--ticker", required=True, help="Asset ticker")
    strategy_compare_parser.add_argument("--start", required=True, help="Start date")
    strategy_compare_parser.add_argument("--end", required=True, help="End date")
    strategy_compare_parser.add_argument("--output", help="Output file")

    # compare batch
    batch_compare_parser = compare_subparsers.add_parser(
        "batch", help="Run batch comparison across multiple assets/strategies"
    )
    batch_compare_parser.add_argument("--tickers", nargs="+", required=True, help="List of tickers")
    batch_compare_parser.add_argument(
        "--strategies", nargs="+", required=True, help="List of strategies (e.g., sd8 sd16)"
    )
    batch_compare_parser.add_argument("--start", required=True, help="Start date")
    batch_compare_parser.add_argument("--end", required=True, help="End date")
    batch_compare_parser.add_argument("--output", help="Output CSV file")

    # Return adjustment options
    batch_compare_parser.add_argument(
        "--adjust-inflation", action="store_true", help="Add inflation-adjusted returns to output"
    )
    batch_compare_parser.add_argument(
        "--adjust-market", action="store_true", help="Add market-adjusted returns to output"
    )
    batch_compare_parser.add_argument(
        "--adjust-both", action="store_true", help="Add both inflation and market adjustments"
    )
    batch_compare_parser.add_argument(
        "--inflation-ticker", default="CPI", help="Ticker for inflation data (default: CPI)"
    )
    batch_compare_parser.add_argument(
        "--market-ticker", default="VOO", help="Ticker for market benchmark (default: VOO)"
    )

    # compare table
    table_parser = compare_subparsers.add_parser("table", help="Generate comparison table")
    table_parser.add_argument("--input", required=True, help="Input CSV file")

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
    order_parser.add_argument("--sd-n", type=int, default=8, help="SD-N value (default: 8)")
    order_parser.add_argument(
        "--ath", type=float, help="Current ATH (optional, will fetch if omitted)"
    )
    order_parser.add_argument(
        "--current-price", type=float, help="Current price (optional, will fetch if omitted)"
    )

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

    from src.algorithms import build_portfolio_algo_from_name
    from src.models.backtest import run_portfolio_backtest_v2

    try:
        # Parse allocations JSON
        allocations = json.loads(args.allocations)

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

        # Build portfolio algorithm from notation
        portfolio_algo = build_portfolio_algo_from_name(args.algo, allocations)

        # Run the backtest
        transactions, summary = run_portfolio_backtest_v2(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=args.initial_investment,
        )

        # Print results
        print("RESULTS:")
        print(f"Final portfolio value: ${summary['total_final_value']:,.0f}")
        print(f"Final bank balance: ${summary['final_bank']:,.0f}")
        print(f"Total return: {summary['total_return']:.2f}%")
        print(f"Annualized return: {summary['annualized_return']:.2f}%")
        print(f"Transactions: {summary['transaction_count']}")
        print()
        print("Asset breakdown:")
        for ticker, data in summary["assets"].items():
            print(
                f"  {ticker}: {data['final_holdings']} shares @ ${data['final_price']:.2f} "
                f"= ${data['final_value']:,.0f} ({data['total_return']:.2f}%)"
            )

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


def run_backtest(args) -> int:
    """Execute backtest command."""

    # Convert args to run_model format
    sys.argv = ["run_model.py", args.ticker]
    if args.verbose:
        print(f"Running backtest: {args.ticker} from {args.start} to {args.end}")

    # This is a simplified version - would need to properly integrate with run_model
    print("Backtest functionality - to be integrated with src.run_model")
    return 0


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
    print(f"SD-N: {args.sd_n}")

    # Would integrate with order_calculator
    return 0


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

    # Dispatch to appropriate handler
    if args.command == "backtest":
        return run_backtest(args)

    elif args.command == "portfolio":
        return run_portfolio(args)

    elif args.command == "research":
        if not args.research_type:
            parser.parse_args(["research", "--help"])
            return 1
        return run_research(args)

    elif args.command == "compare":
        if not args.compare_type:
            parser.parse_args(["compare", "--help"])
            return 1
        return run_compare(args)

    elif args.command == "analyze":
        if not args.analyze_type:
            parser.parse_args(["analyze", "--help"])
            return 1
        return run_analyze(args)

    elif args.command == "order":
        return run_order(args)

    elif args.command == "test":
        return run_test(args)

    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
