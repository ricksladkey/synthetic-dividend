#!/usr/bin/env python3
"""
Volatility Alpha Curves with Realistic Retail Constraints.

Tests different sdN parameters with:
- No margin (can't borrow beyond available cash)
- 10% CASH allocation earning BIL interest (~4-5% APY)
- 90% stock allocation

This shows how the optimal sdN changes under realistic constraints
compared to the unrealistic "infinite margin" assumption.

Expected results vs. old unlimited margin mode:
┌─────────────────────────────────────────────────────────────────────┐
│                 OLD (Unlimited Margin)  │  NEW (Retail Constraints) │
├─────────────────────────────────────────┼───────────────────────────┤
│ sd4:  Good, but leaves money on table   │  BETTER (captures gaps!)  │
│ sd8:  Optimal (captures gaps + vol)     │  Optimal (still best)     │
│ sd16: Worse (misses gaps, more txns)    │  Worse (cash constraints)│
│ sd32: CATASTROPHIC (-2874% margin!)     │  BLOCKED (no margin!)     │
└─────────────────────────────────────────────────────────────────────┘

Key differences:
1. sd32 can't use massive margin → Many skipped buys
2. sd16-sd20 hit cash constraints → Lower returns
3. sd8 remains optimal → Balanced gap capture + safety
4. CASH earns ~4-5% BIL yields → Reduces opportunity cost
5. Skipped buys protect against catastrophic losses

NOTE: This script requires network access to fetch BIL data.
      If yfinance API is blocking, data must be pre-cached.
"""

import sys
import traceback
from datetime import date
from pathlib import Path

import matplotlib.pyplot as plt

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.simulation import run_portfolio_simulation

# SDN parameters to test
SDN_RANGE = [8, 9, 10, 11, 12, 13, 14, 15, 16]

# Test ticker (using cached 2023 data)
TEST_TICKER = "NVDA"
CASH_ALLOCATION = 0.10  # 10% cash reserve (Warren Buffett's 90/10)


def run_retail_backtest(ticker: str, sd_n: int, cash_pct: float = 0.10) -> dict:
    """
    Run portfolio simulation with realistic retail constraints.

    Args:
        ticker: Stock ticker
        sd_n: Synthetic dividend parameter (e.g., 8 for sd8)
        cash_pct: Cash allocation percentage (default 10%)

    Returns:
        Dictionary with performance metrics
    """
    print(f"Testing sd{sd_n} with {cash_pct*100:.0f}% CASH... ", end="", flush=True)

    try:
        result = run_portfolio_simulation(
            allocations={
                ticker: 1.0 - cash_pct,
                "CASH": cash_pct,
            },
            initial_investment=1_000_000,
            # allow_margin defaults to False (retail mode)
            start_date=date(2023, 1, 3),
            end_date=date(2025, 11, 12),
            portfolio_algo=f"per-asset:sd{sd_n}",
        )

        txns, stats = result

        # Calculate metrics
        total_return_pct = ((stats['total_final_value'] / 1_000_000) - 1) * 100
        bank_min = stats.get('bank_min', 0)
        bank_max = stats.get('bank_max', 0)
        skipped_buys = stats.get('skipped_count', 0)

        # Count transactions by ticker
        stock_txns = [t for t in txns if t.ticker == ticker and t.action in ["BUY", "SELL"]]
        cash_interest = [t for t in txns if t.ticker == "CASH" and t.action == "INTEREST"]

        # Get CASH interest earned
        cash_interest_total = stats.get("total_dividends_by_asset", {}).get("CASH", 0)

        print(f"✓ Return: {total_return_pct:+.1f}%, {len(stock_txns)} txns, {skipped_buys} skipped")

        return {
            "sd_n": sd_n,
            "total_return_pct": total_return_pct,
            "final_value": stats['total_final_value'],
            "final_bank": stats['final_bank'],
            "bank_min": bank_min,
            "bank_max": bank_max,
            "transaction_count": len(stock_txns),
            "skipped_buys": skipped_buys,
            "cash_interest": cash_interest_total,
            "used_margin": bank_min < 0,
        }

    except Exception as e:
        print(f"✗ ERROR: {e}")
        traceback.print_exc()
        return {
            "sd_n": sd_n,
            "total_return_pct": None,
            "error": str(e),
        }


def plot_retail_curves(results: list, ticker: str, cash_pct: float):
    """Plot volatility alpha curves with retail constraints."""
    # Filter successful results
    valid_results = [r for r in results if r.get("total_return_pct") is not None]

    if not valid_results:
        print("No valid results to plot!")
        return

    # Extract data for plotting
    sdn_values = [r["sd_n"] for r in valid_results]
    returns = [r["total_return_pct"] for r in valid_results]
    txn_counts = [r["transaction_count"] for r in valid_results]
    skipped_buys = [r["skipped_buys"] for r in valid_results]
    cash_interest = [r["cash_interest"] for r in valid_results]

    # Create figure with subplots
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(f"Volatility Alpha Curves - {ticker} (2023-2025)\n"
                 f"Retail Mode: No Margin + {cash_pct*100:.0f}% CASH earning BIL interest",
                 fontsize=14, fontweight='bold')

    # Plot 1: Total Returns
    ax1.plot(sdn_values, returns, 'o-', linewidth=2, markersize=8, color='darkgreen')
    ax1.axhline(y=0, color='gray', linestyle='--', alpha=0.5)
    ax1.set_xlabel("sdN Parameter", fontsize=11)
    ax1.set_ylabel("Total Return (%)", fontsize=11)
    ax1.set_title("Portfolio Returns by sdN", fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)

    # Highlight best performer
    best_idx = returns.index(max(returns))
    best_sdn = sdn_values[best_idx]
    ax1.scatter([best_sdn], [returns[best_idx]], color='gold', s=200, zorder=5,
                edgecolors='black', linewidths=2)
    ax1.annotate(f'Best: sd{best_sdn}\n{returns[best_idx]:.1f}%',
                 xy=(best_sdn, returns[best_idx]),
                 xytext=(10, 20), textcoords='offset points',
                 bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                 arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    # Plot 2: Transaction Count
    ax2.bar(sdn_values, txn_counts, color='steelblue', alpha=0.7, edgecolor='black')
    ax2.set_xlabel("sdN Parameter", fontsize=11)
    ax2.set_ylabel("Transaction Count", fontsize=11)
    ax2.set_title("Trading Activity (Busywork)", fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y')

    # Plot 3: Skipped Buys (Cash Constraints)
    ax3.bar(sdn_values, skipped_buys, color='crimson', alpha=0.7, edgecolor='black')
    ax3.set_xlabel("sdN Parameter", fontsize=11)
    ax3.set_ylabel("Skipped Buys", fontsize=11)
    ax3.set_title("Buys Skipped Due to Insufficient Cash", fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3, axis='y')

    if max(skipped_buys) > 0:
        ax3.annotate('Cash constraint\nbinding!',
                     xy=(sdn_values[skipped_buys.index(max(skipped_buys))], max(skipped_buys)),
                     xytext=(10, 10), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.5', fc='yellow', alpha=0.7),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'))

    # Plot 4: CASH Interest Earned
    ax4.bar(sdn_values, cash_interest, color='darkgoldenrod', alpha=0.7, edgecolor='black')
    ax4.set_xlabel("sdN Parameter", fontsize=11)
    ax4.set_ylabel("BIL Interest Earned ($)", fontsize=11)
    ax4.set_title(f"CASH Interest from {cash_pct*100:.0f}% BIL Allocation", fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3, axis='y')

    # Add average interest annotation
    avg_interest = sum(cash_interest) / len(cash_interest)
    ax4.axhline(y=avg_interest, color='red', linestyle='--', alpha=0.7, label=f'Avg: ${avg_interest:,.0f}')
    ax4.legend()

    plt.tight_layout()

    # Save figure
    output_path = Path(__file__).parent.parent / f"volatility_alpha_curves_retail_{ticker.lower()}_2023_2025.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n✓ Saved plot to: {output_path}")

    # Also save PDF
    pdf_path = output_path.with_suffix('.pdf')
    plt.savefig(pdf_path, bbox_inches='tight')
    print(f"✓ Saved PDF to: {pdf_path}")

    plt.show()

    # Print summary table
    print("\n" + "=" * 90)
    print(f"{'SDN':<6} {'Return':<10} {'Txns':<8} {'Skipped':<10} {'BIL Int':<12} {'Margin?':<8}")
    print("=" * 90)
    for r in valid_results:
        margin_str = "YES!" if r.get("used_margin", False) else "No"
        print(f"sd{r['sd_n']:<4} {r['total_return_pct']:>+7.1f}%  "
              f"{r['transaction_count']:>6}   {r['skipped_buys']:>6}     "
              f"${r['cash_interest']:>9,.0f}  {margin_str:<6}")
    print("=" * 90)


def main():
    """Run volatility alpha curves with retail constraints."""
    print("\n" + "=" * 90)
    print(" " * 20 + "VOLATILITY ALPHA CURVES - RETAIL MODE")
    print(" " * 15 + "No Margin + 10% CASH (BIL interest) + 90% Stock")
    print("=" * 90)
    print()

    print(f"Testing {len(SDN_RANGE)} different sdN parameters: {SDN_RANGE}")
    print(f"Ticker: {TEST_TICKER} (2023-2025 data)")
    print(f"Allocations: {(1-CASH_ALLOCATION)*100:.0f}% {TEST_TICKER}, {CASH_ALLOCATION*100:.0f}% CASH")
    print(f"Constraints: allow_margin=False (retail mode)")
    print()

    # Run backtests
    results = []
    for sd_n in SDN_RANGE:
        result = run_retail_backtest(TEST_TICKER, sd_n, CASH_ALLOCATION)
        results.append(result)

    # Plot results
    print("\nGenerating plots...")
    plot_retail_curves(results, TEST_TICKER, CASH_ALLOCATION)

    print("\nDone! 🎯")


if __name__ == "__main__":
    main()
