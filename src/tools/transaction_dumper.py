#!/usr/bin/env python3
"""Simple script to dump transaction history without visualization."""

import sys
from datetime import datetime
from typing import List

from src.algorithms.factory import build_algo_from_name
from src.data.asset import Asset
from src.models.backtest import run_algorithm_backtest


def main() -> int:
    """Main entry point for transaction dumper."""
    if len(sys.argv) < 6:
        print(
            "Usage: python -m src.tools.transaction_dumper <TICKER> <START> <END> <ALGO_ID> <OUTPUT_FILE>"
        )
        return 2

    ticker = sys.argv[1]
    start = datetime.fromisoformat(sys.argv[2]).date()
    end = datetime.fromisoformat(sys.argv[3]).date()
    algo_id = sys.argv[4]
    output_file = sys.argv[5]

    # Load price history
    df = Asset(ticker).get_prices(start, end)
    if df.empty:
        print(f"Error: No price data found for {ticker} in the given date range.")
        return 1

    algo = build_algo_from_name(algo_id)

    txs, summary = run_algorithm_backtest(
        df, ticker, initial_qty=10000, start_date=start, end_date=end, algo=algo
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
        if date_attr is not None and action is not None and qty is not None and price is not None:
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

    with open(output_file, "w") as f:
        for line in tx_lines:
            f.write(line + "\n")

    print(f"Wrote {len(tx_lines)} transactions to {output_file}")
    print("Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
