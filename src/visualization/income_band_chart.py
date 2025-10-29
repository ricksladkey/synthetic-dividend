"""
Income Band Chart: Multi-asset income streams visualization.

Creates publication-quality band charts showing income flows from multiple assets,
expenses, and cash reserves over time. Perfect for visualizing retirement portfolio
income sustainability.

Key features:
- Stacked bands showing income from each asset (different colors)
- Red band for expenses/withdrawals
- Green band for USD cash reserves
- Clear visualization of income sustainability
- Export to PNG/PDF

Example:
    >>> from src.visualization.income_band_chart import plot_income_bands
    >>>
    >>> # Income data: date -> {'NVDA': 500, 'SPY': 300, 'BTC': 800, 'expenses': 1200, 'cash': 50000}
    >>> plot_income_bands(
    ...     income_data=income_series,
    ...     title="Retirement Portfolio Income Streams",
    ...     output_file="income_bands.png"
    ... )
"""

from typing import Optional

import matplotlib.dates as mdates
import numpy as np
import pandas as pd

# Asset color scheme - distinct colors for different asset types
ASSET_COLORS = {
    # Tech stocks (blues)
    "NVDA": "#1f77b4",
    "GOOG": "#aec7e8",
    "GOOGL": "#aec7e8",
    "AAPL": "#6baed6",
    "MSFT": "#3182bd",
    "PLTR": "#08519c",
    # Indexes/ETFs (greens)
    "VOO": "#2ca02c",
    "SPY": "#74c476",
    "QQQ": "#a1d99b",
    "VTI": "#41ab5d",
    # Crypto (purples)
    "BTC-USD": "#756bb1",
    "ETH-USD": "#9e9ac8",
    "BTC": "#756bb1",
    "ETH": "#9e9ac8",
    # Commodities (oranges)
    "GLD": "#ff7f0e",
    "SLV": "#fd8d3c",
    "USO": "#fdae6b",
    # Bonds (reds)
    "TLT": "#d62728",
    "BND": "#e6550d",
    "AGG": "#fd8d3c",
    # Special bands
    "expenses": "#d62728",  # Red for expenses
    "cash": "#2ca02c",  # Green for cash
    "withdrawals": "#d62728",  # Red for withdrawals
    # Default
    "default": "#7f7f7f",
}


def get_asset_color(asset_name: str) -> str:
    """Get color for asset/income stream."""
    return ASSET_COLORS.get(asset_name, ASSET_COLORS["default"])


def plot_income_bands(
    income_data: pd.DataFrame,
    title: str = "Portfolio Income Streams Over Time",
    output_file: Optional[str] = None,
    figsize: tuple = (16, 10),
    show_legend: bool = True,
    alpha: float = 0.8,
) -> str:
    """
    Plot income band chart showing portfolio value as stacked bands.

    This shows the TOTAL portfolio value including all withdrawals as stacked bands:
    - Expenses/withdrawals (red band at bottom showing cumulative withdrawals)
    - Cash reserves (green band for USD cash)
    - Asset values (colored bands for each asset)

    The total height = portfolio value + all historical withdrawals

    Args:
        income_data: DataFrame with date index and columns for each component:
            - Asset tickers (e.g., 'NVDA', 'SPY'): Current market value of each holding
            - 'expenses' or 'cumulative_withdrawals': Total withdrawn to date
            - 'cash': Cash reserve levels (green band)
        title: Chart title
        output_file: Optional output filename (PNG/PDF)
        figsize: Figure size as (width, height)
        show_legend: Whether to show the legend
        alpha: Transparency level for bands (0-1)

    Returns:
        Output filename (or "displayed" if shown interactively)

    Example DataFrame:
        date        NVDA    SPY     BTC     cash    expenses
        2024-01-01  45000   40000   87500   50000   3333
        2024-02-01  46000   41000   85000   48000   6666
        ...
    """
    # Set non-interactive backend if saving to file
    if output_file:
        import matplotlib

        matplotlib.use("Agg")

    import matplotlib.pyplot as plt

    if income_data.empty:
        raise ValueError("income_data DataFrame is empty")

    # Ensure we have a date index
    if not isinstance(income_data.index, pd.DatetimeIndex):
        try:
            income_data.index = pd.to_datetime(income_data.index)
        except Exception as e:
            raise ValueError(f"Could not convert index to datetime: {e}")

    dates = income_data.index

    # Identify different types of columns
    asset_columns = []
    expense_columns = []
    cash_columns = []

    for col in income_data.columns:
        col_lower = col.lower()
        if col_lower in ["expenses", "withdrawals", "withdrawal", "cumulative_withdrawals"]:
            expense_columns.append(col)
        elif col_lower in ["cash", "usd", "bank"]:
            cash_columns.append(col)
        else:
            asset_columns.append(col)

    # Prepare data for stacking
    # Stack order (bottom to top): expenses, cash, assets
    stack_data = []
    stack_labels = []
    stack_colors = []

    # 1. Expenses layer (bottom, red wedge above zero line)
    if expense_columns:
        for expense_col in expense_columns:
            stack_data.append(income_data[expense_col].values)
            stack_labels.append(expense_col.title())
            stack_colors.append(ASSET_COLORS["expenses"])

    # 2. Cash layer (middle, green)
    if cash_columns:
        for cash_col in cash_columns:
            stack_data.append(income_data[cash_col].values)
            stack_labels.append(f"{cash_col.title()} Reserves")
            stack_colors.append(ASSET_COLORS["cash"])

    # 3. Asset layers (top, various colors)
    if asset_columns:
        for asset_col in asset_columns:
            stack_data.append(income_data[asset_col].values)
            stack_labels.append(asset_col)
            stack_colors.append(get_asset_color(asset_col))

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot stacked area chart
    if stack_data:
        ax.stackplot(
            dates,
            *stack_data,
            labels=stack_labels,
            colors=stack_colors,
            alpha=alpha,
        )

    # Formatting
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Total Portfolio Value (including withdrawals) ($)", fontsize=12)

    # Y-axis formatting
    ax.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda y, _: f"${y/1e3:.0f}K" if y >= 1000 else f"${y:.0f}")
    )

    # Legend
    if show_legend:
        ax.legend(
            loc="upper left",
            framealpha=0.9,
            fontsize=10,
            title="Portfolio Components",
            title_fontsize=11,
            bbox_to_anchor=(1.02, 1),
            borderaxespad=0,
        )

    # Grid
    ax.grid(True, alpha=0.3, linestyle="--")

    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)

    # Tight layout
    plt.tight_layout()

    # Save or show
    if output_file:
        plt.savefig(output_file, dpi=150, bbox_inches="tight")
        print(f"\n✓ Income band chart saved to: {output_file}")
        plt.close(fig)
        return output_file
    else:
        plt.show()
        return "displayed"


def create_sample_income_data() -> pd.DataFrame:
    """
    Create sample income data for demonstration.

    Returns:
        DataFrame with sample income streams, expenses, and cash reserves
    """
    # Create date range
    dates = pd.date_range("2024-01-01", "2025-01-01", freq="ME")

    # Sample income streams (monthly)
    np.random.seed(42)  # For reproducible results

    n_periods = len(dates)
    data = {
        "NVDA": np.random.normal(500, 50, n_periods) + np.sin(np.arange(n_periods) * 0.5) * 100,
        "SPY": np.random.normal(300, 30, n_periods) + np.cos(np.arange(n_periods) * 0.3) * 50,
        "BTC": np.random.normal(800, 200, n_periods) + np.sin(np.arange(n_periods) * 0.8) * 300,
        "GLD": np.random.normal(150, 20, n_periods),
        "expenses": np.full(n_periods, 1200),  # Constant expenses
        "cash": np.linspace(50000, 45000, n_periods) + np.random.normal(0, 2000, n_periods),
    }

    df = pd.DataFrame(data, index=dates)

    # Ensure non-negative values
    df = df.clip(lower=0)

    return df


def demo_income_bands():
    """Create a demo income band chart."""
    print("Creating sample income band chart...")

    # Create sample data
    income_data = create_sample_income_data()

    # Plot the chart
    output_file = "demo_income_bands.png"
    result = plot_income_bands(
        income_data=income_data,
        title="Sample Retirement Portfolio Income Streams",
        output_file=output_file,
    )

    print(f"Demo chart created: {result}")
    print("\nSample data includes:")
    print("- NVDA, SPY, BTC, GLD: Asset income streams")
    print("- expenses: Monthly withdrawal amount (red band)")
    print("- cash: USD cash reserves (green band)")


if __name__ == "__main__":
    demo_income_bands()
