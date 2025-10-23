"""Simple compare runner: runs one backtest and produces a price chart with trades.

Usage (from repo root):
  python -m src.compare.runner NVDA 2024-10-27 2025-10-27 synthetic-dividend/9.05%/50% out.png
"""

import os
import sys
from datetime import datetime

# Add the app root to sys.path so we can import from src
_app_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _app_root not in sys.path:
    sys.path.insert(0, _app_root)

from src.compare.plotter import plot_price_with_trades
from src.data.fetcher import HistoryFetcher
from src.models.backtest import build_algo_from_name, run_algorithm_backtest


def main(argv):
    if len(argv) < 6:
        print("Usage: runner.py <TICKER> <START> <END> <ALGO_ID> <OUT_PNG>")
        return 2

    ticker = argv[1]
    start = datetime.fromisoformat(argv[2]).date()
    end = datetime.fromisoformat(argv[3]).date()
    algo_id = argv[4]
    out_png = argv[5]

    # load price history (uses fetcher cache)
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start, end)
    algo = build_algo_from_name(algo_id)

    txs, summary = run_algorithm_backtest(
        df, ticker, initial_qty=10000, start_date=start, end_date=end, algo=algo
    )

    # write transactions to a small file next to PNG
    tx_file = os.path.splitext(out_png)[0] + "-tx.txt"
    with open(tx_file, "w") as f:
        for t in txs:
            f.write(t + "\n")

    # plot with markers
    plot_price_with_trades(df, txs, ticker, out_png)

    print(f"Wrote {out_png} and {tx_file}")
    print("Summary:")
    for k, v in summary.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
