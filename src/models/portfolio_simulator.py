"""Portfolio simulator for multi-asset buy-and-hold backtesting.

This module implements simple buy-and-hold portfolio strategies across multiple assets.
It's designed for baseline comparisons against algorithmic strategies.

Key features:
- Multi-asset allocation (e.g., 20% NVDA, 20% BTC, 60% VOO)
- Rebalancing strategies (none, periodic, threshold-based)
- Daily portfolio value tracking
- Asset composition history for visualization

Example:
    >>> allocations = {
    ...     'NVDA': 0.20,
    ...     'GOOG': 0.20,
    ...     'BTC-USD': 0.20,
    ...     'ETH-USD': 0.20,
    ...     'PLTR': 0.20
    ... }
    >>> result = simulate_portfolio(
    ...     allocations=allocations,
    ...     start_date=date(2023, 1, 1),
    ...     end_date=date(2024, 12, 31),
    ...     initial_value=1_000_000
    ... )
    >>> print(f"Final value: ${result['final_value']:,.0f}")
    >>> print(f"Total return: {result['total_return']:.2f}%")
"""

from datetime import date
from typing import Dict, List, Tuple

import pandas as pd


def simulate_portfolio(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    initial_value: float = 1_000_000.0,
    rebalance: str = "none",
) -> Dict:
    """Simulate buy-and-hold portfolio across multiple assets.

    DEPRECATED: This function now uses the unified run_portfolio_backtest infrastructure.
    For algorithmic strategies, use run_portfolio_backtest directly.

    Args:
        allocations: Dict mapping ticker → target allocation (must sum to 1.0)
        start_date: Portfolio start date
        end_date: Portfolio end date
        initial_value: Initial investment in dollars
        rebalance: Rebalancing strategy ('none', 'monthly', 'quarterly', 'annual')
                  NOTE: Rebalancing not yet implemented in unified backtest

    Returns:
        Dict with keys:
            - 'final_value': Ending portfolio value
            - 'total_return': Total return as percentage
            - 'annualized_return': Annualized return as percentage
            - 'daily_values': DataFrame with date index and columns:
                * 'total': Total portfolio value
                * '{ticker}_value': Market value of each holding
                * '{ticker}_shares': Shares held of each asset
                * '{ticker}_price': Price per share
            - 'allocations': Original allocation targets
            - 'summary': Performance summary string

    Raises:
        ValueError: If allocations don't sum to ~1.0 or dates are invalid
    """
    if rebalance != "none":
        raise NotImplementedError(
            "Rebalancing not yet implemented in unified backtest. Use rebalance='none' for now."
        )

    # Use the unified portfolio backtest infrastructure
    from src.models.backtest import run_portfolio_backtest

    transactions, portfolio_summary = run_portfolio_backtest(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo="per-asset:buy-and-hold",  # Updated to new API
        initial_investment=initial_value,
    )

    # Convert to the expected format for backward compatibility
    # Reconstruct daily_values DataFrame in the original format
    daily_values_df = pd.DataFrame(
        {
            "date": list(portfolio_summary["daily_values"].keys()),
            "total": list(portfolio_summary["daily_values"].values()),
        }
    ).set_index("date")

    result = {
        "final_value": portfolio_summary["total_final_value"],
        "total_return": portfolio_summary["total_return"],
        "annualized_return": portfolio_summary["annualized_return"],
        "daily_values": daily_values_df,
        "allocations": portfolio_summary["allocations"],
        "initial_value": portfolio_summary["initial_investment"],
        "start_date": portfolio_summary["start_date"],
        "end_date": portfolio_summary["end_date"],
    }

    # Build summary string
    summary_lines = [
        "Portfolio Performance Summary",
        "=" * 60,
        f"Period: {result['start_date']} to {result['end_date']} ({portfolio_summary['trading_days']} days)",
        f"Initial Investment: ${result['initial_value']:,.0f}",
        f"Final Value: ${result['final_value']:,.0f}",
        f"Total Return: {result['total_return']:+.2f}%",
        f"Annualized Return: {result['annualized_return']:+.2f}%",
        "",
        "Asset Allocation:",
    ]

    for ticker, data in portfolio_summary["assets"].items():
        allocation = data["allocation"]
        final_value = data["final_value"]
        total_return = data["total_return"]

        summary_lines.append(
            f"  {ticker:10s}: {allocation*100:5.1f}% → "
            f"${final_value:12,.0f} ({total_return:+7.2f}%)"
        )

    result["summary"] = "\n".join(summary_lines)

    return result


def compare_portfolios(
    portfolio_configs: List[Tuple[str, Dict[str, float]]],
    start_date: date,
    end_date: date,
    initial_value: float = 1_000_000.0,
) -> Dict:
    """Compare multiple portfolio allocations over the same period.

    Args:
        portfolio_configs: List of (name, allocations) tuples
        start_date: Comparison start date
        end_date: Comparison end date
        initial_value: Initial investment for each portfolio

    Returns:
        Dict with keys:
            - 'results': Dict mapping portfolio name → simulation result
            - 'comparison_table': DataFrame comparing all portfolios
            - 'summary': Comparison summary string
    """
    results = {}

    print(f"\n{'='*70}")
    print(f"Comparing {len(portfolio_configs)} portfolios")
    print(f"{'='*70}")

    for name, allocations in portfolio_configs:
        print(f"\n--- {name} ---")
        result = simulate_portfolio(allocations, start_date, end_date, initial_value)
        results[name] = result
        print(f"\nFinal Value: ${result['final_value']:,.0f}")
        print(f"Total Return: {result['total_return']:+.2f}%")
        print(f"Annualized: {result['annualized_return']:+.2f}%")

    # Build comparison table
    comparison_data = []
    for name, result in results.items():
        comparison_data.append(
            {
                "Portfolio": name,
                "Final Value": result["final_value"],
                "Total Return (%)": result["total_return"],
                "Annualized (%)": result["annualized_return"],
            }
        )

    df_comparison = pd.DataFrame(comparison_data)
    df_comparison = df_comparison.sort_values("Total Return (%)", ascending=False)

    # Build summary
    summary_lines = [
        f"\n{'='*70}",
        "Portfolio Comparison Summary",
        f"{'='*70}",
        f"Period: {start_date} to {end_date}",
        f"Initial Investment: ${initial_value:,.0f}",
        "",
        df_comparison.to_string(index=False),
        "",
    ]

    # Calculate best vs worst
    best = df_comparison.iloc[0]
    worst = df_comparison.iloc[-1]
    alpha = best["Total Return (%)"] - worst["Total Return (%)"]

    summary_lines.append(f"Best: {best['Portfolio']} ({best['Total Return (%)']:+.2f}%)")
    summary_lines.append(f"Worst: {worst['Portfolio']} ({worst['Total Return (%)']:+.2f}%)")
    summary_lines.append(f"Alpha: {alpha:+.2f}%")
    summary_lines.append(f"{'='*70}")

    summary = "\n".join(summary_lines)

    return {
        "results": results,
        "comparison_table": df_comparison,
        "summary": summary,
    }
