"""
Profit Sharing Composition Analysis

Explores how different profit-sharing ratios affect holdings composition over time.

Profit Sharing Spectrum:
- Negative (-25% to 0%): Accumulate shares (deploy less than 100% of profits)
- Standard (0% to 50%): Balanced approach
- Aggressive (50% to 100%): Heavy cash extraction
- Extreme (100% to 125%): Deplete core holding over time

This analysis helps understand:
1. Which ratios lead to stable vs unstable strategies
2. How quickly holdings deplete or accumulate
3. The trade-off between cash flow and long-term growth
"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple
import sys

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.backtest import build_algo_from_name, run_algorithm_backtest
from data.fetcher import HistoryFetcher
import matplotlib.pyplot as plt
import numpy as np


def analyze_profit_sharing_spectrum(
    ticker: str = "NVDA",
    start_date: str = "2022-01-01",
    end_date: str = "2025-01-01",
    initial_value: float = 100000.0,
    rebalance_threshold: float = 0.10,
    profit_sharing_min: float = -0.25,
    profit_sharing_max: float = 1.25,
    profit_sharing_step: float = 0.05,
) -> Dict:
    """
    Run backtests across a spectrum of profit-sharing ratios.
    
    Args:
        ticker: Stock symbol
        start_date: Start date for backtest
        end_date: End date for backtest
        initial_value: Starting capital
        rebalance_threshold: Rebalancing percentage (10% standard)
        profit_sharing_min: Minimum profit sharing ratio (-0.25 = accumulate)
        profit_sharing_max: Maximum profit sharing ratio (1.25 = deplete)
        profit_sharing_step: Increment step (0.05 = 5%)
    
    Returns:
        Dictionary with results for each profit sharing ratio
    """
    print(f"\n{'='*70}")
    print(f"Profit Sharing Composition Analysis")
    print(f"{'='*70}")
    print(f"Ticker: {ticker}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial Value: ${initial_value:,.0f}")
    print(f"Rebalance Threshold: {rebalance_threshold:.0%}")
    print(f"Profit Sharing Range: {profit_sharing_min:.0%} to {profit_sharing_max:.0%} (step {profit_sharing_step:.0%})")
    print(f"{'='*70}\n")
    
    # Fetch data once
    print(f"Fetching {ticker} data...")
    fetcher = HistoryFetcher()
    start_dt = datetime.strptime(start_date, "%Y-%m-%d").date()
    end_dt = datetime.strptime(end_date, "%Y-%m-%d").date()
    
    df = fetcher.get_history(ticker, start_dt, end_dt)
    
    if df is None or df.empty:
        print(f"ERROR: No data for {ticker}")
        return {}
    
    print(f"  Downloaded {len(df)} days of data")
    
    # Calculate initial quantity from initial value and first price
    first_price = float(df.iloc[0]['Close'].iloc[0]) if hasattr(df.iloc[0]['Close'], 'iloc') else float(df.iloc[0]['Close'])
    initial_qty = int(initial_value / first_price)
    print(f"  Initial: {initial_qty} shares @ ${first_price:.2f} = ${initial_qty * first_price:,.2f}\n")
    
    # Generate profit sharing ratios
    ratios = np.arange(profit_sharing_min, profit_sharing_max + profit_sharing_step/2, profit_sharing_step)
    
    results = {}
    
    for ps_ratio in ratios:
        print(f"Running: {ps_ratio:+4.0%}...", end=" ", flush=True)
        
        # Build Enhanced algorithm (with buybacks)
        algo = build_algo_from_name("sd1")  # Enhanced strategy
        algo.rebalance_threshold_pct = rebalance_threshold
        algo.profit_taking_pct = ps_ratio
        algo.verbose = False  # Quiet mode
        
        # Run backtest
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=ticker,
            initial_qty=initial_qty,
            start_date=start_dt,
            end_date=end_dt,
            algo=algo,
        )
        
        results[ps_ratio] = summary
        
        # Quick summary
        final_value = summary['end_value']
        total_return = summary['total_return']
        final_holdings = summary['holdings']
        final_bank = summary['bank']
        utilization = summary.get('capital_utilization', 0.0)
        
        print(f"Return: {total_return:+.1%}, Holdings: {final_holdings:.0f}, Cash: ${final_bank:,.0f}")
    
    return results


def plot_composition_over_time(results: Dict, ticker: str):
    """
    Create visualizations showing how holdings composition changes over time.
    
    Plots:
    1. Holdings (shares) over time for each profit sharing ratio
    2. Cash balance over time
    3. Total portfolio value over time
    4. Capital utilization over time
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle(f'{ticker} Holdings Composition: Profit Sharing Spectrum', fontsize=16, fontweight='bold')
    
    # Color map: negative=blue, standard=green, aggressive=orange, extreme=red
    def get_color(ps_ratio):
        if ps_ratio < 0:
            return plt.cm.Blues(0.7)  # Accumulation (blue)
        elif ps_ratio <= 0.50:
            return plt.cm.Greens(0.5 + ps_ratio)  # Standard (green)
        elif ps_ratio <= 1.00:
            return plt.cm.Oranges(ps_ratio)  # Aggressive (orange)
        else:
            return plt.cm.Reds(ps_ratio - 0.5)  # Extreme (red)
    
    # Get representative ratios to plot (not all, too crowded)
    all_ratios = sorted(results.keys())
    
    # Select subset: every other ratio for cleaner visualization
    plot_ratios = all_ratios[::2]  # Every 10%
    
    for ps_ratio in plot_ratios:
        summary = results[ps_ratio]
        history = summary.get('holdings_history', [])
        
        if not history:
            continue
        
        dates = [h[0] for h in history]
        holdings = [h[1] for h in history]
        banks = [h[2] for h in history]
        prices = [h[3] for h in history]
        
        # Calculate portfolio values
        portfolio_values = [h * p + b for h, p, b in zip(holdings, prices, banks)]
        stock_values = [h * p for h, p in zip(holdings, prices)]
        
        color = get_color(ps_ratio)
        label = f"{ps_ratio:+.0%}"
        
        # Plot 1: Holdings (shares) over time
        axes[0, 0].plot(dates, holdings, color=color, label=label, alpha=0.7, linewidth=1.5)
        
        # Plot 2: Cash balance over time
        axes[0, 1].plot(dates, banks, color=color, label=label, alpha=0.7, linewidth=1.5)
        
        # Plot 3: Total portfolio value over time
        axes[1, 0].plot(dates, portfolio_values, color=color, label=label, alpha=0.7, linewidth=1.5)
        
        # Plot 4: Capital utilization (stock value / portfolio value)
        utilization = [sv / pv if pv > 0 else 0 for sv, pv in zip(stock_values, portfolio_values)]
        axes[1, 1].plot(dates, utilization, color=color, label=label, alpha=0.7, linewidth=1.5)
    
    # Configure Plot 1: Holdings
    axes[0, 0].set_title('Share Holdings Over Time', fontweight='bold')
    axes[0, 0].set_xlabel('Date')
    axes[0, 0].set_ylabel('Shares Owned')
    axes[0, 0].legend(title='Profit\nSharing', loc='best', fontsize=8, ncol=2)
    axes[0, 0].grid(True, alpha=0.3)
    
    # Configure Plot 2: Cash
    axes[0, 1].set_title('Cash Balance Over Time', fontweight='bold')
    axes[0, 1].set_xlabel('Date')
    axes[0, 1].set_ylabel('Cash ($)')
    axes[0, 1].legend(title='Profit\nSharing', loc='best', fontsize=8, ncol=2)
    axes[0, 1].grid(True, alpha=0.3)
    axes[0, 1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    # Configure Plot 3: Portfolio Value
    axes[1, 0].set_title('Total Portfolio Value Over Time', fontweight='bold')
    axes[1, 0].set_xlabel('Date')
    axes[1, 0].set_ylabel('Portfolio Value ($)')
    axes[1, 0].legend(title='Profit\nSharing', loc='best', fontsize=8, ncol=2)
    axes[1, 0].grid(True, alpha=0.3)
    axes[1, 0].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
    
    # Configure Plot 4: Utilization
    axes[1, 1].set_title('Capital Utilization Over Time', fontweight='bold')
    axes[1, 1].set_xlabel('Date')
    axes[1, 1].set_ylabel('Utilization (Stock Value / Total Value)')
    axes[1, 1].legend(title='Profit\nSharing', loc='best', fontsize=8, ncol=2)
    axes[1, 1].grid(True, alpha=0.3)
    axes[1, 1].yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{x:.0%}'))
    axes[1, 1].set_ylim(0, 1.1)
    
    plt.tight_layout()
    
    # Save figure
    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    filename = output_dir / f"profit_sharing_composition_{ticker}.png"
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    print(f"\n📊 Saved composition chart: {filename}")
    
    plt.show()


def create_summary_table(results: Dict, ticker: str):
    """
    Create a summary table showing key metrics for each profit sharing ratio.
    """
    print(f"\n{'='*100}")
    print(f"Summary Table: {ticker} Profit Sharing Analysis")
    print(f"{'='*100}")
    print(f"{'PS%':>6} | {'Final Value':>12} | {'Return':>8} | {'Shares':>8} | {'Cash':>12} | {'Util%':>6} | {'ROD%':>7}")
    print(f"{'-'*100}")
    
    for ps_ratio in sorted(results.keys()):
        summary = results[ps_ratio]
        
        final_value = summary['end_value']
        total_return = summary['total_return']
        final_holdings = summary['holdings']
        final_bank = summary['bank']
        utilization = summary.get('capital_utilization', 0.0)
        return_on_deployed = summary.get('return_on_deployed_capital', 0.0)
        
        print(f"{ps_ratio:+5.0%} | ${final_value:11,.0f} | {total_return:+7.1%} | "
              f"{final_holdings:8.0f} | ${final_bank:11,.0f} | {utilization:5.1%} | {return_on_deployed:+6.1%}")
    
    print(f"{'='*100}\n")
    
    # Identify interesting patterns
    print("🔍 Analysis Insights:")
    
    # Find the best return
    best_ps = max(results.keys(), key=lambda ps: results[ps]['total_return'])
    print(f"  • Highest Return: {best_ps:+.0%} profit sharing → {results[best_ps]['total_return']:+.1%}")
    
    # Find the highest final value
    best_value_ps = max(results.keys(), key=lambda ps: results[ps]['end_value'])
    print(f"  • Highest Final Value: {best_value_ps:+.0%} profit sharing → ${results[best_value_ps]['end_value']:,.0f}")
    
    # Find most shares accumulated
    most_shares_ps = max(results.keys(), key=lambda ps: results[ps]['holdings'])
    print(f"  • Most Shares: {most_shares_ps:+.0%} profit sharing → {results[most_shares_ps]['holdings']:.0f} shares")
    
    # Find most cash accumulated
    most_cash_ps = max(results.keys(), key=lambda ps: results[ps]['bank'])
    print(f"  • Most Cash: {most_cash_ps:+.0%} profit sharing → ${results[most_cash_ps]['bank']:,.0f}")
    
    # Find highest capital efficiency
    best_efficiency_ps = max(results.keys(), key=lambda ps: results[ps].get('return_on_deployed_capital', 0))
    print(f"  • Best Capital Efficiency: {best_efficiency_ps:+.0%} profit sharing → "
          f"{results[best_efficiency_ps].get('return_on_deployed_capital', 0):+.1%} return on deployed")
    
    print()


def main():
    """
    Main analysis: Run profit sharing composition study.
    """
    # Run analysis
    results = analyze_profit_sharing_spectrum(
        ticker="NVDA",
        start_date="2022-01-01",
        end_date="2024-12-31",  # ~3 years
        initial_value=100000.0,
        rebalance_threshold=0.10,
        profit_sharing_min=-0.25,
        profit_sharing_max=1.25,
        profit_sharing_step=0.05,
    )
    
    # Create visualizations
    plot_composition_over_time(results, "NVDA")
    
    # Create summary table
    create_summary_table(results, "NVDA")
    
    print("\n✅ Profit sharing composition analysis complete!\n")


if __name__ == "__main__":
    main()
