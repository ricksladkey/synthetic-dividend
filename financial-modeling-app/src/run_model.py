#!/usr/bin/env python3
"""Command-line interface for running backtest simulations.

Fetches historical price data and executes trading algorithms,
printing transaction log and performance summary.

Usage:
    python run_model.py TICKER START END STRATEGY [QTY]
    
Examples:
    python run_model.py NVDA 10/22/2024 10/22/2025 buy-and-hold
    python run_model.py NVDA 2024-10-22 2025-10-22 sd/9.05%/50% 10000

Date formats: MM/DD/YYYY or YYYY-MM-DD
Strategy formats: buy-and-hold, sd/X%/Y%, sd-ath-only/X%/Y%
Optional QTY defaults to 10000 shares
"""
import sys
import os
from datetime import date, datetime
from typing import List


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


def main(argv: List[str]) -> int:
    """Execute backtest from command-line arguments.
    
    Args:
        argv: Command-line arguments (excluding program name)
        
    Returns:
        Exit code (0 = success, >0 = error)
    """
    # Validate argument count
    if len(argv) < 4:
        print("Usage: run_model.py TICKER START_DATE END_DATE STRATEGY_NAME [QTY]")
        print("Example: run_model.py NVDA 10/22/2024 10/22/2025 sd/9.05%/50% 10000")
        return 2

    # Parse required arguments
    ticker: str = argv[0]
    try:
        start: date = parse_date(argv[1])
        end: date = parse_date(argv[2])
    except ValueError as e:
        print("Error parsing dates:", e)
        return 2

    # Parse strategy and optional quantity
    # If last arg is numeric, treat as quantity; else all args form strategy name
    qty: int = 10000  # Default quantity
    strategy_args: List[str] = argv[3:]
    
    if len(strategy_args) > 0:
        try:
            # Attempt to parse last arg as integer quantity
            qty = int(strategy_args[-1])
            # Success: exclude quantity from strategy string
            strategy = " ".join(strategy_args[:-1])
        except ValueError:
            # Last arg not numeric: all args form strategy name
            strategy = " ".join(strategy_args)

    # Ensure src package is importable (for running from repo root)
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    # Import runtime dependencies
    try:
        from src.data.fetcher import HistoryFetcher
        from src.models.backtest import run_algorithm_backtest, build_algo_from_name
    except Exception as e:
        print("Failed to import runtime modules:", e)
        return 3

    # Fetch historical price data
    hf = HistoryFetcher()
    try:
        df = hf.get_history(ticker, start, end)
    except Exception as e:
        print("Fetcher error:", e)
        return 4

    # Validate data availability
    if df is None or df.empty:
        print("No price data available for", ticker, "in that range.")
        return 5

    # Build algorithm instance from string identifier
    algo_inst = build_algo_from_name(strategy)
    
    # Execute backtest
    try:
        transactions, summary = run_algorithm_backtest(
            df, ticker, qty, start, end, algo=algo_inst
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
    print(f"Total (holdings + bank): {summary.get('total', summary['end_value']):.2f}")
    print()
    print(f"Total return: {summary['total_return']*100:.2f}%")
    print(f"Annualized return: {summary['annualized']*100:.2f}% (over {summary['years']:.3f} years)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
