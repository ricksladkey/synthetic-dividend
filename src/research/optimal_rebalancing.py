#!/usr/bin/env python3
"""Multi-asset optimal rebalancing research script.

Tests various sdN configurations across different asset classes to determine
optimal rebalancing frequencies for different volatility regimes.

Usage:
    python -m src.research.optimal_rebalancing --start 2020-01-01 --end 2025-01-01 --output research_results.csv
    python -m src.research.optimal_rebalancing --ticker NVDA --quick  # Quick test on single asset
"""
import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.data.fetcher import HistoryFetcher  # noqa: E402
from src.algorithms.factory import build_algo_from_name  # noqa: E402
from src.models.backtest import run_algorithm_backtest  # noqa: E402
from src.research.asset_classes import (  # noqa: E402
    ASSET_CLASSES,
    get_class_for_ticker,
    get_recommended_sd_values,
    print_sd_reference_table,
)


def parse_date(s: str) -> date:
    """Parse date string in MM/DD/YYYY or YYYY-MM-DD format."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    raise ValueError(f"Unrecognized date format: {s}")


def run_single_backtest(
    ticker: str,
    start_date: date,
    end_date: date,
    sd_n: int,
    profit_pct: float = 50.0,
    initial_qty: int = 10000,
) -> Optional[Dict]:
    """Run backtest for single asset and sdN configuration.

    Returns:
        Dictionary with results or None if data unavailable
    """
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        print(f"  [WARNING] No data for {ticker}")
        return None

    # Build strategy name
    if profit_pct == 50.0:
        strategy = f"sd{sd_n}"
    else:
        strategy = f"sd{sd_n},{profit_pct}"

    algo = build_algo_from_name(strategy)

    try:
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=ticker,
            initial_qty=initial_qty,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )

        # Extract key metrics from summary dict
        # Note: summary uses 'total_return' (decimal), 'holdings', 'bank', etc.
        # Convert to percentage and use correct key names
        total_return_pct = summary.get("total_return", 0) * 100  # Convert to percentage
        volatility_alpha_pct = summary.get("volatility_alpha", 0) * 100
        transaction_count = len(transactions)  # Count transactions (excluding initial buy)

        # Get algorithm trigger percentage if available (from algo object)
        rebalance_trigger = 0
        if hasattr(algo, "alpha_pct"):
            rebalance_trigger = algo.alpha_pct

        result = {
            "ticker": ticker,
            "asset_class": get_class_for_ticker(ticker),
            "strategy": strategy,
            "sd_n": sd_n,
            "profit_pct": profit_pct,
            "rebalance_trigger": rebalance_trigger,
            "total_return_pct": total_return_pct,
            "volatility_alpha_pct": volatility_alpha_pct,
            "max_drawdown_pct": 0,  # TODO: Calculate from bank/holdings history
            "sharpe_ratio": 0,  # TODO: Calculate from daily returns
            "transaction_count": transaction_count,
            "final_holdings": summary.get("holdings", 0),
            "final_bank": summary.get("bank", 0),
            "final_value": summary.get("total", 0),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }

        return result

    except Exception as e:
        print(f"  [ERROR] Error backtesting {ticker} with {strategy}: {e}")
        return None


def run_asset_class_sweep(
    asset_class_name: str,
    start_date: date,
    end_date: date,
    profit_pct: float = 50.0,
    initial_qty: int = 10000,
) -> List[Dict]:
    """Run all recommended sdN values for all tickers in an asset class."""
    print(f"\n{'='*70}")
    print(f"ASSET CLASS: {asset_class_name.upper()}")
    print(f"{'='*70}")

    results = []
    asset_class = ASSET_CLASSES[asset_class_name]
    tickers = asset_class["tickers"]
    recommended_sd = asset_class["recommended_sd"]

    for ticker in tickers:
        print(f"\n[{ticker}] ({asset_class_name}):")
        for sd_n in recommended_sd:
            result = run_single_backtest(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                sd_n=sd_n,
                profit_pct=profit_pct,
                initial_qty=initial_qty,
            )
            if result:
                results.append(result)
                print(
                    f"  [OK] sd{sd_n}: {result['total_return_pct']:.2f}% return, "
                    f"{result['transaction_count']} txns, "
                    f"{result['max_drawdown_pct']:.2f}% max drawdown"
                )

    return results


def run_comprehensive_sweep(
    start_date: date,
    end_date: date,
    profit_pct: float = 50.0,
    initial_qty: int = 10000,
) -> List[Dict]:
    """Run all asset classes with their recommended sdN values."""
    all_results = []

    print_sd_reference_table()

    for asset_class_name in ASSET_CLASSES.keys():
        results = run_asset_class_sweep(
            asset_class_name=asset_class_name,
            start_date=start_date,
            end_date=end_date,
            profit_pct=profit_pct,
            initial_qty=initial_qty,
        )
        all_results.extend(results)

    return all_results


def save_results_to_csv(results: List[Dict], output_path: str):
    """Save results to CSV file."""
    if not results:
        print("[WARNING] No results to save")
        return

    fieldnames = [
        "ticker",
        "asset_class",
        "strategy",
        "sd_n",
        "profit_pct",
        "rebalance_trigger",
        "total_return_pct",
        "volatility_alpha_pct",
        "max_drawdown_pct",
        "sharpe_ratio",
        "transaction_count",
        "final_holdings",
        "final_bank",
        "final_value",
        "start_date",
        "end_date",
    ]

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[OK] Results saved to: {output_path}")
    print(f"   Total records: {len(results)}")


def print_summary_analysis(results: List[Dict]):
    """Print summary analysis of results."""
    if not results:
        return

    df = pd.DataFrame(results)

    print(f"\n{'='*70}")
    print("SUMMARY ANALYSIS")
    print(f"{'='*70}\n")

    # Best performing sdN per asset class
    print("OPTIMAL sdN BY ASSET CLASS (by total return):")
    print("-" * 70)
    for asset_class in df["asset_class"].unique():
        class_data = df[df["asset_class"] == asset_class]
        best_row = class_data.loc[class_data["total_return_pct"].idxmax()]
        print(
            f"{asset_class:20s}: sd{int(best_row['sd_n'])} "
            f"({best_row['total_return_pct']:.2f}% return)"
        )

    print("\n" + "=" * 70)


def main():
    """Command-line interface for optimal rebalancing research."""
    parser = argparse.ArgumentParser(
        description="Research optimal rebalancing frequencies across asset classes",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--start",
        default="2020-01-01",
        help="Start date (YYYY-MM-DD or MM/DD/YYYY)",
    )
    parser.add_argument(
        "--end",
        default="2025-01-01",
        help="End date (YYYY-MM-DD or MM/DD/YYYY)",
    )
    parser.add_argument(
        "--output",
        default="optimal_rebalancing_results.csv",
        help="Output CSV filename",
    )
    parser.add_argument(
        "--ticker",
        help="Test single ticker only (with all recommended sdN values)",
    )
    parser.add_argument(
        "--asset-class",
        choices=list(ASSET_CLASSES.keys()),
        help="Test single asset class only",
    )
    parser.add_argument(
        "--profit",
        type=float,
        default=50.0,
        help="Profit sharing percentage (default: 50)",
    )
    parser.add_argument(
        "--qty",
        type=int,
        default=10000,
        help="Initial quantity of shares (default: 10000)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick test: 1-year lookback from end date",
    )

    args = parser.parse_args()

    # Parse dates
    end_date = parse_date(args.end)
    if args.quick:
        start_date = date(end_date.year - 1, end_date.month, end_date.day)
    else:
        start_date = parse_date(args.start)

    print("\nOPTIMAL REBALANCING RESEARCH")
    print(f"Date Range: {start_date} to {end_date}")
    print(f"Profit Sharing: {args.profit}%")
    print(f"Initial Quantity: {args.qty:,} shares\n")

    # Run appropriate sweep
    if args.ticker:
        # Single ticker test
        print(f"Testing single ticker: {args.ticker}")
        sd_values = get_recommended_sd_values(args.ticker)
        results = []
        for sd_n in sd_values:
            result = run_single_backtest(
                ticker=args.ticker,
                start_date=start_date,
                end_date=end_date,
                sd_n=sd_n,
                profit_pct=args.profit,
                initial_qty=args.qty,
            )
            if result:
                results.append(result)

    elif args.asset_class:
        # Single asset class test
        results = run_asset_class_sweep(
            asset_class_name=args.asset_class,
            start_date=start_date,
            end_date=end_date,
            profit_pct=args.profit,
            initial_qty=args.qty,
        )

    else:
        # Comprehensive sweep
        results = run_comprehensive_sweep(
            start_date=start_date,
            end_date=end_date,
            profit_pct=args.profit,
            initial_qty=args.qty,
        )

    # Save and analyze results
    if results:
        save_results_to_csv(results, args.output)
        print_summary_analysis(results)
    else:
        print("[ERROR] No results generated")

    return 0


if __name__ == "__main__":
    sys.exit(main())
