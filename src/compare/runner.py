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

    # Write transactions to a small file next to PNG
    tx_file = os.path.splitext(out_png)[0] + "-tx.txt"
    with open(tx_file, "w", encoding="utf-8") as f:
        for t in txs:
            f.write(t + "\n")

    # Plot with markers
    plot_price_with_trades(df, txs, ticker, out_png)

    print(f"Wrote {out_png} and {tx_file}")
    print("Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())