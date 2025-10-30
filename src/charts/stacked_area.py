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
    n_dates = len(dates)

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
            baseline='zero',
        )

    # Plot negative series (stacked downward from zero)
    if data.negative_series:
        # Negative values need to be negated for display below zero
        negative_values = np.array([
            [-v for v in series.values] for series in data.negative_series
        ])
        negative_labels = [series.label for series in data.negative_series]
        negative_colors = [series.color for series in data.negative_series]

        ax.stackplot(
            dates,
            negative_values,
            labels=negative_labels,
            colors=negative_colors,
            alpha=alpha,
            baseline='zero',
        )

    # Add zero line
    ax.axhline(y=0, color='black', linewidth=0.5, linestyle='-', alpha=0.3)

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
    # Classic-plus-crypto: 60% VOO, 30% BIL, 10% BTC-USD
    start_date = date(2024, 1, 1)
    dates = [start_date + timedelta(days=30 * i) for i in range(12)]

    # Simulate portfolio with monthly withdrawals
    # Cash (sweeps account) starts at ~3% and fluctuates based on trading/withdrawals
    cash_values = [30000, 28000, 32000, 25000, 29000, 23000, 27000, 21000, 26000, 20000, 25000, 18000]

    # BIL position (~30% of portfolio) - bonds, relatively stable
    bil_values = [300000, 302000, 301000, 305000, 307000, 306000, 310000, 312000, 311000, 315000, 314000, 316000]

    # VOO position (~60% of portfolio) - equities, moderate growth
    voo_values = [600000, 620000, 610000, 640000, 650000, 645000, 670000, 680000, 690000, 700000, 710000, 720000]

    # BTC position (~10% of portfolio) - crypto, high volatility
    btc_values = [100000, 110000, 95000, 120000, 115000, 125000, 130000, 120000, 140000, 145000, 150000, 155000]

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
    print("- Narrow neck visible around month 8 where USD cash dips to $20K")
    print("- Withdrawals (red wedge) represent accumulated spending power")
    print("- Both sides of zero line represent positive wealth")
    print()
    print("Portfolio structure (60/30/10):")
    print("- BTC-USD (Crypto) - Top band, most volatile")
    print("- VOO (Equities) - Orange band, moderate volatility")
    print("- BIL (Bonds) - Brown band, low volatility")
    print("- USD (Cash/Sweeps) - Green band, buying power for trading")
    print()
    print("Note: Cash is the SWEEPS ACCOUNT (buying power), distinct from BIL position")


if __name__ == "__main__":
    demo_horn_chart()
