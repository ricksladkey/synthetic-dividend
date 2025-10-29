"""
Generate comparison table for different algorithms.

Compares buy-and-hold, sd (full), and sd-ath-only
showing ending shares, value, bank, and total for easy analysis.
"""

import sys
from datetime import date, datetime

import pandas as pd

from src.data.asset import Asset
from src.models.backtest import build_algo_from_name, run_algorithm_backtest


def parse_date(s: str) -> date:
    """Parse date from MM/DD/YYYY or YYYY-MM-DD format."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognized date format: {s}")


def run_comparison_table(
    ticker: str,
    start_date: date,
    end_date: date,
    rebalance_pct: float,
    profit_pct: float,
    initial_qty: int = 10000,
) -> pd.DataFrame:
    """
    Run all three algorithms and return a comparison table.

    Returns DataFrame with columns:
    - Algorithm Name
    - Ending Shares
    - Ending Value
    - Ending Bank
    - Ending Total
    - Total Return %
    """

    # Fetch price data
    df = Asset(ticker).get_prices(start_date, end_date)

    if df is None or df.empty:
        raise ValueError(f"No price data for {ticker}")

    print(f"\n{'='*80}")
    print(f"COMPARISON TABLE: {ticker} from {start_date} to {end_date}")
    print(f"Initial Quantity: {initial_qty:,} shares")
    print(f"Parameters: rebalance={rebalance_pct}%, profit_sharing={profit_pct}%")
    print(f"{'='*80}\n")

    results = []

    # Algorithm configurations (modern comma-based format)
    algorithms = [
        ("Buy and Hold", "buy-and-hold"),
        (f"SD ({rebalance_pct}%/{profit_pct}%)", f"sd-{rebalance_pct},{profit_pct}"),
        (
            f"SD ATH-Only ({rebalance_pct}%/{profit_pct}%)",
            f"sd-ath-only-{rebalance_pct},{profit_pct}",
        ),
    ]

    for algo_name, algo_id in algorithms:
        print(f"Running: {algo_name}...")
        algo = build_algo_from_name(algo_id)
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=ticker,
            initial_qty=initial_qty,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )

        results.append(
            {
                "Algorithm Name": algo_name,
                "Ending Shares": summary["holdings"],
                "Ending Value": summary["end_value"],
                "Ending Bank": summary["bank"],
                "Ending Total": summary["bank"] + summary["end_value"],
                "Total Return %": summary["total_return"] * 100,
                "Annualized Return %": (summary.get("annualized_return", 0) or 0) * 100,
            }
        )
        print("  ✓ Complete\n")

    # Create DataFrame
    df_results = pd.DataFrame(results)

    return df_results


def print_table(df: pd.DataFrame):
    """Pretty print the comparison table."""
    print("\n" + "=" * 80)
    print("RESULTS TABLE")
    print("=" * 80 + "\n")

    # Format the display
    pd.options.display.float_format = "{:,.2f}".format

    # Print with custom formatting
    print(df.to_string(index=False))

    print("\n" + "=" * 80 + "\n")


def main():
    if len(sys.argv) < 6:
        print(
            "Usage: python -m src.compare.table TICKER START END REBALANCE% PROFIT% [INITIAL_QTY]"
        )
        print("Example: python -m src.compare.table NVDA 10/22/2024 10/22/2025 9.05 50 10000")
        sys.exit(1)

    ticker = sys.argv[1]
    start = parse_date(sys.argv[2])
    end = parse_date(sys.argv[3])
    rebalance = float(sys.argv[4])
    profit = float(sys.argv[5])
    initial_qty = int(sys.argv[6]) if len(sys.argv) > 6 else 10000

    df_results = run_comparison_table(ticker, start, end, rebalance, profit, initial_qty)
    print_table(df_results)

    # Additional analysis
    print("\nDIFFERENCES FROM BUY-AND-HOLD:")
    print("-" * 80)

    base_total = df_results.iloc[0]["Ending Total"]
    base_return = df_results.iloc[0]["Total Return %"]

    for i in range(1, len(df_results)):
        algo_name = df_results.iloc[i]["Algorithm Name"]
        algo_total = df_results.iloc[i]["Ending Total"]
        algo_return = df_results.iloc[i]["Total Return %"]

        diff_total = algo_total - base_total
        diff_return = algo_return - base_return

        print(f"\n{algo_name}:")
        print(f"  Total difference: ${diff_total:,.2f} ({diff_return:+.2f}% return)")
        print(f"  Shares held: {df_results.iloc[i]['Ending Shares']:,}")
        print(f"  Bank balance: ${df_results.iloc[i]['Ending Bank']:,.2f}")


if __name__ == "__main__":
    main()
