"""Stacked area chart with support for positive/negative splits.

Creates publication-quality stacked area charts showing multi-component totals
over time, with optional negative bands below zero for representing withdrawals
or spending power.

Key features:
- Positive bands stack upward from zero (assets, reserves)
- Negative bands stack downward from zero (withdrawals, spending)
- Creates "horn shape" visualization showing total wealth generated
- Narrow neck visible where cash reserves approach zero
- Domain-neutral: works for any stacked time series data
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np


@dataclass
class SeriesData:
    """Single data series for stacking.

    Attributes:
        label: Series name for legend
        values: Y-axis values (must align with dates)
        color: Hex color code (auto-assigned if None)
    """

    label: str
    values: List[float]
    color: Optional[str] = None


@dataclass
class StackedAreaData:
    """Data contract for stacked area chart with optional positive/negative split.

    The chart creates a "horn shape" visualization:
    - Positive series stack upward from zero (assets, cash reserves)
    - Negative series stack downward from zero (withdrawals, spending power)
    - Zero line is just a visual separator - both sides represent positive wealth

    Total horn height = sum(positive_series) + abs(sum(negative_series))
    Narrow neck = point where positive_series[0] (typically cash) is smallest

    Attributes:
        dates: X-axis datetime values
        positive_series: Bands stacked above zero (bottom to top order)
        negative_series: Bands stacked below zero (top to bottom order)
    """

    dates: List[datetime]
    positive_series: List[SeriesData]
    negative_series: List[SeriesData] = field(default_factory=list)

    def __post_init__(self):
        """Validate data consistency."""
        n_dates = len(self.dates)

        # Validate positive series
        for series in self.positive_series:
            if len(series.values) != n_dates:
                raise ValueError(
                    f"Series '{series.label}' has {len(series.values)} values but {n_dates} dates"
                )

        # Validate negative series
        for series in self.negative_series:
            if len(series.values) != n_dates:
                raise ValueError(
                    f"Series '{series.label}' has {len(series.values)} values but {n_dates} dates"
                )

        if n_dates == 0:
            raise ValueError("Cannot create chart with zero data points")


def get_default_color(index: int) -> str:
    """Get color from default palette by index.

    Uses matplotlib's default color cycle for consistency.
    """
    palette = [
        "#1f77b4",  # Blue
        "#ff7f0e",  # Orange
        "#2ca02c",  # Green
        "#d62728",  # Red
        "#9467bd",  # Purple
        "#8c564b",  # Brown
        "#e377c2",  # Pink
        "#7f7f7f",  # Gray
        "#bcbd22",  # Olive
        "#17becf",  # Cyan
    ]
    return palette[index % len(palette)]


def create_stacked_area_chart(
    data: StackedAreaData,
    title: str,
    y_label: str,
    output: Optional[str] = None,
    figsize: tuple = (14, 8),
    alpha: float = 0.8,
    show_legend: bool = True,
    y_format: str = "currency",  # 'currency', 'percentage', 'number'
) -> str:
    """Create stacked area chart with optional positive/negative split.

    This creates a "horn shape" visualization:
    - Positive bands stack upward (assets, cash)
    - Negative bands stack downward (withdrawals)
    - Zero line separates them visually
    - Narrow neck visible where bottom positive band approaches zero

    Args:
        data: Chart data with positive/negative series
        title: Chart title
        y_label: Y-axis label
        output: Output file path (PNG/PDF). If None, generates temp file.
        figsize: Figure size as (width, height) in inches
        alpha: Transparency level for bands (0-1)
        show_legend: Whether to show legend
        y_format: Y-axis number format ('currency', 'percentage', 'number')

    Returns:
        Path to saved chart file

    Example:
        >>> from datetime import date
        >>> data = StackedAreaData(
        ...     dates=[date(2024, 1, 1), date(2024, 2, 1)],
        ...     positive_series=[
        ...         SeriesData("Cash", [50000, 48000], "#2ca02c"),
        ...         SeriesData("VOO", [600000, 620000], "#ff7f0e"),
        ...     ],
        ...     negative_series=[
        ...         SeriesData("Withdrawals", [3333, 6666], "#d62728"),
        ...     ]
        ... )
        >>> path = create_stacked_area_chart(
        ...     data=data,
        ...     title="Portfolio Horn Chart",
        ...     y_label="Value ($)",
        ...     output="portfolio.png"
        ... )
    """
    # Set non-interactive backend if saving to file
    if output:
        import matplotlib

        matplotlib.use("Agg")

    # Validate input
    if not isinstance(data, StackedAreaData):
        raise TypeError(f"Expected StackedAreaData, got {type(data)}")

    dates = data.dates

    # Assign colors to series that don't have them
    color_index = 0
    for series in data.positive_series + data.negative_series:
        if series.color is None:
            series.color = get_default_color(color_index)
            color_index += 1

    # Create figure
    fig, ax = plt.subplots(figsize=figsize)

    # Plot positive series (stacked upward from zero)
    if data.positive_series:
        positive_values = np.array([series.values for series in data.positive_series])
        positive_labels = [series.label for series in data.positive_series]
        positive_colors = [series.color for series in data.positive_series]

        ax.stackplot(
            dates,
            positive_values,
            labels=positive_labels,
            colors=positive_colors,
            alpha=alpha,
            baseline="zero",
        )

    # Plot negative series (stacked downward from zero)
    if data.negative_series:
        # Negative values need to be negated for display below zero
        negative_values = np.array([[-v for v in series.values] for series in data.negative_series])
        negative_labels = [series.label for series in data.negative_series]
        negative_colors = [series.color for series in data.negative_series]

        ax.stackplot(
            dates,
            negative_values,
            labels=negative_labels,
            colors=negative_colors,
            alpha=alpha,
            baseline="zero",
        )

    # Add zero line
    ax.axhline(y=0, color="black", linewidth=0.5, linestyle="-", alpha=0.3)

    # Formatting
    ax.set_title(title, fontsize=16, fontweight="bold", pad=20)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel(y_label, fontsize=12)

    # Y-axis formatting
    if y_format == "currency":
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(
                lambda y, _: f"${abs(y)/1e6:.2f}M" if abs(y) >= 1e6 else f"${abs(y)/1e3:.0f}K"
            )
        )
    elif y_format == "percentage":
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.1f}%"))
    # else: default number formatting

    # Legend
    if show_legend and (data.positive_series or data.negative_series):
        ax.legend(
            loc="upper left",
            framealpha=0.9,
            fontsize=10,
            title="Components",
            title_fontsize=11,
        )

    # Grid
    ax.grid(True, alpha=0.3, linestyle="--")

    # Date formatting
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)

    # Tight layout
    plt.tight_layout()

    # Save
    if output is None:
        import tempfile

        output = tempfile.mktemp(suffix=".png")

    plt.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)

    return output


def demo_horn_chart():
    """Create a demo horn chart showing the positive/negative split concept."""
    from datetime import date, timedelta

    print("Creating demo horn chart...")

    # Create sample data simulating a 60/30/10 portfolio with withdrawals
    # User requests: 60% VOO, 30% BIL, 10% BTC-USD
    # Actual allocation: We reserve 10% cash buffer for synthetic dividends
    # So we scale down: 54% VOO, 27% BIL, 9% BTC, 10% USD cash
    start_date = date(2024, 1, 1)
    dates = [start_date + timedelta(days=30 * i) for i in range(12)]

    # Initial investment: $1,000,000
    # Cash (sweeps account) starts at 10% ($100K) and fluctuates with trading/withdrawals
    # Narrow neck occurs when it approaches zero (month 10-11)
    cash_values = [
        100000,
        95000,
        92000,
        88000,
        85000,
        80000,
        75000,
        70000,
        60000,
        45000,
        30000,
        50000,
    ]

    # BIL position (27% = 30% * 0.9) - bonds, relatively stable
    bil_values = [
        270000,
        272000,
        271000,
        275000,
        277000,
        276000,
        280000,
        282000,
        281000,
        285000,
        284000,
        286000,
    ]

    # VOO position (54% = 60% * 0.9) - equities, moderate growth
    voo_values = [
        540000,
        558000,
        549000,
        576000,
        585000,
        580500,
        603000,
        612000,
        621000,
        630000,
        639000,
        648000,
    ]

    # BTC position (9% = 10% * 0.9) - crypto, high volatility
    btc_values = [
        90000,
        99000,
        85500,
        108000,
        103500,
        112500,
        117000,
        108000,
        126000,
        130500,
        135000,
        139500,
    ]

    # Cumulative withdrawals (growing wedge below zero)
    withdrawals = [3333 * (i + 1) for i in range(12)]  # 4% annual = $3,333/month

    data = StackedAreaData(
        dates=dates,
        positive_series=[
            # Bottom to top: least volatile to most volatile
            SeriesData("USD (Cash)", cash_values, "#2ca02c"),  # Green for cash/sweeps
            SeriesData("BIL (Bonds)", bil_values, "#8c564b"),  # Brown for bonds
            SeriesData("VOO (Equities)", voo_values, "#ff7f0e"),  # Orange for stocks
            SeriesData("BTC-USD (Crypto)", btc_values, "#1f77b4"),  # Blue for crypto
        ],
        negative_series=[
            SeriesData("Withdrawals (Spending Power)", withdrawals, "#d62728"),  # Red
        ],
    )

    output = create_stacked_area_chart(
        data=data,
        title="Portfolio Horn Chart - Total Wealth Generated",
        y_label="Value ($)",
        output="demo_horn_chart.png",
    )

    print(f"Demo chart saved to: {output}")
    print()
    print("Key observations:")
    print("- Total horn height = Portfolio value + Cumulative withdrawals")
    print("- Narrow neck visible at month 11 where USD cash dips to $30K")
    print("- Cash starts at 10% buffer ($100K), gradually depletes under withdrawal pressure")
    print("- Withdrawals (red wedge) represent accumulated spending power")
    print("- Both sides of zero line represent positive wealth")
    print()
    print("Portfolio allocation strategy:")
    print("- User requests: 60% VOO, 30% BIL, 10% BTC-USD")
    print("- We reserve: 10% cash buffer for synthetic dividend strategy")
    print("- Actual allocation: 54% VOO, 27% BIL, 9% BTC, 10% USD cash")
    print()
    print("Visual stacking (bottom to top by volatility):")
    print("- USD (Cash/Sweeps) - Green band, buying power (~10% initially)")
    print("- BIL (Bonds) - Brown band, Treasury bills (~27%)")
    print("- VOO (Equities) - Orange band, S&P 500 (~54%)")
    print("- BTC-USD (Crypto) - Blue band, Bitcoin (~9%)")
    print()
    print("Note: Cash is the SWEEPS ACCOUNT (buying power), distinct from BIL position.")
    print("      The 10% buffer prevents forced asset sales during buyback opportunities.")


def create_portfolio_horn_chart(
    portfolio_summary: dict,
    output: Optional[str] = None,
    resample: Optional[str] = None,
) -> str:
    """Create horn chart from actual portfolio backtest results.

    Args:
        portfolio_summary: Summary dict from run_portfolio_backtest
        output: Output file path (default: auto-generated)
        resample: Resampling frequency ('D'=daily, 'W'=weekly, 'M' or 'ME'=monthly, None=daily)

    Returns:
        Path to saved chart file
    """
    from datetime import date  # noqa: F401

    import pandas as pd

    # Extract daily data
    daily_values = portfolio_summary["daily_values"]
    daily_bank = portfolio_summary["daily_bank_values"]
    daily_asset_values = portfolio_summary.get("daily_asset_values", {})
    daily_withdrawals_dict = portfolio_summary.get("daily_withdrawals", {})
    allocations = portfolio_summary["allocations"]

    # Build dates list
    dates = sorted(daily_values.keys())

    # Extract per-asset values
    cash_values = [daily_bank[d] for d in dates]

    # Build per-asset series data
    asset_series_data = {}
    for ticker in allocations.keys():
        if ticker in daily_asset_values:
            asset_series_data[ticker] = [daily_asset_values[ticker].get(d, 0) for d in dates]

    # Handle resampling if requested
    if resample and resample != "D":
        df_data = {"date": dates, "cash": cash_values}
        # Add per-asset columns
        for ticker, values in asset_series_data.items():
            df_data[ticker] = values

        df = pd.DataFrame(df_data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date")

        # Convert deprecated 'M' to 'ME' (month end)
        resample_freq = "ME" if resample == "M" else resample

        # Resample (use mean for values)
        df_resampled = df.resample(resample_freq).mean()

        dates = [d.date() for d in df_resampled.index]
        cash_values = df_resampled["cash"].tolist()

        # Update asset series data with resampled values
        for ticker in asset_series_data.keys():
            asset_series_data[ticker] = df_resampled[ticker].tolist()

    # Build cumulative withdrawals from daily withdrawal events
    cumulative_withdrawals = []
    cumulative = 0.0
    for d in dates:
        if d in daily_withdrawals_dict:
            cumulative += daily_withdrawals_dict[d]
        cumulative_withdrawals.append(cumulative)

    # Define asset volatility order (least to most volatile for stacking)
    # Common ordering: Cash < Bonds (BIL/TLT) < Stocks (VOO/SPY) < Crypto (BTC)
    volatility_order = {
        "BIL": 1,
        "TLT": 1,
        "SHY": 1,  # Bonds
        "VOO": 2,
        "SPY": 2,
        "QQQ": 2,
        "IVV": 2,  # Equity indices
        "AAPL": 3,
        "MSFT": 3,
        "GOOG": 3,
        "NVDA": 3,  # Tech stocks
        "GLD": 3,
        "GLDM": 3,  # Gold
        "BTC-USD": 4,
        "ETH-USD": 4,  # Crypto
    }

    # Sort assets by volatility (lowest to highest for bottom-to-top stacking)
    sorted_tickers = sorted(
        asset_series_data.keys(),
        key=lambda t: (volatility_order.get(t, 2.5), t),  # Default to mid-range if unknown
    )

    # Build positive series (bottom to top: cash, then assets by volatility)
    positive_series = [SeriesData("USD (Cash)", cash_values, "#2ca02c")]

    # Asset color palette (different from cash green)
    asset_colors = ["#8c564b", "#ff7f0e", "#1f77b4", "#9467bd", "#e377c2"]

    for i, ticker in enumerate(sorted_tickers):
        color = asset_colors[i % len(asset_colors)]
        # Add asset type label
        if ticker in ["BIL", "TLT", "SHY"]:
            label = f"{ticker} (Bonds)"
        elif ticker in ["VOO", "SPY", "QQQ", "IVV"]:
            label = f"{ticker} (Equities)"
        elif ticker in ["BTC-USD", "ETH-USD"]:
            label = f"{ticker} (Crypto)"
        else:
            label = ticker

        positive_series.append(SeriesData(label, asset_series_data[ticker], color))

    # Build negative series (withdrawals)
    negative_series = []
    if cumulative_withdrawals and cumulative_withdrawals[-1] > 0:
        negative_series.append(
            SeriesData("Withdrawals (Spending Power)", cumulative_withdrawals, "#d62728")
        )

    data = StackedAreaData(
        dates=dates,
        positive_series=positive_series,
        negative_series=negative_series,
    )

    # Create title with summary stats
    start_date = portfolio_summary["start_date"]
    end_date = portfolio_summary["end_date"]
    total_return = portfolio_summary["total_return"]
    annualized_return = portfolio_summary["annualized_return"]
    total_withdrawn = portfolio_summary.get("total_withdrawn", 0)

    title = f"Portfolio Horn Chart: {start_date} to {end_date}\n"
    title += f"Total Return: {total_return:.2f}% | Annualized: {annualized_return:.2f}%"

    if total_withdrawn > 0:
        title += f" | Withdrawn: ${total_withdrawn:,.0f}"

    return create_stacked_area_chart(
        data=data,
        title=title,
        y_label="Value ($)",
        output=output,
    )


if __name__ == "__main__":
    demo_horn_chart()
