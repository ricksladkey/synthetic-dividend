#!/usr/bin/env python3
"""Small CLI runner that loads ticker history using HistoryFetcher.

Usage:
  python run_model.py TICKER START_DATE END_DATE STRATEGY_NAME

START_DATE and END_DATE accept MM/DD/YYYY or YYYY-MM-DD.
"""
import sys
import os
from datetime import datetime


def parse_date(s: str):
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    raise ValueError(f"Unrecognized date format: {s}")


def main(argv):
    if len(argv) < 4:
        print("Usage: run_model.py TICKER START_DATE END_DATE STRATEGY_NAME")
        return 2

    ticker = argv[0]
    try:
        start = parse_date(argv[1])
        end = parse_date(argv[2])
    except ValueError as e:
        print("Error parsing dates:", e)
        return 2

    # strategy may contain spaces or special chars
    # optional last argument (if it's a number) is quantity; default to 1000
    qty = 1000
    strategy_args = argv[3:]
    
    # Check if last arg is a number (quantity)
    if len(strategy_args) > 0:
        try:
            qty = int(strategy_args[-1])
            # If successful, it's a quantity, so exclude it from strategy
            strategy = " ".join(strategy_args[:-1])
        except ValueError:
            # Not a number, so all args are part of strategy
            strategy = " ".join(strategy_args)

    # ensure repo src package is importable when running from repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from src.data.fetcher import HistoryFetcher
        from src.models.backtest import run_algorithm_backtest, build_algo_from_name
    except Exception as e:
        print("Failed to import runtime modules:", e)
        return 3

    hf = HistoryFetcher()
    try:
        df = hf.get_history(ticker, start, end)
    except Exception as e:
        print("Fetcher error:", e)
        return 4

    if df is None or df.empty:
        print("No price data available for", ticker, "in that range.")
        return 5

    algo_inst = build_algo_from_name(strategy)
    try:
        transactions, summary = run_algorithm_backtest(df, ticker, qty, start, end, algo=algo_inst)
    except Exception as e:
        print("Backtest error:", e)
        return 6

    # Print transactions and summary to match GUI
    for t in transactions:
        print(t)

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
