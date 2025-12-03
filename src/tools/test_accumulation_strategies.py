#!/usr/bin/env python3
"""Test different position accumulation strategies (bulk vs DCA variants).

Compares lump sum vs dollar-cost averaging approaches by running rolling
window backtests across historical data and reporting average CAGR.
"""

import argparse
from datetime import date, timedelta
from typing import Dict, List, Tuple

import pandas as pd

from src.data.asset import Asset


def calculate_cagr(initial_value: float, final_value: float, years: float) -> float:
    """Calculate compound annual growth rate."""
    if initial_value <= 0 or years <= 0:
        return 0.0
    return ((final_value / initial_value) ** (1.0 / years)) - 1.0


def simulate_accumulation(
    df: pd.DataFrame,
    start_date: date,
    end_date: date,
    capital: float,
    strategy: str,
) -> Tuple[float, float]:
    """Simulate an accumulation strategy over a date range.

    Args:
        df: Price DataFrame with 'Close' column
        start_date: Start of accumulation period
        end_date: End of holding period (12 months from start)
        capital: Total capital to deploy
        strategy: Strategy name (e.g., 'bulk', 'dca-weekly-4', 'dca-monthly-10')

    Returns:
        Tuple of (shares_acquired, final_value)
    """
    # Parse strategy
    parts = strategy.split("-")
    if parts[0] == "bulk":
        # Deploy 100% on day 1
        purchases = [(start_date, 1.0)]
    else:
        # DCA strategy: dca-{frequency}-{periods}
        frequency = parts[1]  # 'weekly' or 'monthly'
        num_periods = int(parts[2])
        pct_per_period = 1.0 / num_periods

        # Generate purchase dates
        purchases = []
        for i in range(num_periods):
            if frequency == "weekly":
                purchase_date = start_date + timedelta(weeks=i)
            elif frequency == "monthly":
                purchase_date = start_date + timedelta(days=30 * i)
            else:
                raise ValueError(f"Unknown frequency: {frequency}")
            purchases.append((purchase_date, pct_per_period))

    # Filter df to date range (convert dates to Timestamps for pandas compatibility)
    start_ts = pd.Timestamp(start_date)
    end_ts = pd.Timestamp(end_date)
    df_range = df.loc[start_ts:end_ts]
    if df_range.empty:
        return 0.0, 0.0

    # Execute purchases
    total_shares = 0.0
    for purchase_date, pct in purchases:
        # Convert to Timestamp for pandas index comparison
        purchase_ts = pd.Timestamp(purchase_date)

        # Find nearest trading day
        if purchase_ts in df_range.index:
            price = df_range.loc[purchase_ts, "Close"]
        else:
            # Use next available date
            future_dates = df_range.index[df_range.index >= purchase_ts]
            if len(future_dates) == 0:
                continue
            price = df_range.loc[future_dates[0], "Close"]

        # Buy shares
        amount = capital * pct
        shares = amount / price
        total_shares += shares

    # Calculate final value at end_date
    if end_ts in df_range.index:
        final_price = df_range.loc[end_ts, "Close"]
    else:
        # Use last available price
        final_price = df_range.iloc[-1]["Close"]

    final_value = total_shares * final_price
    return total_shares, final_value


def run_experiment(
    ticker: str,
    capital: float,
    strategies: List[str],
    lookback_years: int = 2,
) -> Dict[str, Dict[str, float]]:
    """Run accumulation strategy experiment across rolling windows.

    Args:
        ticker: Asset ticker symbol
        capital: Total capital to deploy
        strategies: List of strategy names
        lookback_years: How many years back to start testing

    Returns:
        Dict mapping strategy name to statistics dict
    """
    # Load asset data
    asset = Asset(ticker)
    end_date = date.today()
    start_date = end_date - timedelta(days=365 * lookback_years)
    df = asset.get_prices(start_date, end_date)

    if df is None or df.empty:
        raise ValueError(f"No price data available for {ticker}")

    # Generate rolling windows (12-month holding period, start every month)
    windows = []
    current_start = start_date
    while current_start + timedelta(days=365) <= end_date:
        window_end = current_start + timedelta(days=365)
        windows.append((current_start, window_end))
        current_start += timedelta(days=30)  # Start next window 1 month later

    print(f"Testing {len(windows)} rolling 12-month windows from {start_date} to {end_date}")
    print(f"Strategies: {', '.join(strategies)}")
    print()

    # Run each strategy on each window
    results: Dict[str, List[float]] = {strategy: [] for strategy in strategies}

    for window_start, window_end in windows:
        for strategy in strategies:
            shares, final_value = simulate_accumulation(
                df, window_start, window_end, capital, strategy
            )
            cagr = calculate_cagr(capital, final_value, 1.0)  # 1 year holding period
            results[strategy].append(cagr)

    # Calculate statistics
    stats = {}
    for strategy in strategies:
        cagrs = results[strategy]
        stats[strategy] = {
            "avg_cagr": sum(cagrs) / len(cagrs) if cagrs else 0.0,
            "min_cagr": min(cagrs) if cagrs else 0.0,
            "max_cagr": max(cagrs) if cagrs else 0.0,
            "std_dev": pd.Series(cagrs).std() if cagrs else 0.0,
            "num_windows": len(cagrs),
        }

    return stats


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Test accumulation strategies (bulk vs DCA)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test NVDA with default strategies
  python -m src.tools.test_accumulation_strategies --ticker NVDA

  # Test VOO with custom capital
  python -m src.tools.test_accumulation_strategies --ticker VOO --capital 100000

  # Test specific strategies
  python -m src.tools.test_accumulation_strategies --ticker BTC-USD \\
      --strategies bulk dca-weekly-4 dca-monthly-12
""",
    )
    parser.add_argument("--ticker", type=str, required=True, help="Ticker symbol")
    parser.add_argument(
        "--capital",
        type=float,
        default=10000.0,
        help="Total capital to deploy (default: $10,000)",
    )
    parser.add_argument(
        "--strategies",
        type=str,
        nargs="+",
        default=["bulk", "dca-weekly-4", "dca-monthly-4", "dca-weekly-10", "dca-monthly-10"],
        help="Strategies to test (default: bulk dca-weekly-4 dca-monthly-4 dca-weekly-10 dca-monthly-10)",
    )
    parser.add_argument(
        "--lookback",
        type=int,
        default=2,
        help="Years of historical data to test (default: 2)",
    )

    args = parser.parse_args()

    # Run experiment
    print(f"Accumulation Strategy Test")
    print(f"=" * 60)
    print(f"Ticker: {args.ticker}")
    print(f"Capital: ${args.capital:,.2f}")
    print()

    stats = run_experiment(args.ticker, args.capital, args.strategies, args.lookback)

    # Print results table
    print()
    print("Results (Average across all windows):")
    print("-" * 80)
    print(f"{'Strategy':<20} {'Avg CAGR':>12} {'Std Dev':>12} {'Min CAGR':>12} {'Max CAGR':>12}")
    print("-" * 80)

    # Sort by avg CAGR descending
    sorted_strategies = sorted(stats.keys(), key=lambda s: stats[s]["avg_cagr"], reverse=True)

    for strategy in sorted_strategies:
        s = stats[strategy]
        print(
            f"{strategy:<20} "
            f"{s['avg_cagr']:>11.2%} "
            f"{s['std_dev']:>11.2%} "
            f"{s['min_cagr']:>11.2%} "
            f"{s['max_cagr']:>11.2%}"
        )

    print("-" * 80)
    print(f"Tested across {stats[sorted_strategies[0]]['num_windows']} rolling 12-month windows")
    print()

    # Print winner
    winner = sorted_strategies[0]
    winner_cagr = stats[winner]["avg_cagr"]
    print(f"Winner: {winner} with {winner_cagr:.2%} average CAGR")


if __name__ == "__main__":
    main()
