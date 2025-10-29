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

    # Normalize shorthand legacy algo identifiers used in the example batch file.
    # Accept forms like:
    #   - "ath-only/9.05%/50%"  -> "sd-ath-only/9.05%/50%"
    #   - trailing "/full" is optional and not used by the factory (strip it)
    if algo_id.endswith("/full"):
        algo_id = algo_id[: -len("/full")]
    if algo_id.startswith("ath-only/"):
        algo_id = "sd-ath-only/" + algo_id.split("ath-only/", 1)[1]
    # If ATH-only provided with only rebalance percent (no profit sharing),
    # assume default 50% profit sharing (legacy shorthand used in the .bat).
    if algo_id.startswith("sd-ath-only/") and algo_id.count("%") == 1:
        algo_id = algo_id + "/50%"

    # load price history (uses fetcher cache)
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start, end)
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
            tx_lines.append(f"{date_str} {action.upper()} {qty} @ {price:.2f} {ticker_attr or ''}".strip())
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


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
