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
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np

from src.data.fetcher import HistoryFetcher


def simulate_portfolio(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    initial_value: float = 1_000_000.0,
    rebalance: str = 'none'
) -> Dict:
    """Simulate buy-and-hold portfolio across multiple assets.
    
    Args:
        allocations: Dict mapping ticker → target allocation (must sum to 1.0)
        start_date: Portfolio start date
        end_date: Portfolio end date
        initial_value: Initial investment in dollars
        rebalance: Rebalancing strategy ('none', 'monthly', 'quarterly', 'annual')
        
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
    # Validate allocations
    total_allocation = sum(allocations.values())
    if abs(total_allocation - 1.0) > 0.01:
        raise ValueError(f"Allocations must sum to 1.0, got {total_allocation:.3f}")
    
    if start_date >= end_date:
        raise ValueError(f"start_date must be before end_date: {start_date} >= {end_date}")
    
    # Fetch price data for all assets
    fetcher = HistoryFetcher()
    price_data: Dict[str, pd.DataFrame] = {}
    
    print(f"\nFetching data for {len(allocations)} assets...")
    for ticker in allocations.keys():
        print(f"  - {ticker}...", end=' ')
        df = fetcher.get_history(ticker, start_date, end_date)
        if df is None or df.empty:
            raise ValueError(f"No data available for {ticker}")
        price_data[ticker] = df
        print(f"✓ ({len(df)} days)")
    
    # Find common date range (intersection of all available dates)
    all_dates = set(pd.to_datetime(price_data[list(allocations.keys())[0]].index).date)
    for df in price_data.values():
        all_dates = all_dates.intersection(set(pd.to_datetime(df.index).date))
    
    if not all_dates:
        raise ValueError("No common dates across all assets")
    
    dates = sorted(list(all_dates))
    print(f"\nCommon trading days: {len(dates)} (from {dates[0]} to {dates[-1]})")
    
    # Initialize holdings: buy shares on first day according to allocation
    first_date = dates[0]
    shares: Dict[str, float] = {}
    
    print(f"\nInitial purchase on {first_date}:")
    for ticker, allocation in allocations.items():
        # Find first_date in this ticker's data (convert back to datetime for lookup)
        df_dates = pd.to_datetime(price_data[ticker].index).date
        idx = list(df_dates).index(first_date)
        first_price = price_data[ticker].iloc[idx]['Close'].item()  # Use .item() to extract scalar
        investment = initial_value * allocation
        shares[ticker] = investment / first_price
        print(f"  {ticker}: {shares[ticker]:.4f} shares @ ${first_price:.2f} = ${investment:,.0f}")
    
    # Build daily value history
    daily_values = []
    
    for d in dates:
        row = {'date': d, 'total': 0.0}
        
        for ticker in allocations.keys():
            # Find this date in ticker's data
            df_dates = pd.to_datetime(price_data[ticker].index).date
            idx = list(df_dates).index(d)
            price = price_data[ticker].iloc[idx]['Close'].item()  # Use .item() to extract scalar
            value = shares[ticker] * price
            
            row[f'{ticker}_price'] = price
            row[f'{ticker}_shares'] = shares[ticker]
            row[f'{ticker}_value'] = value
            row['total'] += value
        
        daily_values.append(row)
    
    # Convert to DataFrame
    df_values = pd.DataFrame(daily_values)
    df_values.set_index('date', inplace=True)
    
    # Calculate returns
    final_value = df_values['total'].iloc[-1]
    total_return = ((final_value - initial_value) / initial_value) * 100
    
    # Annualized return
    days = (dates[-1] - dates[0]).days
    years = days / 365.25
    annualized_return = (((final_value / initial_value) ** (1 / years)) - 1) * 100 if years > 0 else 0
    
    # Build summary
    summary_lines = [
        f"Portfolio Performance Summary",
        f"=" * 60,
        f"Period: {dates[0]} to {dates[-1]} ({days} days, {years:.2f} years)",
        f"Initial Investment: ${initial_value:,.0f}",
        f"Final Value: ${final_value:,.0f}",
        f"Total Return: {total_return:+.2f}%",
        f"Annualized Return: {annualized_return:+.2f}%",
        f"",
        f"Asset Allocation:",
    ]
    
    for ticker, allocation in allocations.items():
        final_price = df_values[f'{ticker}_price'].iloc[-1]
        final_shares = shares[ticker]
        final_asset_value = df_values[f'{ticker}_value'].iloc[-1]
        
        # Calculate asset return
        df_dates = pd.to_datetime(price_data[ticker].index).date
        first_idx = list(df_dates).index(first_date)
        first_price_for_return = price_data[ticker].iloc[first_idx]['Close'].item()  # Use .item() to extract scalar
        asset_return = ((final_price / first_price_for_return) - 1) * 100
        
        summary_lines.append(
            f"  {ticker:10s}: {allocation*100:5.1f}% → "
            f"{final_shares:10.4f} shares @ ${final_price:8.2f} = "
            f"${final_asset_value:12,.0f} ({asset_return:+7.2f}%)"
        )
    
    summary = '\n'.join(summary_lines)
    
    return {
        'final_value': final_value,
        'total_return': total_return,
        'annualized_return': annualized_return,
        'daily_values': df_values,
        'allocations': allocations,
        'summary': summary,
        'initial_value': initial_value,
        'start_date': dates[0],
        'end_date': dates[-1],
    }


def compare_portfolios(
    portfolio_configs: List[Tuple[str, Dict[str, float]]],
    start_date: date,
    end_date: date,
    initial_value: float = 1_000_000.0
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
        comparison_data.append({
            'Portfolio': name,
            'Final Value': result['final_value'],
            'Total Return (%)': result['total_return'],
            'Annualized (%)': result['annualized_return'],
        })
    
    df_comparison = pd.DataFrame(comparison_data)
    df_comparison = df_comparison.sort_values('Total Return (%)', ascending=False)
    
    # Build summary
    summary_lines = [
        f"\n{'='*70}",
        f"Portfolio Comparison Summary",
        f"{'='*70}",
        f"Period: {start_date} to {end_date}",
        f"Initial Investment: ${initial_value:,.0f}",
        f"",
        df_comparison.to_string(index=False),
        f"",
    ]
    
    # Calculate best vs worst
    best = df_comparison.iloc[0]
    worst = df_comparison.iloc[-1]
    alpha = best['Total Return (%)'] - worst['Total Return (%)']
    
    summary_lines.append(f"Best: {best['Portfolio']} ({best['Total Return (%)']:+.2f}%)")
    summary_lines.append(f"Worst: {worst['Portfolio']} ({worst['Total Return (%)']:+.2f}%)")
    summary_lines.append(f"Alpha: {alpha:+.2f}%")
    summary_lines.append(f"{'='*70}")
    
    summary = '\n'.join(summary_lines)
    
    return {
        'results': results,
        'comparison_table': df_comparison,
        'summary': summary,
    }
