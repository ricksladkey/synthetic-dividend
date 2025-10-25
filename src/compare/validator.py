"""
Compare full sd with ATH-only variant.

This script validates the symmetry property: at every new ATH,
both algorithms should have the same share count.
"""

import sys
from datetime import date, datetime
from typing import Dict, List, Tuple

import pandas as pd

from src.data.fetcher import HistoryFetcher
from src.models.backtest import build_algo_from_name, run_algorithm_backtest


def parse_date(s: str) -> date:
    """Parse date from MM/DD/YYYY or YYYY-MM-DD format."""
    if "/" in s:
        parts = s.split("/")
        if len(parts) == 3:
            m, d, y = int(parts[0]), int(parts[1]), int(parts[2])
            return date(y, m, d)
    return datetime.strptime(s, "%Y-%m-%d").date()


def extract_holdings_from_transactions(transactions: List[str]) -> List[Tuple[date, int]]:
    """Extract (date, holdings) tuples from transaction strings."""
    holdings_timeline = []
    for tx in transactions:
        # Parse transaction format: "YYYY-MM-DD ACTION qty TICKER @ price = value, holdings = X, bank = Y  # notes"
        parts = tx.split()
        if len(parts) < 10:
            continue

        date_str = parts[0]
        tx_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Find "holdings = X" in the string
        try:
            holdings_idx = parts.index("holdings")
            if holdings_idx + 2 < len(parts):
                # Next token should be "=" and then the holdings count (may have trailing comma)
                holdings_str = parts[holdings_idx + 2].rstrip(",")
                holdings = int(holdings_str)
                holdings_timeline.append((tx_date, holdings))
        except (ValueError, IndexError):
            pass

    return holdings_timeline


def find_ath_dates(df: pd.DataFrame, start_date: date, end_date: date) -> List[Tuple[date, float]]:
    """Find all dates when price reached a new all-time high."""
    df_indexed = df.copy()
    df_indexed.index = pd.to_datetime(df_indexed.index).date

    # Filter to date range
    dates = sorted(d for d in df_indexed.index if d >= start_date and d <= end_date)

    ath_dates = []
    current_ath = 0.0

    for d in dates:
        try:
            row = df_indexed.loc[d]
            # Get High for the day
            if isinstance(row["High"], pd.Series):
                high = float(row["High"].iloc[0])
            else:
                high = float(row["High"])

            if high > current_ath:
                current_ath = high
                ath_dates.append((d, current_ath))
        except Exception:
            continue

    return ath_dates


def compare_algorithms(
    ticker: str,
    start_date: date,
    end_date: date,
    rebalance_pct: float,
    profit_pct: float,
    initial_qty: int = 10000,
) -> Dict:
    """Compare full sd with ATH-only variant."""

    # Fetch price data
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        raise ValueError(f"No price data for {ticker}")

    # Build algorithm identifiers (modern comma-based format)
    full_algo_name = f"sd-{rebalance_pct},{profit_pct}"
    ath_algo_name = f"sd-ath-only-{rebalance_pct},{profit_pct}"

    print(f"\n{'='*80}")
    print(f"COMPARISON: {ticker} from {start_date} to {end_date}")
    print(f"Parameters: rebalance={rebalance_pct}%, profit_sharing={profit_pct}%")
    print(f"{'='*80}\n")

    # Run full sd algorithm
    print(f"Running FULL algorithm: {full_algo_name}")
    print("-" * 80)
    full_algo = build_algo_from_name(full_algo_name)
    full_tx, full_summary = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        start_date=start_date,
        end_date=end_date,
        algo=full_algo,
    )
    print("\nFull algorithm results:")
    print(f"  Transactions: {len(full_tx)}")
    print(f"  Final holdings: {full_summary['holdings']} shares")
    print(f"  Final bank: ${full_summary['bank']:.2f}")
    print(f"  Total return: {full_summary['total_return']*100:.2f}%")

    # Run ATH-only
    print("\n\nRunning ATH-ONLY algorithm: {ath_algo_name}")
    print("-" * 80)
    ath_algo = build_algo_from_name(ath_algo_name)
    ath_tx, ath_summary = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        start_date=start_date,
        end_date=end_date,
        algo=ath_algo,
    )
    print("\nATH-only algorithm results:")
    print(f"  Transactions: {len(ath_tx)}")
    print(f"  Final holdings: {ath_summary['holdings']} shares")
    print(f"  Final bank: ${ath_summary['bank']:.2f}")
    print(f"  Total return: {ath_summary['total_return']*100:.2f}%")

    # Extract holdings timelines
    full_holdings = extract_holdings_from_transactions(full_tx)
    ath_holdings = extract_holdings_from_transactions(ath_tx)

    # Find ATH dates
    ath_dates = find_ath_dates(df, start_date, end_date)

    print("\n\n" + "=" * 80)
    print("VALIDATION: Holdings at each ATH")
    print("=" * 80)

    # Build holdings lookup dictionaries (unused but kept for potential future use)
    # full_holdings_dict = dict(full_holdings)
    # ath_holdings_dict = dict(ath_holdings)

    validation_passed = True
    for ath_date, ath_price in ath_dates:
        # Find holdings on or before this date
        full_h = None
        ath_h = None

        # Find most recent holdings at or before ath_date
        for d, h in reversed(full_holdings):
            if d <= ath_date:
                full_h = h
                break

        for d, h in reversed(ath_holdings):
            if d <= ath_date:
                ath_h = h
                break

        match = "✓" if full_h == ath_h else "✗"
        print(f"{ath_date} (ATH=${ath_price:.2f}): Full={full_h}, ATH-only={ath_h} {match}")

        if full_h != ath_h:
            validation_passed = False

    print(f"\n{'='*80}")
    if validation_passed:
        print("✓ VALIDATION PASSED: Holdings match at all ATH dates")
    else:
        print("✗ VALIDATION FAILED: Holdings mismatch at some ATH dates")
    print(f"{'='*80}\n")

    # Calculate buyback/resell symmetry for full algorithm
    buyback_count = 0
    resell_count = 0

    for tx in full_tx[1:]:  # Skip initial buy
        if " BUY " in tx and "Buying back" in tx:
            buyback_count += 1
        elif " SELL " in tx and "Taking profits" in tx:
            parts = tx.split()
            if len(parts) >= 3:
                # qty_str = parts[2]  # Unused - kept for reference
                # Check if this is a buyback resell (not an ATH sell)
                # ATH sells would have higher holdings in ATH-only at same date
                # For now, count all non-ATH sells
                if "ATH-only" not in tx:
                    resell_count += 1

    print("\nFull algorithm buyback/resell analysis:")
    print(f"  Buyback transactions: {buyback_count}")
    print(f"  Taking-profit transactions: {resell_count}")
    print(f"  Net extra transactions: {buyback_count + resell_count}")

    return {
        "validation_passed": validation_passed,
        "full_transactions": len(full_tx),
        "ath_transactions": len(ath_tx),
        "full_holdings": full_summary["holdings"],
        "ath_holdings": ath_summary["holdings"],
        "full_return": full_summary["total_return"],
        "ath_return": ath_summary["total_return"],
        "buyback_count": buyback_count,
        "resell_count": resell_count,
    }


def main():
    if len(sys.argv) < 6:
        print("Usage: python -m src.compare.validator TICKER START END REBALANCE% PROFIT%")
        print("Example: python -m src.compare.validator NVDA 10/22/2024 10/22/2025 9.05 50")
        sys.exit(1)

    ticker = sys.argv[1]
    start = parse_date(sys.argv[2])
    end = parse_date(sys.argv[3])
    rebalance = float(sys.argv[4])
    profit = float(sys.argv[5])

    result = compare_algorithms(ticker, start, end, rebalance, profit)

    sys.exit(0 if result["validation_passed"] else 1)


if __name__ == "__main__":
    main()
