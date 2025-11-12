#!/usr/bin/env python3
"""
Demo: Volatility Alpha Curves using test data from testdata/ directory.

This demonstrates the volatility alpha visualization using the test data
that ships with the project (2023 data for NVDA and SPY).

Usage:
    python scripts/demo_volatility_alpha_curves.py
    python scripts/demo_volatility_alpha_curves.py --realized-only
"""

import argparse
import sys
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.algorithms.factory import build_algo_from_name
from src.models.backtest import run_algorithm_backtest

# SDN parameters to test
SDN_RANGE = [4, 6, 8, 10, 12, 16, 20, 24, 32]

# Test data available
TEST_TICKERS = ["NVDA", "SPY"]


def load_test_data(ticker: str) -> pd.DataFrame:
    """Load test data from testdata directory."""
    testdata_dir = Path(__file__).parent.parent / "testdata"
    csv_path = testdata_dir / f"{ticker}.csv"

    df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    return df


def run_backtest_with_test_data(ticker: str, sd_n: int) -> dict:
    """Run backtest using test data."""
    df = load_test_data(ticker)

    # Determine date range from data
    start_date = df.index[0].date()
    end_date = df.index[-1].date()

    # Build algorithm
    strategy = f"sd{sd_n}"
    algo = build_algo_from_name(strategy)

    try:
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=ticker,
            initial_qty=10000,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )

        # Extract metrics
        total_return_pct = summary.get("total_return", 0) * 100
        transaction_count = len([t for t in transactions if t.action in ["BUY", "SELL"]])

        # Get volatility alpha from algorithm (prefer realized over estimated)
        realized_vol_alpha = 0.0
        unrealized_vol_alpha = 0.0
        total_vol_alpha = 0.0

        if hasattr(algo, "realized_volatility_alpha"):
            realized_vol_alpha = algo.realized_volatility_alpha
        if hasattr(algo, "unrealized_stack_alpha"):
            unrealized_vol_alpha = algo.unrealized_stack_alpha
        if hasattr(algo, "total_volatility_alpha"):
            total_vol_alpha = algo.total_volatility_alpha

        stack_size = 0
        if hasattr(algo, "buyback_stack_count"):
            stack_size = algo.buyback_stack_count

        print(
            f"  sd{sd_n:2d}: return={total_return_pct:7.2f}%, "
            f"realized_alpha={realized_vol_alpha:6.2f}%, "
            f"unrealized={unrealized_vol_alpha:6.2f}%, "
            f"txns={transaction_count:3d}, stack={stack_size}"
        )

        return {
            "ticker": ticker,
            "sd_n": sd_n,
            "total_return_pct": total_return_pct,
            "realized_vol_alpha_pct": realized_vol_alpha,
            "unrealized_vol_alpha_pct": unrealized_vol_alpha,
            "total_vol_alpha_pct": total_vol_alpha,
            "transaction_count": transaction_count,
            "buyback_stack_size": stack_size,
        }
    except Exception as e:
        print(f"  sd{sd_n:2d}: ERROR - {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Generate volatility alpha curves from test data")
    parser.add_argument(
        "--realized-only",
        action="store_true",
        help="Plot only realized alpha (default: show both realized and total)",
    )
    args = parser.parse_args()

    print("=" * 70)
    print("DEMO: VOLATILITY ALPHA CURVES (using 2023 test data)")
    if args.realized_only:
        print("Mode: REALIZED ALPHA ONLY")
    else:
        print("Mode: BOTH REALIZED AND TOTAL ALPHA")
    print("=" * 70)

    # Collect results
    all_results = {}

    for ticker in TEST_TICKERS:
        print(f"\n[{ticker}] Running sweep across sdN parameters:")
        all_results[ticker] = []

        for sd_n in SDN_RANGE:
            result = run_backtest_with_test_data(ticker, sd_n)
            if result:
                all_results[ticker].append(result)

        # Print best
        if all_results[ticker]:
            best = max(all_results[ticker], key=lambda r: r["realized_vol_alpha_pct"])
            print(
                f"  ➜ Best REALIZED: sd{best['sd_n']} with "
                f"{best['realized_vol_alpha_pct']:.2f}% alpha"
            )
            if not args.realized_only:
                best_total = max(all_results[ticker], key=lambda r: r["total_vol_alpha_pct"])
                print(
                    f"  ➜ Best TOTAL: sd{best_total['sd_n']} with "
                    f"{best_total['total_vol_alpha_pct']:.2f}% alpha "
                    f"({best_total['unrealized_vol_alpha_pct']:.2f}% unrealized)"
                )

    # Create plot
    print(f"\n{'=' * 70}")
    print("Generating visualization...")
    print(f"{'=' * 70}\n")

    fig, ax = plt.subplots(figsize=(12, 7))

    if args.realized_only:
        title = (
            "Volatility Alpha vs SDN Parameter (2023 Test Data)\n"
            "REALIZED Alpha Only (Banked Profits from Completed Cycles)"
        )
        ylabel = "Realized Volatility Alpha (%)"
    else:
        title = (
            "Volatility Alpha vs SDN Parameter (2023 Test Data)\n"
            "Solid = Realized (Banked) | Dashed = Total (Realized + Unrealized Stack)"
        )
        ylabel = "Volatility Alpha (%)"

    fig.suptitle(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("SDN Parameter", fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.grid(True, alpha=0.3)

    # Color map
    colors = {"NVDA": "#76B900", "SPY": "#005eb8"}  # NVIDIA green, S&P blue

    # Plot each ticker
    for ticker in TEST_TICKERS:
        if not all_results[ticker]:
            continue

        results = all_results[ticker]
        sdn_values = [r["sd_n"] for r in results]
        realized_values = [r["realized_vol_alpha_pct"] for r in results]
        total_values = [r["total_vol_alpha_pct"] for r in results]

        # Sort by sdN
        sorted_data = sorted(zip(sdn_values, realized_values, total_values))
        sdn_values, realized_values, total_values = zip(*sorted_data)

        color = colors.get(ticker, "gray")

        # Plot realized alpha (solid line)
        ax.plot(
            sdn_values,
            realized_values,
            marker="o",
            linewidth=2.5,
            markersize=8,
            label=f"{ticker} (realized)",
            color=color,
            linestyle="-",
        )

        # Mark the realized peak
        max_realized_idx = realized_values.index(max(realized_values))
        ax.plot(
            sdn_values[max_realized_idx],
            realized_values[max_realized_idx],
            marker="*",
            markersize=20,
            color=color,
            markeredgecolor="black",
            markeredgewidth=2,
            zorder=10,
        )

        # Plot total alpha (dashed line) if not realized-only mode
        if not args.realized_only:
            ax.plot(
                sdn_values,
                total_values,
                marker="s",
                linewidth=2.0,
                markersize=6,
                label=f"{ticker} (total)",
                color=color,
                linestyle="--",
                alpha=0.6,
            )

    # Customize axes
    ax.set_xticks(SDN_RANGE)
    ax.set_xlim(3, 33)
    ax.legend(loc="best", fontsize=11, framealpha=0.9)

    # Add explanatory text
    if args.realized_only:
        explanation = (
            "REALIZED alpha = actual cash profits from completed buy-sell cycles\n"
            "Hump-shaped curves show practical optimal sdN for each ticker\n"
            "Peak = maximum bankable profits (not paper gains in stack)"
        )
    else:
        explanation = (
            "REALIZED (solid) = banked cash from unwound cycles\n"
            "TOTAL (dashed) = realized + unrealized paper gains in stack\n"
            "Note: Total approaches stable limit as brackets shrink (1/4 alpha × ~4× txns)"
        )

    ax.text(
        0.02,
        0.98,
        explanation,
        transform=ax.transAxes,
        fontsize=9,
        verticalalignment="top",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.5),
    )

    plt.tight_layout()
    output_path = "volatility_alpha_curves_demo.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"✅ Saved plot to: {output_path}")

    # Also save as PDF for publication quality
    pdf_path = "volatility_alpha_curves_demo.pdf"
    plt.savefig(pdf_path, bbox_inches="tight")
    print(f"✅ Saved PDF to: {pdf_path}")


if __name__ == "__main__":
    main()
