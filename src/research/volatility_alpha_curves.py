#!/usr/bin/env python3
"""
Volatility Alpha Curves - Visualize optimal sdN parameter for different tickers.

This script generates plots showing the relationship between sdN parameter and
volatility alpha for various tickers. Each ticker should show a hump-shaped curve
with the peak representing the optimal sdN parameter for that asset's volatility profile.

The "estimated future volatility alpha" metric includes both realized (unwound buybacks)
and unrealized (current buyback stack) gains, making it comparable across different
time frames.

Usage:
    python -m src.research.volatility_alpha_curves --output volatility_alpha_curves.png
    python -m src.research.volatility_alpha_curves --tickers NVDA BTC-USD GLDM --year 2024
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.algorithms.factory import build_algo_from_name  # noqa: E402
from src.data.fetcher import HistoryFetcher  # noqa: E402
from src.models.backtest import run_algorithm_backtest  # noqa: E402


# SDN parameters to test (covering the full spectrum)
SDN_RANGE = [4, 6, 8, 10, 12, 16, 20, 24, 32]

# Default tickers spanning different volatility profiles
DEFAULT_TICKERS = [
    "BTC-USD",  # Crypto - very high volatility
    "NVDA",  # Growth tech - high volatility
    "SOUN",  # Small cap growth - high volatility
    "APP",  # Small cap growth - high volatility
    "GLDM",  # Gold ETF - low volatility
    "SPY",  # S&P 500 - moderate volatility
]

# Time periods for analysis
TIME_PERIODS = {
    "2023": (date(2023, 1, 1), date(2023, 12, 31)),
    "2024": (date(2024, 1, 1), date(2024, 12, 31)),
    "2025_YTD": (date(2025, 1, 1), date.today()),
}


def run_backtest_for_sdn(
    ticker: str,
    start_date: date,
    end_date: date,
    sd_n: int,
    profit_pct: float = 50.0,
    initial_qty: int = 10000,
) -> Optional[Dict]:
    """
    Run backtest for a single ticker and sdN parameter.

    Returns:
        Dictionary with metrics including estimated volatility alpha
        (realized + unrealized from buyback stack)
    """
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        print(f"    [SKIP] {ticker} sd{sd_n}: No data available")
        return None

    # Build algorithm
    strategy = f"sd{sd_n}" if profit_pct == 50.0 else f"sd{sd_n},{profit_pct}"
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

        # Extract key metrics
        total_return_pct = summary.get("total_return", 0) * 100
        transaction_count = len([t for t in transactions if t.action in ["BUY", "SELL"]])

        # Get volatility alpha from algorithm
        # This includes both realized (sold buybacks) and unrealized (stack value)
        estimated_vol_alpha = 0.0
        if hasattr(algo, "total_volatility_alpha"):
            estimated_vol_alpha = algo.total_volatility_alpha

        # Get buyback stack count (for diagnostics)
        stack_size = 0
        if hasattr(algo, "buyback_stack_count"):
            stack_size = algo.buyback_stack_count

        print(
            f"    sd{sd_n:2d}: return={total_return_pct:7.2f}%, "
            f"vol_alpha={estimated_vol_alpha:6.2f}%, "
            f"txns={transaction_count:3d}, stack={stack_size}"
        )

        return {
            "ticker": ticker,
            "sd_n": sd_n,
            "total_return_pct": total_return_pct,
            "estimated_vol_alpha_pct": estimated_vol_alpha,
            "transaction_count": transaction_count,
            "buyback_stack_size": stack_size,
        }

    except Exception as e:
        print(f"    [ERROR] sd{sd_n}: {e}")
        return None


def sweep_sdn_parameters(
    ticker: str,
    start_date: date,
    end_date: date,
    sdn_range: List[int] = SDN_RANGE,
    profit_pct: float = 50.0,
) -> List[Dict]:
    """
    Sweep across all sdN parameters for a single ticker.

    Returns:
        List of result dictionaries, one per sdN parameter
    """
    print(f"\n[{ticker}] {start_date} to {end_date}:")
    results = []

    for sd_n in sdn_range:
        result = run_backtest_for_sdn(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            sd_n=sd_n,
            profit_pct=profit_pct,
        )
        if result:
            results.append(result)

    return results


def create_volatility_alpha_plot(
    all_results: Dict[str, Dict[str, List[Dict]]],
    output_path: str = "volatility_alpha_curves.png",
):
    """
    Create matplotlib figure with volatility alpha curves.

    Args:
        all_results: Nested dict structure:
            {ticker: {period: [result_dicts]}}
        output_path: Path to save the figure
    """
    # Create figure with 3 subplots (one per time period)
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    fig.suptitle(
        "Volatility Alpha vs SDN Parameter\n"
        "(Estimated: Realized + Unrealized from Buyback Stack)",
        fontsize=16,
        fontweight="bold",
    )

    periods = ["2023", "2024", "2025_YTD"]
    period_labels = ["2023 Calendar", "2024 Calendar", "2025 YTD"]

    # Color map for tickers (distinct colors)
    colors = plt.cm.tab10(range(len(DEFAULT_TICKERS)))
    ticker_colors = dict(zip(DEFAULT_TICKERS, colors))

    for idx, (period, period_label) in enumerate(zip(periods, period_labels)):
        ax = axes[idx]
        ax.set_title(period_label, fontsize=14, fontweight="bold")
        ax.set_xlabel("SDN Parameter", fontsize=12)
        ax.set_ylabel("Estimated Volatility Alpha (%)", fontsize=12)
        ax.grid(True, alpha=0.3)

        # Plot each ticker
        for ticker in all_results.keys():
            if period not in all_results[ticker]:
                continue

            results = all_results[ticker][period]
            if not results:
                continue

            # Extract data for plotting
            sdn_values = [r["sd_n"] for r in results]
            vol_alpha_values = [r["estimated_vol_alpha_pct"] for r in results]

            # Sort by sdN for clean lines
            sorted_pairs = sorted(zip(sdn_values, vol_alpha_values))
            sdn_values, vol_alpha_values = zip(*sorted_pairs)

            # Plot line with markers
            color = ticker_colors.get(ticker, "gray")
            ax.plot(
                sdn_values,
                vol_alpha_values,
                marker="o",
                linewidth=2,
                markersize=6,
                label=ticker,
                color=color,
            )

            # Find and mark the peak (optimal sdN)
            max_idx = vol_alpha_values.index(max(vol_alpha_values))
            ax.plot(
                sdn_values[max_idx],
                vol_alpha_values[max_idx],
                marker="*",
                markersize=15,
                color=color,
                markeredgecolor="black",
                markeredgewidth=1.5,
                zorder=10,
            )

        # Customize x-axis to show our specific SDN values
        ax.set_xticks(SDN_RANGE)
        ax.set_xlim(3, 33)

        # Add legend
        ax.legend(loc="best", fontsize=10, framealpha=0.9)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"\n✅ Saved plot to: {output_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate volatility alpha curves for multiple tickers"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=DEFAULT_TICKERS,
        help=f"Tickers to analyze (default: {' '.join(DEFAULT_TICKERS)})",
    )
    parser.add_argument(
        "--output",
        default="volatility_alpha_curves.png",
        help="Output file path for the plot",
    )
    parser.add_argument(
        "--sdn-range",
        nargs="+",
        type=int,
        default=SDN_RANGE,
        help=f"SDN parameters to test (default: {' '.join(map(str, SDN_RANGE))})",
    )
    parser.add_argument(
        "--profit-pct",
        type=float,
        default=50.0,
        help="Profit sharing percentage (default: 50.0)",
    )
    parser.add_argument(
        "--periods",
        nargs="+",
        choices=["2023", "2024", "2025_YTD"],
        default=["2023", "2024", "2025_YTD"],
        help="Time periods to analyze",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("VOLATILITY ALPHA CURVES - SDN PARAMETER OPTIMIZATION")
    print("=" * 70)
    print(f"\nTickers: {', '.join(args.tickers)}")
    print(f"SDN Range: {args.sdn_range}")
    print(f"Profit Sharing: {args.profit_pct}%")
    print(f"Periods: {', '.join(args.periods)}\n")

    # Collect results for all tickers and periods
    all_results = {}

    for ticker in args.tickers:
        all_results[ticker] = {}

        for period_name in args.periods:
            start_date, end_date = TIME_PERIODS[period_name]

            results = sweep_sdn_parameters(
                ticker=ticker,
                start_date=start_date,
                end_date=end_date,
                sdn_range=args.sdn_range,
                profit_pct=args.profit_pct,
            )

            all_results[ticker][period_name] = results

            # Print summary
            if results:
                best_result = max(results, key=lambda r: r["estimated_vol_alpha_pct"])
                print(
                    f"  ➜ Best: sd{best_result['sd_n']} with "
                    f"{best_result['estimated_vol_alpha_pct']:.2f}% volatility alpha"
                )

    # Create visualization
    print(f"\n{'=' * 70}")
    print("Generating plot...")
    print(f"{'=' * 70}")
    create_volatility_alpha_plot(all_results, args.output)


if __name__ == "__main__":
    main()
