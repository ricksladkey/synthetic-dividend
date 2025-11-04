#!/usr/bin/env python3
"""Command-line interface for running backtest simulations.

Fetches historical price data and executes trading algorithms,
printing transaction log and performance summary.

Usage:
    python run_model.py TICKER START END STRATEGY [options]

Examples:
    python run_model.py NVDA 10/22/2024 10/22/2025 buy-and-hold
    python run_model.py NVDA 2024-10-22 2025-10-22 sd-9.05,50 --qty 10000
    python run_model.py NVDA 10/22/2024 10/22/2025 sd-9.05,50 --reference-asset SPY --risk-free-asset BIL

Date formats: MM/DD/YYYY or YYYY-MM-DD
Strategy formats: buy-and-hold, sd-X,Y, sd-ath-only-X,Y
Legacy formats: sd/X%/Y%, sd-ath-only/X%/Y% (still supported)
"""
import argparse
import os
import sys
from datetime import date, datetime
from typing import List, Optional


def parse_date(s: str) -> date:
    """Parse date string in MM/DD/YYYY or YYYY-MM-DD format.

    Args:
        s: Date string

    Returns:
        date object

    Raises:
        ValueError: If format not recognized
    """
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    raise ValueError(f"Unrecognized date format: {s}")


def main(argv: Optional[List[str]] = None) -> int:
    """Execute backtest from command-line arguments.

    Args:
        argv: Command-line arguments (excluding program name). If None, uses sys.argv[1:]

    Returns:
        Exit code (0 = success, >0 = error)
    """
    if argv is None:
        argv = sys.argv[1:]

    # Setup argument parser
    parser = argparse.ArgumentParser(
        description="Run backtest on historical stock data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_model.py NVDA 10/22/2024 10/22/2025 buy-and-hold
  python run_model.py NVDA 2024-10-22 2025-10-22 sd-9.05,50 --qty 10000
  python run_model.py NVDA 10/22/2024 10/22/2025 sd-9.05,50 --reference-asset SPY --risk-free-asset BIL
        """,
    )

    parser.add_argument("ticker", help="Stock ticker symbol (e.g., NVDA)")
    parser.add_argument("start_date", help="Start date (MM/DD/YYYY or YYYY-MM-DD)")
    parser.add_argument("end_date", help="End date (MM/DD/YYYY or YYYY-MM-DD)")
    parser.add_argument("strategy", help="Strategy name (e.g., buy-and-hold, sd-9.05,50)")
    parser.add_argument(
        "--initial-investment", type=int, default=10000, help="Initial quantity of shares (default: 10000)"
    )
    parser.add_argument(
        "--reference-asset",
        type=str,
        default="VOO",
        help="Reference asset for opportunity cost (default: VOO)",
    )
    parser.add_argument(
        "--risk-free-asset",
        type=str,
        default="BIL",
        help="Risk-free asset for cash interest (default: BIL)",
    )

    args = parser.parse_args(argv)

    # Parse dates
    ticker: str = args.ticker
    try:
        start: date = parse_date(args.start_date)
        end: date = parse_date(args.end_date)
    except ValueError as e:
        print("Error parsing dates:", e)
        return 2

    strategy: str = args.strategy
    qty: int = args.initial_investment
    reference_asset: str = args.reference_asset
    risk_free_asset: str = args.risk_free_asset

    # Ensure src package is importable (for running from repo root)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Import runtime dependencies
    try:
        from src.algorithms.factory import build_algo_from_name
        from src.data.fetcher import HistoryFetcher
        from src.models.backtest import run_algorithm_backtest
    except Exception as e:
        print("Failed to import runtime modules:", e)
        return 3

    # Fetch historical price data for main ticker and financial adjustment assets
    hf = HistoryFetcher()
    try:
        # Fetch main ticker
        df = hf.get_history(ticker, start, end)

        # Fetch reference and risk-free assets
        from src.models.backtest import Data

        reference_data: Optional[Data] = None
        risk_free_data: Optional[Data] = None

        if reference_asset:
            try:
                reference_data = hf.get_history(reference_asset, start, end)
                if reference_data.empty:
                    print(
                        f"Warning: No data for reference asset {reference_asset}, using fallback rate"
                    )
                    reference_data = None
            except Exception as e:
                print(f"Warning: Failed to fetch {reference_asset}: {e}")
                reference_data = None

        if risk_free_asset:
            try:
                risk_free_data = hf.get_history(risk_free_asset, start, end)
                if risk_free_data.empty:
                    print(
                        f"Warning: No data for risk-free asset {risk_free_asset}, using fallback rate"
                    )
                    risk_free_data = None
            except Exception as e:
                print(f"Warning: Failed to fetch {risk_free_asset}: {e}")
                risk_free_data = None

    except Exception as e:
        print("Fetcher error:", e)
        return 4

    # Validate data availability
    if df is None or df.empty:
        print("No price data available for", ticker, "in that range.")
        return 5

    # Build algorithm instance from string identifier
    algo_inst = build_algo_from_name(strategy)

    # Execute backtest with financial adjustment assets
    try:
        transactions, summary = run_algorithm_backtest(
            df,
            ticker,
            qty,
            start,
            end,
            algo=algo_inst,
            reference_data=reference_data,
            risk_free_data=risk_free_data,
            reference_asset_ticker=reference_asset,
            risk_free_asset_ticker=risk_free_asset,
        )
    except Exception as e:
        print("Backtest error:", e)
        return 6

    # Print transaction log
    for t in transactions:
        print(t)

    # Print summary statistics (format matches GUI output)
    print()
    print(f"Ticker: {summary['ticker']}")
    print(f"Start Date: {summary['start_date'].isoformat()}")
    print(f"Start Price: {summary['start_price']:.2f}")
    print(f"Start Value: {summary['start_value']:.2f}")
    print()
    print(f"End Date: {summary['end_date'].isoformat()}")
    print(f"End Price: {summary['end_price']:.2f}")
    print(f"End Value: {summary['end_value']:.2f}")
    print(f"Holdings: {summary.get('holdings', qty)} shares")
    print()
    print(f"Bank: {summary.get('bank', 0.0):.2f}")
    print(f"  Bank Min: {summary.get('bank_min', 0.0):.2f}")
    print(f"  Bank Max: {summary.get('bank_max', 0.0):.2f}")
    print(f"  Bank Avg: {summary.get('bank_avg', 0.0):.2f}")
    print(f"  Days Negative: {summary.get('bank_negative_count', 0)}")
    print(f"  Days Positive: {summary.get('bank_positive_count', 0)}")
    print(f"Total (holdings + bank): {summary.get('total', summary['end_value']):.2f}")
    print()
    print(f"Opportunity Cost ({reference_asset}): {summary.get('opportunity_cost', 0.0):.2f}")
    print(f"Risk-Free Gains ({risk_free_asset}): {summary.get('risk_free_gains', 0.0):.2f}")
    print(
        f"Net Financial Adjustment: {summary.get('risk_free_gains', 0.0) - summary.get('opportunity_cost', 0.0):.2f}"
    )
    print()
    print(f"Total return: {summary['total_return']*100:.2f}%")
    print(
        f"Annualized return: {summary['annualized']*100:.2f}% (over {summary['years']:.3f} years)"
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
