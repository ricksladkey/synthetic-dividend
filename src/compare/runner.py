"""Simple compare runner: runs one backtest and produces a price chart with trades.

Usage (from repo root):
  python -m src.compare.runner NVDA 2024-10-27 2025-10-27 synthetic-dividend/9.05%/50% out.png
"""

import os
import sys
from datetime import datetime

from src.compare.plotter import plot_price_with_trades
from src.data.asset import Asset
from src.models.backtest import build_algo_from_name, run_algorithm_backtest


def main() -> int:
    """Main entry point for the runner script."""
    if len(sys.argv) < 6:
        print("Usage: python -m src.compare.runner <TICKER> <START> <END> <ALGO_ID> <OUT_PNG>")
        return 2

    ticker = sys.argv[1]
    start = datetime.fromisoformat(sys.argv[2]).date()
    end = datetime.fromisoformat(sys.argv[3]).date()
    algo_id = sys.argv[4]
    out_png = sys.argv[5]

    # Load price history using the modern Asset class
    df = Asset(ticker).get_prices(start, end)
    if df.empty:
        print(f"Error: No price data found for {ticker} in the given date range.")
        return 1

    algo = build_algo_from_name(algo_id)

    txs, summary = run_algorithm_backtest(
        df, ticker, initial_qty=10000, start_date=start, end_date=end, algo=algo
    )

    # Write transactions to a small file next to PNG and prepare stable string lines
    tx_file = os.path.splitext(out_png)[0] + "-tx.txt"
    tx_lines = []
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
        # Fallback: try common attributes used by transaction types
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
            # Standardized format: YYYY-MM-DD ACTION QTY @ PRICE TICKER
            tx_lines.append(
                f"{date_str} {action.upper()} {qty} @ {price:.2f} {ticker_attr or ''}".strip()
            )
            continue
        # Last resort: use str()
        tx_lines.append(str(t))
    with open(tx_file, "w") as f:
        for line in tx_lines:
            f.write(line + "\n")

    # plot with markers (plotter expects a list of string lines)
    # Pass the summary so the plotter can annotate metrics like volatility alpha.
    plot_price_with_trades(df, tx_lines, ticker, out_png, summary)

    print(f"Wrote {out_png} and {tx_file}")
    print("Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())