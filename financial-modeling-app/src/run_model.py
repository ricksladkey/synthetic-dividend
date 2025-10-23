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

    # strategy may contain spaces; join the remaining args
    # optional 5th argument is quantity; default to 1000 to match GUI
    strategy = " ".join(argv[3:])
    qty = 1000
    if len(argv) >= 5:
        try:
            qty = int(argv[4])
        except Exception:
            print("Invalid quantity provided, using default 1000")

    # ensure repo src package is importable when running from repo root
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    try:
        from src.data.fetcher import HistoryFetcher
        from src.models.backtest import buy_and_hold_backtest
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

    try:
        transactions, summary = buy_and_hold_backtest(df, ticker, qty, start, end)
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
    print()
    print(f"Total return: {summary['total_return']*100:.2f}%")
    print(f"Annualized return: {summary['annualized']*100:.2f}% (over {summary['years']:.3f} years)")

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
