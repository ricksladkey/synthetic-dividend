"""PDF report generation for backtest results.

This module creates comprehensive PDF reports showing:
- Backtest summary and parameters
- Price chart with buy/sell transaction markers
- Transaction log with running balances
- Performance analysis and metrics
- Observations and recommendations
"""

import re
from datetime import date
from typing import Any, Dict, List, Optional

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_pdf import PdfPages


def _extract_limit_price(notes: str) -> Optional[float]:
    """Extract algorithmic limit price from transaction notes.

    Args:
        notes: Transaction notes containing limit price info

    Returns:
        Limit price if found, None otherwise
    """
    # Pattern: "limit=$52.53"
    match = re.search(r"limit=\$?([\d,]+\.?\d*)", notes)
    if match:
        price_str = match.group(1).replace(",", "")
        try:
            return float(price_str)
        except ValueError:
            pass
    return None


def create_backtest_pdf_report(
    ticker: str,
    transactions: List[Any],
    summary: Dict[str, Any],
    price_data: pd.DataFrame,
    output_path: str,
    comparative_results: Optional[Dict[str, Any]] = None,
) -> str:
    """Create comprehensive PDF report for backtest results.

    Args:
        ticker: Asset ticker symbol
        transactions: List of Transaction objects from backtest
        summary: Summary dict from backtest
        price_data: DataFrame with OHLC price data
        output_path: Output PDF file path
        comparative_results: Optional dict with comparative backtest results

    Returns:
        Path to generated PDF file
    """
    with PdfPages(output_path) as pdf:
        # Page 1: Title and Summary
        _create_summary_page(pdf, ticker, summary)

        # Page 2: Price Chart with Transaction Markers
        _create_price_chart_page(pdf, ticker, transactions, price_data)

        # Page 3+: Transaction Log
        _create_transaction_log_pages(pdf, ticker, transactions, summary)

        # Comparison page if comparative results provided
        if comparative_results:
            _create_comparison_page(pdf, ticker, summary, comparative_results)

        # Final Page: Analysis and Recommendations
        _create_analysis_page(pdf, ticker, summary, transactions)

    return output_path


def _create_summary_page(pdf: PdfPages, ticker: str, summary: Dict[str, Any]):
    """Create title page with backtest summary."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis("off")

    # Title
    title_text = f"Backtest Report: {ticker}"
    ax.text(
        0.5,
        0.95,
        title_text,
        ha="center",
        va="top",
        fontsize=24,
        fontweight="bold",
        transform=ax.transAxes,
    )

    # Report date
    ax.text(
        0.5,
        0.90,
        f"Generated: {date.today()}",
        ha="center",
        va="top",
        fontsize=10,
        color="gray",
        transform=ax.transAxes,
    )

    # Summary box
    summary_y = 0.82
    ax.text(
        0.5,
        summary_y,
        "BACKTEST SUMMARY",
        ha="center",
        va="top",
        fontsize=16,
        fontweight="bold",
        transform=ax.transAxes,
    )

    y_pos = summary_y - 0.05

    # Basic info
    basic_metrics = [
        ("Period", f"{summary.get('start_date', 'N/A')} to {summary.get('end_date', 'N/A')}"),
        ("Algorithm", summary.get("algorithm_name", "N/A")),
        ("", ""),
    ]

    for label, value in basic_metrics:
        if label:
            ax.text(
                0.25, y_pos, label + ":", ha="left", va="top", fontsize=11, transform=ax.transAxes
            )
            ax.text(
                0.75,
                y_pos,
                str(value),
                ha="right",
                va="top",
                fontsize=11,
                fontweight="bold",
                transform=ax.transAxes,
            )
        y_pos -= 0.04

    # Initial Portfolio breakdown
    initial_investment = summary.get("initial_investment", 0)
    start_price = summary.get("start_price", 0)
    initial_qty = int(initial_investment / start_price) if start_price > 0 else 0
    initial_asset_value = initial_qty * start_price
    initial_cash = 0.0  # Start with no cash

    ax.text(
        0.5,
        y_pos,
        "INITIAL PORTFOLIO",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        transform=ax.transAxes,
        color="#0066CC",
    )
    y_pos -= 0.04

    # Use simpler format to avoid text overlap
    initial_portfolio_metrics = [
        (f"  {ticker}", f"{initial_qty:,} shares"),
        ("", f"${initial_asset_value:,.2f}"),
        ("  USD (cash sweeps)", f"${initial_cash:,.2f}"),
        ("  Portfolio Value", f"${initial_investment:,.2f}"),
        ("", ""),
    ]

    for label, value in initial_portfolio_metrics:
        if label or value:  # Allow lines with just value (for continuation)
            ax.text(0.25, y_pos, label, ha="left", va="top", fontsize=10, transform=ax.transAxes)
            ax.text(
                0.75,
                y_pos,
                str(value),
                ha="right",
                va="top",
                fontsize=10,
                fontweight="bold",
                transform=ax.transAxes,
            )
        y_pos -= 0.035

    # Final Portfolio breakdown
    final_holdings = summary.get("final_holdings", 0)
    final_price = summary.get("final_price", 0)
    final_asset_value = final_holdings * final_price
    final_cash = summary.get("final_bank", 0)
    final_portfolio_value = summary.get("final_portfolio_value", 0)

    ax.text(
        0.5,
        y_pos,
        "FINAL PORTFOLIO",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        transform=ax.transAxes,
        color="#00AA00",
    )
    y_pos -= 0.04

    final_portfolio_metrics = [
        (f"  {ticker}", f"{final_holdings:,} shares"),
        ("", f"${final_asset_value:,.2f}"),
        ("  USD (cash sweeps)", f"${final_cash:,.2f}"),
        ("  Portfolio Value", f"${final_portfolio_value:,.2f}"),
        ("", ""),
    ]

    for label, value in final_portfolio_metrics:
        if label or value:
            ax.text(0.25, y_pos, label, ha="left", va="top", fontsize=10, transform=ax.transAxes)
            ax.text(
                0.75,
                y_pos,
                str(value),
                ha="right",
                va="top",
                fontsize=10,
                fontweight="bold",
                transform=ax.transAxes,
            )
        y_pos -= 0.035

    # Performance metrics
    ax.text(
        0.5,
        y_pos,
        "PERFORMANCE",
        ha="center",
        va="top",
        fontsize=12,
        fontweight="bold",
        transform=ax.transAxes,
        color="#AA00AA",
    )
    y_pos -= 0.04

    performance_metrics = [
        ("  Total Return", f"{summary.get('total_return_pct', 0):.2f}%"),
        ("  Annualized Return", f"{summary.get('annualized_return_pct', 0):.2f}%"),
        ("", ""),
    ]

    for label, value in performance_metrics:
        if label:
            ax.text(0.25, y_pos, label, ha="left", va="top", fontsize=10, transform=ax.transAxes)
            ax.text(
                0.75,
                y_pos,
                str(value),
                ha="right",
                va="top",
                fontsize=10,
                fontweight="bold",
                transform=ax.transAxes,
            )
        y_pos -= 0.04

    # Transaction summary
    transaction_metrics = [
        ("Total Transactions", f"{summary.get('transaction_count', 0)}"),
        ("  Buy Transactions", f"{summary.get('buy_count', 0)}"),
        ("  Sell Transactions", f"{summary.get('sell_count', 0)}"),
    ]

    for label, value in transaction_metrics:
        ax.text(0.25, y_pos, label + ":", ha="left", va="top", fontsize=10, transform=ax.transAxes)
        ax.text(
            0.75,
            y_pos,
            str(value),
            ha="right",
            va="top",
            fontsize=10,
            fontweight="bold",
            transform=ax.transAxes,
        )
        y_pos -= 0.04

    # Additional metrics if available
    if summary.get("sharpe_ratio"):
        y_pos -= 0.02
        ax.text(
            0.5,
            y_pos,
            "RISK METRICS",
            ha="center",
            va="top",
            fontsize=14,
            fontweight="bold",
            transform=ax.transAxes,
        )
        y_pos -= 0.04

        risk_metrics = [
            ("Sharpe Ratio", f"{summary.get('sharpe_ratio', 0):.2f}"),
            ("Max Drawdown", f"{summary.get('max_drawdown_pct', 0):.2f}%"),
            ("Volatility", f"{summary.get('volatility_pct', 0):.2f}%"),
        ]

        for label, value in risk_metrics:
            ax.text(
                0.25, y_pos, label + ":", ha="left", va="top", fontsize=11, transform=ax.transAxes
            )
            ax.text(
                0.75,
                y_pos,
                str(value),
                ha="right",
                va="top",
                fontsize=11,
                fontweight="bold",
                transform=ax.transAxes,
            )
            y_pos -= 0.04

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _create_price_chart_page(
    pdf: PdfPages,
    ticker: str,
    transactions: List[Any],
    price_data: pd.DataFrame,
):
    """Create price chart with buy/sell markers."""
    fig, ax = plt.subplots(figsize=(11, 8.5))

    # Plot price data
    dates = pd.to_datetime(price_data.index)
    prices = price_data["Close"]

    ax.plot(dates, prices, linewidth=2, color="#2E86AB", label="Close Price")

    # Add transaction markers
    buy_dates = []
    buy_prices = []
    sell_dates = []
    sell_prices = []

    for tx in transactions:
        # Use limit price for chart markers if available (shows algorithmic behavior),
        # otherwise fall back to fill price
        display_price = tx.limit_price if tx.limit_price is not None else tx.price

        if tx.action == "BUY":
            buy_dates.append(tx.transaction_date)
            buy_prices.append(display_price)
        elif tx.action == "SELL":
            sell_dates.append(tx.transaction_date)
            sell_prices.append(display_price)

    # Plot buy markers (red dots - money going out)
    if buy_dates:
        ax.scatter(
            buy_dates,
            buy_prices,
            color="red",
            s=100,
            marker="o",
            zorder=5,
            label=f"Buy ({len(buy_dates)} transactions)",
            alpha=0.8,
        )

    # Plot sell markers (green dots - money coming in)
    if sell_dates:
        ax.scatter(
            sell_dates,
            sell_prices,
            color="green",
            s=100,
            marker="o",
            zorder=5,
            label=f"Sell ({len(sell_dates)} transactions)",
            alpha=0.8,
        )

    # Formatting
    ax.set_xlabel("Date", fontsize=12, fontweight="bold")
    ax.set_ylabel("Price ($)", fontsize=12, fontweight="bold")
    ax.set_title(f"{ticker} Price Chart with Transactions", fontsize=16, fontweight="bold", pad=20)
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.legend(loc="best", fontsize=10)

    # Format dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.xticks(rotation=45)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f"${x:,.2f}"))

    plt.tight_layout()
    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _create_transaction_log_pages(
    pdf: PdfPages,
    ticker: str,
    transactions: List[Any],
    summary: Dict[str, Any],
):
    """Create transaction log with running balances."""
    # Calculate running balances
    running_bank = summary.get("initial_investment", 0)
    running_holdings = 0

    tx_data = []
    for tx in transactions:
        # Use actual market price for balance calculations
        if tx.action == "BUY":
            cost = tx.qty * tx.price
            running_bank -= cost
            running_holdings += tx.qty
        elif tx.action == "SELL":
            proceeds = tx.qty * tx.price
            running_bank += proceeds
            running_holdings -= tx.qty

        portfolio_value = running_bank + (running_holdings * tx.price)

        # Show both limit price (algorithmic target) and fill price (actual execution)
        limit_str = f"${tx.limit_price:.2f}" if tx.limit_price is not None else "-"
        fill_str = f"${tx.price:.2f}"

        tx_data.append(
            {
                "Date": str(tx.transaction_date),
                "Action": tx.action,
                "Qty": tx.qty,
                "Limit": limit_str,  # Algorithmic target price
                "Fill": fill_str,  # Actual execution price
                "Amount": f"${tx.qty * tx.price:,.2f}",  # Actual cash amount
                "Holdings": running_holdings,
                "Bank": f"${running_bank:,.2f}",
                "Portfolio": f"${portfolio_value:,.2f}",
            }
        )

    # Create pages with transaction tables
    rows_per_page = 35
    total_pages = (len(tx_data) + rows_per_page - 1) // rows_per_page

    for page_num in range(total_pages):
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis("off")

        # Title
        ax.text(
            0.5,
            0.98,
            f"Transaction Log (Page {page_num + 1} of {total_pages})",
            ha="center",
            va="top",
            fontsize=14,
            fontweight="bold",
            transform=ax.transAxes,
        )

        # Get transactions for this page
        start_idx = page_num * rows_per_page
        end_idx = min(start_idx + rows_per_page, len(tx_data))
        page_data = tx_data[start_idx:end_idx]

        # Create table
        col_labels = [
            "Date",
            "Action",
            "Qty",
            "Limit",
            "Fill",
            "Amount",
            "Holdings",
            "Bank",
            "Portfolio",
        ]
        cell_text = [[row[col] for col in col_labels] for row in page_data]

        # Calculate appropriate table height based on number of rows
        # Each row needs about 0.025 height units, plus header
        num_rows = len(page_data) + 1  # +1 for header
        table_height = min(0.88, num_rows * 0.025 + 0.05)  # Cap at 0.88 max

        table = ax.table(
            cellText=cell_text,
            colLabels=col_labels,
            cellLoc="center",
            loc="upper center",
            bbox=[0.05, 0.92 - table_height, 0.9, table_height],  # type: ignore[arg-type]
        )

        table.auto_set_font_size(False)
        table.set_fontsize(7)  # Smaller font to fit extra column
        table.scale(1, 1.5)

        # Style header
        for i in range(len(col_labels)):
            cell = table[(0, i)]
            cell.set_facecolor("#2E86AB")
            cell.set_text_props(weight="bold", color="white")

        # Alternate row colors
        for i in range(1, len(page_data) + 1):
            for j in range(len(col_labels)):
                cell = table[(i, j)]
                if i % 2 == 0:
                    cell.set_facecolor("#f0f0f0")

                # Color-code actions
                if j == 1:  # Action column
                    if page_data[i - 1]["Action"] == "BUY":
                        cell.set_text_props(color="red", weight="bold")  # Red = money out
                    elif page_data[i - 1]["Action"] == "SELL":
                        cell.set_text_props(color="green", weight="bold")  # Green = money in

        pdf.savefig(fig, bbox_inches="tight")
        plt.close(fig)


def _create_analysis_page(
    pdf: PdfPages,
    ticker: str,
    summary: Dict[str, Any],
    transactions: List[Any],
):
    """Create analysis and recommendations page."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis("off")

    # Title
    ax.text(
        0.5,
        0.95,
        "Analysis & Recommendations",
        ha="center",
        va="top",
        fontsize=18,
        fontweight="bold",
        transform=ax.transAxes,
    )

    y_pos = 0.88

    # Performance Analysis
    ax.text(
        0.1,
        y_pos,
        "PERFORMANCE ANALYSIS",
        ha="left",
        va="top",
        fontsize=14,
        fontweight="bold",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round", facecolor="#2E86AB", alpha=0.3),
    )
    y_pos -= 0.05

    observations = _generate_observations(summary, transactions)
    for obs in observations:
        wrapped_text = _wrap_text(obs, 85)
        ax.text(
            0.1,
            y_pos,
            f"• {wrapped_text}",
            ha="left",
            va="top",
            fontsize=10,
            transform=ax.transAxes,
            wrap=True,
        )
        y_pos -= 0.04 * (wrapped_text.count("\n") + 1)

    y_pos -= 0.03

    # Recommendations
    ax.text(
        0.1,
        y_pos,
        "RECOMMENDATIONS",
        ha="left",
        va="top",
        fontsize=14,
        fontweight="bold",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round", facecolor="#A23B72", alpha=0.3),
    )
    y_pos -= 0.05

    recommendations = _generate_recommendations(summary, transactions)
    for rec in recommendations:
        wrapped_text = _wrap_text(rec, 85)
        ax.text(
            0.1,
            y_pos,
            f"• {wrapped_text}",
            ha="left",
            va="top",
            fontsize=10,
            transform=ax.transAxes,
            wrap=True,
        )
        y_pos -= 0.04 * (wrapped_text.count("\n") + 1)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _generate_observations(summary: Dict[str, Any], transactions: List[Any]) -> List[str]:
    """Generate analytical observations from backtest results."""
    observations = []

    # Return analysis
    total_return = summary.get("total_return_pct", 0)
    if total_return > 0:
        observations.append(
            f"Positive return of {total_return:.2f}% demonstrates profitable strategy execution."
        )
    else:
        observations.append(
            f"Negative return of {total_return:.2f}% indicates strategy underperformance in this period."
        )

    # Transaction frequency
    tx_count = summary.get("transaction_count", 0)
    days = summary.get("trading_days", 0)
    if days > 0:
        tx_per_month = (tx_count / days) * 21  # Approx trading days per month
        observations.append(
            f"Average transaction frequency: {tx_per_month:.1f} transactions per month "
            f"({tx_count} total over {days} trading days)."
        )

    # Bank balance
    final_bank = summary.get("final_bank", 0)
    initial_inv = summary.get("initial_investment", 1)
    bank_pct = (final_bank / initial_inv) * 100 if initial_inv > 0 else 0
    observations.append(
        f"Final cash position: ${final_bank:,.2f} ({bank_pct:.1f}% of initial investment). "
        f"{'Sufficient liquidity maintained.' if bank_pct > 5 else 'Low cash reserves.'}"
    )

    # Volatility harvesting (if applicable)
    buy_count = summary.get("buy_count", 0)
    sell_count = summary.get("sell_count", 0)
    if buy_count > 0 and sell_count > 0:
        observations.append(
            f"Strategy executed {sell_count} sales and {buy_count} buybacks, "
            f"indicating active volatility harvesting."
        )

    return observations


def _generate_recommendations(summary: Dict[str, Any], transactions: List[Any]) -> List[str]:
    """Generate recommendations based on backtest results."""
    recommendations = []

    # Parameter optimization
    algo_name = summary.get("algorithm_name", "")
    if "sd" in algo_name.lower():
        recommendations.append(
            "Consider running parameter sweep to find optimal rebalancing threshold "
            "for this asset's volatility profile."
        )

    # Risk management
    final_bank = summary.get("final_bank", 0)
    if final_bank < 0:
        recommendations.append(
            "Negative cash balance indicates margin usage. Consider stricter bank balance "
            "enforcement or lower profit-sharing percentage."
        )

    # Extended backtesting
    recommendations.append(
        "Validate strategy across multiple market cycles (bull, bear, sideways) "
        "to confirm robustness."
    )

    # Transaction costs
    tx_count = summary.get("transaction_count", 0)
    if tx_count > 100:
        recommendations.append(
            f"High transaction count ({tx_count}) may incur significant trading costs. "
            "Include commission/slippage in analysis."
        )

    return recommendations


def _create_comparison_page(
    pdf: PdfPages,
    ticker: str,
    primary_summary: Dict[str, Any],
    comparative_results: Dict[str, Any],
):
    """Create comparison page showing SD8 vs other strategies."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis("off")

    # Title
    ax.text(
        0.5,
        0.95,
        "Strategy Comparison",
        ha="center",
        va="top",
        fontsize=18,
        fontweight="bold",
        transform=ax.transAxes,
    )

    y_pos = 0.88

    # Create comparison table
    strategies = []
    final_values = []
    total_returns = []
    annualized_returns = []
    transaction_counts = []

    # Primary strategy (SD8)
    algo_name = primary_summary.get("algorithm_name", "SD8")
    strategies.append(algo_name)
    final_values.append(f"${primary_summary.get('final_portfolio_value', 0):,.2f}")
    total_returns.append(f"{primary_summary.get('total_return_pct', 0):.2f}%")
    annualized_returns.append(f"{primary_summary.get('annualized_return_pct', 0):.2f}%")
    transaction_counts.append(str(primary_summary.get("transaction_count", 0)))

    # Comparative strategies
    for strategy_name in ["buy_and_hold", "sd8_ath_only"]:
        if strategy_name in comparative_results:
            result = comparative_results[strategy_name]
            display_name = {"buy_and_hold": "Buy & Hold", "sd8_ath_only": "SD8 ATH-Only"}.get(
                strategy_name, strategy_name
            )

            strategies.append(display_name)
            final_values.append(f"${result.get('final_portfolio_value', 0):,.2f}")
            total_returns.append(f"{result.get('total_return_pct', 0):.2f}%")
            annualized_returns.append(f"{result.get('annualized_return_pct', 0):.2f}%")
            transaction_counts.append(str(result.get("transaction_count", 0)))

    # Create table data
    col_labels = ["Strategy", "Final Value", "Total Return", "Annualized", "Transactions"]
    cell_text = list(
        zip(strategies, final_values, total_returns, annualized_returns, transaction_counts)
    )

    # Calculate table height
    num_rows = len(strategies) + 1  # +1 for header
    table_height = min(0.6, num_rows * 0.045 + 0.05)

    table = ax.table(
        cellText=cell_text,
        colLabels=col_labels,
        cellLoc="center",
        loc="upper center",
        bbox=[0.05, 0.82 - table_height, 0.9, table_height],  # type: ignore[arg-type]
    )

    table.auto_set_font_size(False)
    table.set_fontsize(9)
    table.scale(1, 1.8)

    # Style header
    for i in range(len(col_labels)):
        cell = table[(0, i)]
        cell.set_facecolor("#2E86AB")
        cell.set_text_props(weight="bold", color="white")

    # Alternate row colors and highlight primary strategy
    for i in range(1, len(strategies) + 1):
        for j in range(len(col_labels)):
            cell = table[(i, j)]
            if i == 1:  # Primary strategy (SD8)
                cell.set_facecolor("#FFE5B4")  # Peach highlight
                cell.set_text_props(weight="bold")
            elif i % 2 == 0:
                cell.set_facecolor("#f0f0f0")

    # Analysis text
    y_pos = 0.82 - table_height - 0.08

    ax.text(
        0.1,
        y_pos,
        "COMPARATIVE ANALYSIS",
        ha="left",
        va="top",
        fontsize=14,
        fontweight="bold",
        transform=ax.transAxes,
        bbox=dict(boxstyle="round", facecolor="#2E86AB", alpha=0.3),
    )
    y_pos -= 0.05

    # Generate insights with alpha decomposition
    insights = []

    # Alpha Decomposition: Calculate Synthetic Alpha and Volatility Alpha
    primary_return = primary_summary.get("annualized_return_pct", 0)
    bh_return = comparative_results.get("buy_and_hold", {}).get("annualized_return_pct", 0)
    ath_return = comparative_results.get("sd8_ath_only", {}).get("annualized_return_pct", 0)

    # Synthetic Alpha (Primary): return(sd8-ath-only) - return(buy-and-hold)
    # This measures the value of profit-taking at all-time highs vs pure holding
    synthetic_alpha = ath_return - bh_return if ath_return and bh_return else None

    # Volatility Alpha (Secondary): return(sd8) - return(sd8-ath-only)
    # This measures the additional value from buying dips (volatility harvesting)
    volatility_alpha = primary_return - ath_return if ath_return else None

    # Display Alpha Decomposition
    if synthetic_alpha is not None or volatility_alpha is not None:
        insights.append("ALPHA DECOMPOSITION:")

        if synthetic_alpha is not None:
            insights.append(
                f"  Synthetic Alpha (Primary): {synthetic_alpha:+.2f}% annualized. "
                f"This is return(SD8-ATH-Only) - return(Buy-and-Hold), measuring the value "
                f"of systematic profit-taking at all-time highs."
            )

        if volatility_alpha is not None:
            insights.append(
                f"  Volatility Alpha (Secondary): {volatility_alpha:+.2f}% annualized. "
                f"This is return(SD8) - return(SD8-ATH-Only), measuring the additional value "
                f"from buying dips and harvesting volatility."
            )

        # Total alpha
        if synthetic_alpha is not None and volatility_alpha is not None:
            total_alpha = synthetic_alpha + volatility_alpha
            insights.append(
                f"  Total Alpha: {total_alpha:+.2f}% annualized (Synthetic + Volatility)."
            )

    # Burn rate information
    burn_rate = comparative_results.get("buy_and_hold", {}).get("burn_rate_pct", 0)
    if burn_rate > 0:
        insights.append(
            f"All strategies tested with {burn_rate:.2f}% annual burn rate "
            f"(maximum sustainable rate from SD8 minimum bank balance). "
            f"This ensures fair comparison with realistic expense/withdrawal scenarios."
        )

    # Transaction efficiency
    primary_tx = primary_summary.get("transaction_count", 0)
    insights.append(
        f"SD8 generated {primary_tx} transactions. Higher transaction count indicates "
        f"more frequent rebalancing opportunities from volatility."
    )

    # Display insights
    for insight in insights:
        wrapped_text = _wrap_text(insight, 85)
        ax.text(
            0.1,
            y_pos,
            f"• {wrapped_text}",
            ha="left",
            va="top",
            fontsize=10,
            transform=ax.transAxes,
            wrap=True,
        )
        y_pos -= 0.04 * (wrapped_text.count("\n") + 1.5)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def _wrap_text(text: str, width: int) -> str:
    """Simple text wrapping for better formatting."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        if current_length + len(word) + 1 <= width:
            current_line.append(word)
            current_length += len(word) + 1
        else:
            lines.append(" ".join(current_line))
            current_line = [word]
            current_length = len(word) + 1

    if current_line:
        lines.append(" ".join(current_line))

    return "\n  ".join(lines)
