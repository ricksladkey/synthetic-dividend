"""Portfolio composition visualization using stacked area charts.

This module creates publication-quality charts showing how portfolio composition
changes over time. Perfect for visualizing multi-asset portfolios.

Key features:
- Stacked area charts showing asset values over time
- Percentage-based composition charts
- Color-coded by asset type (stocks, crypto, indexes)
- Automatic legend and labeling
- Export to PNG/PDF

Example:
    >>> from src.models.portfolio_simulator import simulate_portfolio
    >>> from src.visualization import plot_portfolio_composition
    >>> 
    >>> result = simulate_portfolio(allocations, start, end, 1_000_000)
    >>> plot_portfolio_composition(
    ...     result['daily_values'],
    ...     result['allocations'],
    ...     title="Crypto/Stocks Portfolio",
    ...     output_file="portfolio_composition.png"
    ... )
"""

from typing import Dict, Optional
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
import numpy as np


# Asset type color schemes
ASSET_COLORS = {
    # Crypto (blues)
    'BTC-USD': '#1f77b4',
    'ETH-USD': '#aec7e8',
    'BTC': '#1f77b4',
    'ETH': '#aec7e8',
    
    # Tech stocks (greens)
    'NVDA': '#2ca02c',
    'GOOG': '#98df8a',
    'GOOGL': '#98df8a',
    'PLTR': '#d5e8d4',
    'AAPL': '#7fb17f',
    'MSFT': '#5e9c5e',
    
    # Indexes/ETFs (oranges/grays)
    'VOO': '#ff7f0e',
    'SPY': '#ffbb78',
    'QQQ': '#ffd280',
    'VTI': '#e6a368',
    
    # Other
    'default': '#bcbd22',
}


def get_asset_color(ticker: str) -> str:
    """Get color for asset ticker."""
    return ASSET_COLORS.get(ticker, ASSET_COLORS['default'])


def plot_portfolio_composition(
    daily_values: pd.DataFrame,
    allocations: Dict[str, float],
    title: str = "Portfolio Composition Over Time",
    output_file: Optional[str] = None,
    show_percentage: bool = False,
    figsize: tuple = (14, 8)
) -> str:
    """Plot stacked area chart showing portfolio composition over time.
    
    Args:
        daily_values: DataFrame from simulate_portfolio with date index and:
            - 'total': Total portfolio value
            - '{ticker}_value': Market value of each asset
        allocations: Dict mapping ticker → target allocation
        title: Chart title
        output_file: Optional output filename (PNG/PDF)
        show_percentage: If True, show % composition instead of dollar values
        figsize: Figure size as (width, height)
        
    Returns:
        Output filename (or "displayed" if shown interactively)
    """
    # Extract asset values
    tickers = list(allocations.keys())
    dates = daily_values.index
    
    # Build value matrix: dates × assets
    values = np.zeros((len(dates), len(tickers)))
    for i, ticker in enumerate(tickers):
        values[:, i] = daily_values[f'{ticker}_value'].values
    
    if show_percentage:
        # Convert to percentages
        totals = values.sum(axis=1, keepdims=True)
        values = (values / totals) * 100
    
    # Create figure
    fig, ax = plt.subplots(figsize=figsize)
    
    # Plot stacked area
    colors = [get_asset_color(ticker) for ticker in tickers]
    ax.stackplot(
        dates,
        values.T,  # Transpose to get (assets, dates)
        labels=tickers,
        colors=colors,
        alpha=0.8
    )
    
    # Formatting
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.set_xlabel('Date', fontsize=12)
    
    if show_percentage:
        ax.set_ylabel('Portfolio Composition (%)', fontsize=12)
        ax.set_ylim(0, 100)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'{y:.0f}%'))
    else:
        ax.set_ylabel('Portfolio Value ($)', fontsize=12)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y/1e6:.2f}M' if y >= 1e6 else f'${y/1e3:.0f}K'))
    
    # Legend
    ax.legend(
        loc='upper left',
        framealpha=0.9,
        fontsize=10,
        title='Assets',
        title_fontsize=11
    )
    
    # Grid
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    
    # Tight layout
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n✓ Chart saved to: {output_file}")
        plt.close(fig)
        return output_file
    else:
        plt.show()
        return "displayed"


def plot_portfolio_comparison(
    results: Dict[str, Dict],
    title: str = "Portfolio Comparison",
    output_file: Optional[str] = None,
    figsize: tuple = (14, 10)
) -> str:
    """Plot multiple portfolios for side-by-side comparison.
    
    Creates a 2-panel chart:
    - Top: Total value over time for each portfolio
    - Bottom: Composition of best-performing portfolio
    
    Args:
        results: Dict mapping portfolio name → simulation result
        title: Chart title
        output_file: Optional output filename
        figsize: Figure size
        
    Returns:
        Output filename or "displayed"
    """
    fig, axes = plt.subplots(2, 1, figsize=figsize)
    
    # Panel 1: Total values comparison
    ax1 = axes[0]
    
    best_return = -float('inf')
    best_name = None
    
    for name, result in results.items():
        daily_values = result['daily_values']
        dates = daily_values.index
        total = daily_values['total'].values
        
        ax1.plot(dates, total, label=name, linewidth=2, alpha=0.8)
        
        if result['total_return'] > best_return:
            best_return = result['total_return']
            best_name = name
    
    ax1.set_title(f'{title} - Total Value', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=11)
    ax1.set_ylabel('Portfolio Value ($)', fontsize=11)
    ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y/1e6:.2f}M' if y >= 1e6 else f'${y/1e3:.0f}K'))
    ax1.legend(loc='upper left', framealpha=0.9, fontsize=10)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Panel 2: Best portfolio composition
    ax2 = axes[1]
    
    if best_name:
        best_result = results[best_name]
        daily_values = best_result['daily_values']
        allocations = best_result['allocations']
        tickers = list(allocations.keys())
        dates = daily_values.index
        
        # Build value matrix
        values = np.zeros((len(dates), len(tickers)))
        for i, ticker in enumerate(tickers):
            values[:, i] = daily_values[f'{ticker}_value'].values
        
        # Plot stacked area
        colors = [get_asset_color(ticker) for ticker in tickers]
        ax2.stackplot(
            dates,
            values.T,
            labels=tickers,
            colors=colors,
            alpha=0.8
        )
        
        ax2.set_title(f'{best_name} Composition (Best Performer: {best_return:+.2f}%)', 
                     fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=11)
        ax2.set_ylabel('Asset Value ($)', fontsize=11)
        ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f'${y/1e6:.2f}M' if y >= 1e6 else f'${y/1e3:.0f}K'))
        ax2.legend(loc='upper left', framealpha=0.9, fontsize=9)
        ax2.grid(True, alpha=0.3, linestyle='--')
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
    
    plt.tight_layout()
    
    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"\n✓ Comparison chart saved to: {output_file}")
        plt.close(fig)
        return output_file
    else:
        plt.show()
        return "displayed"
