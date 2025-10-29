"""
Volatility Alpha Research

Compares the best synthetic dividend strategy (with buybacks) against
the all-time-high-    # Build ATH-only algorithm (no buybacks)
    # Use same rebalance trigger as enhanced, but disable buybacks
    ath_name = f"sd-ath-only-{enhanced_algo.alpha_pct},{profit_pct}"
    print(f"\n[2/2] Running ATH-ONLY baseline: {ath_name}")
    ath_algo = build_algo_from_name(ath_name)

    ath_transactions, ath_summary = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        start_date=start_dt,
        end_date=end_dt,
        algo=ath_algo,
    )

    ath_return = ath_summary['total_return'] * 100
    ath_txns = len(ath_transactions)
    ath_final = ath_summary.get('total', 0)to quantify "volatility alpha" - the
extra profit earned by capitalizing on price volatility.

Usage:
    python -m src.research.volatility_alpha --ticker NVDA --start 10/23/2023 --end 10/23/2024
    python -m src.research.volatility_alpha --comprehensive --start 10/23/2023 --end 10/23/2024
"""

import argparse
import csv
import sys
from pathlib import Path
from typing import Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.fetcher import HistoryFetcher  # noqa: E402
from src.algorithms.factory import build_algo_from_name
from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm
from src.models.backtest import run_algorithm_backtest  # noqa: E402

# Asset classes matching Phase 1 research
ASSET_CLASSES = {
    "growth_stocks": ["NVDA", "MSTR", "PLTR", "SHOP", "GOOG"],
    "crypto": ["BTC-USD", "ETH-USD"],
    "commodities": ["GLD", "SLV"],
    "indices": ["SPY", "QQQ", "DIA"],
}

# Best sdN values from Phase 1 research (research_phase1_1year_core.csv)
BEST_SDN = {
    "MSTR": 6,
    "BTC-USD": 4,
    "NVDA": 8,
    "PLTR": 8,
    "ETH-USD": 8,
    "SHOP": 12,
    "GOOG": 6,
    "SLV": 16,
    "GLD": 8,
    "SPY": 10,
    "QQQ": 10,
    "DIA": 10,
}


def run_single_comparison(
    ticker: str, start_date: str, end_date: str, profit_pct: float, initial_qty: int
) -> Optional[dict]:
    """
    Compare best sdN strategy vs ATH-only for a single ticker.

    Returns dict with:
        - ticker
        - asset_class
        - best_sdn
        - enhanced_return_pct (best sdN with buybacks)
        - enhanced_transactions
        - ath_only_return_pct (baseline without buybacks)
        - ath_only_transactions
        - volatility_alpha_pct (difference)
        - alpha_per_transaction (efficiency metric)
    """
    print(f"\n{'='*70}")
    print(f"Analyzing {ticker}: Best sdN vs ATH-Only")
    print(f"{'='*70}")

    # Determine asset class
    asset_class = None
    for cls, tickers in ASSET_CLASSES.items():
        if ticker in tickers:
            asset_class = cls
            break

    # Get best sdN from Phase 1 results
    best_sdn = BEST_SDN.get(ticker)
    if best_sdn is None:
        print(f"ERROR: No best sdN found for {ticker}")
        return None

    # Fetch data once
    print(f"\nFetching {ticker} data from {start_date} to {end_date}...")
    fetcher = HistoryFetcher()

    # Convert string dates to date objects
    from datetime import datetime

    start_dt = datetime.strptime(start_date, "%m/%d/%Y").date()
    end_dt = datetime.strptime(end_date, "%m/%d/%Y").date()

    df = fetcher.get_history(ticker, start_dt, end_dt)
    if df is None or df.empty:
        print(f"ERROR: No data for {ticker}")
        return None

    print(f"  Data points: {len(df)}")
    print(f"  Price range: ${float(df['Close'].min()):.2f} - ${float(df['Close'].max()):.2f}")

    # Build enhanced algorithm (with buybacks)
    enhanced_name = f"sd{best_sdn}"
    print(f"\n[1/2] Running ENHANCED strategy: {enhanced_name}")
    enhanced_algo = build_algo_from_name(enhanced_name)
    assert isinstance(enhanced_algo, SyntheticDividendAlgorithm)
    enhanced_algo.profit_sharing = profit_pct / 100.0  # Convert percentage to decimal

    enhanced_transactions, enhanced_summary = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        start_date=start_dt,
        end_date=end_dt,
        algo=enhanced_algo,
    )

    enhanced_return = enhanced_summary["total_return"] * 100
    enhanced_txns = len(enhanced_transactions)
    enhanced_final = enhanced_summary.get("total", 0)

    print("\n  Enhanced Results:")
    print(f"    Total Return: {enhanced_return:.2f}%")
    print(f"    Transactions: {enhanced_txns}")
    print(f"    Final Value: ${enhanced_final:,.2f}")

    # Build ATH-only algorithm (no buybacks)
    # Use same rebalance trigger as enhanced, but disable buybacks
    rebalance_pct = enhanced_algo.rebalance_size * 100  # Convert decimal to percentage
    ath_name = f"sd-ath-only-{rebalance_pct},{profit_pct}"
    print(f"\n[2/2] Running ATH-ONLY baseline: {ath_name}")
    ath_algo = build_algo_from_name(ath_name)

    ath_transactions, ath_summary = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        start_date=start_dt,
        end_date=end_dt,
        algo=ath_algo,
    )

    ath_return = ath_summary["total_return"] * 100
    ath_txns = len(ath_transactions)
    ath_final = ath_summary.get("total", 0)

    print("\n  ATH-Only Results:")
    print(f"    Total Return: {ath_return:.2f}%")
    print(f"    Transactions: {ath_txns}")
    print(f"    Final Value: ${ath_final:,.2f}")

    # Calculate volatility alpha
    volatility_alpha = enhanced_return - ath_return
    alpha_per_txn = volatility_alpha / enhanced_txns if enhanced_txns > 0 else 0

    print("\n  VOLATILITY ALPHA:")
    print(f"    Extra Return: {volatility_alpha:+.2f}%")
    print(f"    Alpha per Transaction: {alpha_per_txn:+.4f}%")

    if volatility_alpha > 0:
        print(f"    ✓ Enhanced strategy OUTPERFORMS ATH-only by {volatility_alpha:.2f}%")
    elif volatility_alpha < 0:
        print(f"    ✗ Enhanced strategy UNDERPERFORMS ATH-only by {abs(volatility_alpha):.2f}%")
    else:
        print("    = No difference (unusual!)")

    return {
        "ticker": ticker,
        "asset_class": asset_class or "unknown",
        "best_sdn": best_sdn,
        "rebalance_trigger_pct": round(enhanced_algo.rebalance_size * 100, 4),
        "profit_taking_pct": profit_pct,
        # Enhanced (with buybacks)
        "enhanced_return_pct": round(enhanced_return, 2),
        "enhanced_transactions": enhanced_txns,
        "enhanced_final_value": round(enhanced_final, 2),
        # ATH-only (baseline)
        "ath_only_return_pct": round(ath_return, 2),
        "ath_only_transactions": ath_txns,
        "ath_only_final_value": round(ath_final, 2),
        # Volatility alpha
        "volatility_alpha_pct": round(volatility_alpha, 2),
        "alpha_per_transaction": round(alpha_per_txn, 4),
        "alpha_percentage_gain": round(
            (volatility_alpha / ath_return * 100) if ath_return != 0 else 0, 2
        ),
    }


def main():
    """Command-line interface for volatility alpha analysis."""
    parser = argparse.ArgumentParser(
        description="Measure volatility alpha by comparing best sdN vs ATH-only"
    )
    parser.add_argument("--ticker", help="Single ticker to analyze (e.g., NVDA)")
    parser.add_argument(
        "--comprehensive", action="store_true", help="Run all 12 assets from Phase 1 research"
    )
    parser.add_argument("--start", required=True, help="Start date (MM/DD/YYYY)")
    parser.add_argument("--end", required=True, help="End date (MM/DD/YYYY)")
    parser.add_argument(
        "--profit", type=float, default=50.0, help="Profit-taking percentage (default: 50%%)"
    )
    parser.add_argument("--qty", type=int, default=10000, help="Initial quantity (default: 10000)")
    parser.add_argument(
        "--output",
        default="volatility_alpha_results.csv",
        help="Output CSV filename (default: volatility_alpha_results.csv)",
    )

    args = parser.parse_args()

    # Validate inputs
    if not args.ticker and not args.comprehensive:
        print("ERROR: Must specify either --ticker or --comprehensive")
        sys.exit(1)

    if args.ticker and args.comprehensive:
        print("ERROR: Cannot use both --ticker and --comprehensive")
        sys.exit(1)

    # Determine which tickers to run
    if args.comprehensive:
        tickers = [t for tickers in ASSET_CLASSES.values() for t in tickers]
        print(f"Running comprehensive analysis: {len(tickers)} assets")
    else:
        tickers = [args.ticker]
        print(f"Running single asset: {args.ticker}")

    # Run comparisons
    results = []
    for ticker in tickers:
        result = run_single_comparison(ticker, args.start, args.end, args.profit, args.qty)
        if result:
            results.append(result)

    # Save results to CSV
    if results:
        fieldnames = [
            "ticker",
            "asset_class",
            "best_sdn",
            "rebalance_trigger_pct",
            "profit_taking_pct",
            "enhanced_return_pct",
            "enhanced_transactions",
            "enhanced_final_value",
            "ath_only_return_pct",
            "ath_only_transactions",
            "ath_only_final_value",
            "volatility_alpha_pct",
            "alpha_per_transaction",
            "alpha_percentage_gain",
        ]

        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print(f"\n{'='*70}")
        print(f"[OK] Results saved to: {args.output}")
        print(f"   Total records: {len(results)}")
        print(f"{'='*70}")

        # Print summary
        print(f"\n{'='*70}")
        print("VOLATILITY ALPHA SUMMARY")
        print(f"{'='*70}")

        for cls in ASSET_CLASSES.keys():
            cls_results = [r for r in results if r["asset_class"] == cls]
            if cls_results:
                avg_alpha = sum(r["volatility_alpha_pct"] for r in cls_results) / len(cls_results)
                best = max(cls_results, key=lambda r: r["volatility_alpha_pct"])
                print(f"\n{cls.upper().replace('_', ' ')}:")
                print(f"  Average Volatility Alpha: {avg_alpha:+.2f}%")
                print(f"  Best: {best['ticker']} ({best['volatility_alpha_pct']:+.2f}%)")

        overall_avg = sum(r["volatility_alpha_pct"] for r in results) / len(results)
        print(f"\nOVERALL AVERAGE: {overall_avg:+.2f}%")

        positive = sum(1 for r in results if r["volatility_alpha_pct"] > 0)
        print(f"Positive Alpha: {positive}/{len(results)} ({positive/len(results)*100:.1f}%)")

        print(f"\n{'='*70}")
    else:
        print("\nERROR: No results generated")
        sys.exit(1)


if __name__ == "__main__":
    main()
