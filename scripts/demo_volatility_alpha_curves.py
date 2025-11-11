#!/usr/bin/env python3
"""
Demo: Volatility Alpha Curves using test data from testdata/ directory.

This demonstrates the volatility alpha visualization using the test data
that ships with the project (2023 data for NVDA and SPY).
"""

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

        # Get volatility alpha from algorithm
        estimated_vol_alpha = 0.0
        if hasattr(algo, "total_volatility_alpha"):
            estimated_vol_alpha = algo.total_volatility_alpha

        stack_size = 0
        if hasattr(algo, "buyback_stack_count"):
            stack_size = algo.buyback_stack_count

        print(
            f"  sd{sd_n:2d}: return={total_return_pct:7.2f}%, "
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
        print(f"  sd{sd_n:2d}: ERROR - {e}")
        return None


def main():
    print("=" * 70)
    print("DEMO: VOLATILITY ALPHA CURVES (using 2023 test data)")
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
            best = max(all_results[ticker], key=lambda r: r["estimated_vol_alpha_pct"])
            print(
                f"  ➜ Best: sd{best['sd_n']} with "
                f"{best['estimated_vol_alpha_pct']:.2f}% volatility alpha"
            )

    # Create plot
    print(f"\n{'=' * 70}")
    print("Generating visualization...")
    print(f"{'=' * 70}\n")

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.suptitle(
        "Volatility Alpha vs SDN Parameter (2023 Test Data)\n"
        "Estimated: Realized + Unrealized from Buyback Stack",
        fontsize=14,
        fontweight="bold",
    )

    ax.set_xlabel("SDN Parameter", fontsize=12)
    ax.set_ylabel("Estimated Volatility Alpha (%)", fontsize=12)
    ax.grid(True, alpha=0.3)

    # Color map
    colors = {"NVDA": "#76B900", "SPY": "#005eb8"}  # NVIDIA green, S&P blue

    # Plot each ticker
    for ticker in TEST_TICKERS:
        if not all_results[ticker]:
            continue

        results = all_results[ticker]
        sdn_values = [r["sd_n"] for r in results]
        vol_alpha_values = [r["estimated_vol_alpha_pct"] for r in results]

        # Sort by sdN
        sorted_pairs = sorted(zip(sdn_values, vol_alpha_values))
        sdn_values, vol_alpha_values = zip(*sorted_pairs)

        # Plot line
        ax.plot(
            sdn_values,
            vol_alpha_values,
            marker="o",
            linewidth=2.5,
            markersize=8,
            label=ticker,
            color=colors.get(ticker, "gray"),
        )

        # Mark the peak (optimal sdN)
        max_idx = vol_alpha_values.index(max(vol_alpha_values))
        ax.plot(
            sdn_values[max_idx],
            vol_alpha_values[max_idx],
            marker="*",
            markersize=20,
            color=colors.get(ticker, "gray"),
            markeredgecolor="black",
            markeredgewidth=2,
            zorder=10,
        )

        # Annotate peak
        ax.annotate(
            f"sd{sdn_values[max_idx]}\n{vol_alpha_values[max_idx]:.1f}%",
            xy=(sdn_values[max_idx], vol_alpha_values[max_idx]),
            xytext=(10, 10),
            textcoords="offset points",
            fontsize=10,
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.5", facecolor=colors.get(ticker, "gray"), alpha=0.3),
        )

    # Customize axes
    ax.set_xticks(SDN_RANGE)
    ax.set_xlim(3, 33)
    ax.legend(loc="best", fontsize=11, framealpha=0.9)

    # Add explanatory text
    ax.text(
        0.02,
        0.98,
        "Hump-shaped curves show optimal sdN for each ticker\n"
        "Peak = best volatility alpha for that asset's volatility profile",
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
