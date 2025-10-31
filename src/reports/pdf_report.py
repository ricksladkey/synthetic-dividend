"""PDF report generation for backtest results.

This module creates comprehensive PDF reports showing:
- Backtest summary and parameters
- Price chart with buy/sell transaction markers
- Transaction log with running balances
- Performance analysis and metrics
- Observations and recommendations
"""

from datetime import date
from typing import Dict, List, Optional, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_pdf import PdfPages
import matplotlib.patches as mpatches
import pandas as pd
import numpy as np
import re


def _extract_limit_price(notes: str) -> Optional[float]:
    """Extract algorithmic limit price from transaction notes.

    Args:
        notes: Transaction notes containing limit price info

    Returns:
        Limit price if found, None otherwise
    """
    # Pattern: "limit=$52.53"
    match = re.search(r'limit=\$?([\d,]+\.?\d*)', notes)
    if match:
        price_str = match.group(1).replace(',', '')
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
) -> str:
    """Create comprehensive PDF report for backtest results.

    Args:
        ticker: Asset ticker symbol
        transactions: List of Transaction objects from backtest
        summary: Summary dict from backtest
        price_data: DataFrame with OHLC price data
        output_path: Output PDF file path

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

        # Final Page: Analysis and Recommendations
        _create_analysis_page(pdf, ticker, summary, transactions)

    return output_path


def _create_summary_page(pdf: PdfPages, ticker: str, summary: Dict[str, Any]):
    """Create title page with backtest summary."""
    fig = plt.figure(figsize=(8.5, 11))
    ax = fig.add_subplot(111)
    ax.axis('off')

    # Title
    title_text = f"Backtest Report: {ticker}"
    ax.text(0.5, 0.95, title_text, ha='center', va='top',
            fontsize=24, fontweight='bold', transform=ax.transAxes)

    # Report date
    ax.text(0.5, 0.90, f"Generated: {date.today()}", ha='center', va='top',
            fontsize=10, color='gray', transform=ax.transAxes)

    # Summary box
    summary_y = 0.82
    ax.text(0.5, summary_y, "BACKTEST SUMMARY", ha='center', va='top',
            fontsize=16, fontweight='bold', transform=ax.transAxes)

    # Key metrics
    metrics = [
        ("Period", f"{summary.get('start_date', 'N/A')} to {summary.get('end_date', 'N/A')}"),
        ("Algorithm", summary.get('algorithm_name', 'N/A')),
        ("Initial Investment", f"${summary.get('initial_investment', 0):,.2f}"),
        ("Final Portfolio Value", f"${summary.get('final_portfolio_value', 0):,.2f}"),
        ("Total Return", f"{summary.get('total_return_pct', 0):.2f}%"),
        ("Annualized Return", f"{summary.get('annualized_return_pct', 0):.2f}%"),
        ("", ""),
        ("Final Holdings", f"{summary.get('final_holdings', 0):,} shares"),
        ("Final Share Price", f"${summary.get('final_price', 0):.2f}"),
        ("Final Bank Balance", f"${summary.get('final_bank', 0):,.2f}"),
        ("", ""),
        ("Total Transactions", f"{summary.get('transaction_count', 0)}"),
        ("Buy Transactions", f"{summary.get('buy_count', 0)}"),
        ("Sell Transactions", f"{summary.get('sell_count', 0)}"),
    ]

    y_pos = summary_y - 0.05
    for label, value in metrics:
        if label:  # Skip empty lines for spacing
            ax.text(0.25, y_pos, label + ":", ha='left', va='top',
                   fontsize=11, transform=ax.transAxes)
            ax.text(0.75, y_pos, str(value), ha='right', va='top',
                   fontsize=11, fontweight='bold', transform=ax.transAxes)
        y_pos -= 0.04

    # Additional metrics if available
    if summary.get('sharpe_ratio'):
        y_pos -= 0.02
        ax.text(0.5, y_pos, "RISK METRICS", ha='center', va='top',
               fontsize=14, fontweight='bold', transform=ax.transAxes)
        y_pos -= 0.04

        risk_metrics = [
            ("Sharpe Ratio", f"{summary.get('sharpe_ratio', 0):.2f}"),
            ("Max Drawdown", f"{summary.get('max_drawdown_pct', 0):.2f}%"),
            ("Volatility", f"{summary.get('volatility_pct', 0):.2f}%"),
        ]

        for label, value in risk_metrics:
            ax.text(0.25, y_pos, label + ":", ha='left', va='top',
                   fontsize=11, transform=ax.transAxes)
            ax.text(0.75, y_pos, str(value), ha='right', va='top',
                   fontsize=11, fontweight='bold', transform=ax.transAxes)
            y_pos -= 0.04

    pdf.savefig(fig, bbox_inches='tight')
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
    prices = price_data['Close']

    ax.plot(dates, prices, linewidth=2, color='#2E86AB', label='Close Price')

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
        ax.scatter(buy_dates, buy_prices, color='red', s=100, marker='o',
                  zorder=5, label=f'Buy ({len(buy_dates)} transactions)', alpha=0.8)

    # Plot sell markers (green dots - money coming in)
    if sell_dates:
        ax.scatter(sell_dates, sell_prices, color='green', s=100, marker='o',
                  zorder=5, label=f'Sell ({len(sell_dates)} transactions)', alpha=0.8)

    # Formatting
    ax.set_xlabel('Date', fontsize=12, fontweight='bold')
    ax.set_ylabel('Price ($)', fontsize=12, fontweight='bold')
    ax.set_title(f'{ticker} Price Chart with Transactions', fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, alpha=0.3, linestyle='--')
    ax.legend(loc='best', fontsize=10)

    # Format dates
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45)

    # Format y-axis as currency
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.2f}'))

    plt.tight_layout()
    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def _create_transaction_log_pages(
    pdf: PdfPages,
    ticker: str,
    transactions: List[Any],
    summary: Dict[str, Any],
):
    """Create transaction log with running balances."""
    # Calculate running balances
    running_bank = summary.get('initial_investment', 0)
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
        limit_str = f'${tx.limit_price:.2f}' if tx.limit_price is not None else '-'
        fill_str = f'${tx.price:.2f}'

        tx_data.append({
            'Date': str(tx.transaction_date),
            'Action': tx.action,
            'Qty': tx.qty,
            'Limit': limit_str,  # Algorithmic target price
            'Fill': fill_str,  # Actual execution price
            'Amount': f'${tx.qty * tx.price:,.2f}',  # Actual cash amount
            'Holdings': running_holdings,
            'Bank': f'${running_bank:,.2f}',
            'Portfolio': f'${portfolio_value:,.2f}',
        })

    # Create pages with transaction tables
    rows_per_page = 35
    total_pages = (len(tx_data) + rows_per_page - 1) // rows_per_page

    for page_num in range(total_pages):
        fig = plt.figure(figsize=(11, 8.5))
        ax = fig.add_subplot(111)
        ax.axis('off')

        # Title
        ax.text(0.5, 0.98, f"Transaction Log (Page {page_num + 1} of {total_pages})",
               ha='center', va='top', fontsize=14, fontweight='bold',
               transform=ax.transAxes)

        # Get transactions for this page
        start_idx = page_num * rows_per_page
        end_idx = min(start_idx + rows_per_page, len(tx_data))
        page_data = tx_data[start_idx:end_idx]

        # Create table
        col_labels = ['Date', 'Action', 'Qty', 'Limit', 'Fill', 'Amount', 'Holdings', 'Bank', 'Portfolio']
        cell_text = [[row[col] for col in col_labels] for row in page_data]

        table = ax.table(cellText=cell_text, colLabels=col_labels,
                        cellLoc='center', loc='center',
                        bbox=[0.05, 0.05, 0.9, 0.88])

        table.auto_set_font_size(False)
        table.set_fontsize(7)  # Smaller font to fit extra column
        table.scale(1, 1.5)

        # Style header
        for i in range(len(col_labels)):
            cell = table[(0, i)]
            cell.set_facecolor('#2E86AB')
            cell.set_text_props(weight='bold', color='white')

        # Alternate row colors
        for i in range(1, len(page_data) + 1):
            for j in range(len(col_labels)):
                cell = table[(i, j)]
                if i % 2 == 0:
                    cell.set_facecolor('#f0f0f0')

                # Color-code actions
                if j == 1:  # Action column
                    if page_data[i-1]['Action'] == 'BUY':
                        cell.set_text_props(color='red', weight='bold')  # Red = money out
                    elif page_data[i-1]['Action'] == 'SELL':
                        cell.set_text_props(color='green', weight='bold')  # Green = money in

        pdf.savefig(fig, bbox_inches='tight')
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
    ax.axis('off')

    # Title
    ax.text(0.5, 0.95, "Analysis & Recommendations", ha='center', va='top',
           fontsize=18, fontweight='bold', transform=ax.transAxes)

    y_pos = 0.88

    # Performance Analysis
    ax.text(0.1, y_pos, "PERFORMANCE ANALYSIS", ha='left', va='top',
           fontsize=14, fontweight='bold', transform=ax.transAxes,
           bbox=dict(boxstyle='round', facecolor='#2E86AB', alpha=0.3))
    y_pos -= 0.05

    observations = _generate_observations(summary, transactions)
    for obs in observations:
        wrapped_text = _wrap_text(obs, 85)
        ax.text(0.1, y_pos, f"• {wrapped_text}", ha='left', va='top',
               fontsize=10, transform=ax.transAxes, wrap=True)
        y_pos -= 0.04 * (wrapped_text.count('\n') + 1)

    y_pos -= 0.03

    # Recommendations
    ax.text(0.1, y_pos, "RECOMMENDATIONS", ha='left', va='top',
           fontsize=14, fontweight='bold', transform=ax.transAxes,
           bbox=dict(boxstyle='round', facecolor='#A23B72', alpha=0.3))
    y_pos -= 0.05

    recommendations = _generate_recommendations(summary, transactions)
    for rec in recommendations:
        wrapped_text = _wrap_text(rec, 85)
        ax.text(0.1, y_pos, f"• {wrapped_text}", ha='left', va='top',
               fontsize=10, transform=ax.transAxes, wrap=True)
        y_pos -= 0.04 * (wrapped_text.count('\n') + 1)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def _generate_observations(summary: Dict[str, Any], transactions: List[Any]) -> List[str]:
    """Generate analytical observations from backtest results."""
    observations = []

    # Return analysis
    total_return = summary.get('total_return_pct', 0)
    if total_return > 0:
        observations.append(
            f"Positive return of {total_return:.2f}% demonstrates profitable strategy execution."
        )
    else:
        observations.append(
            f"Negative return of {total_return:.2f}% indicates strategy underperformance in this period."
        )

    # Transaction frequency
    tx_count = summary.get('transaction_count', 0)
    days = summary.get('trading_days', 0)
    if days > 0:
        tx_per_month = (tx_count / days) * 21  # Approx trading days per month
        observations.append(
            f"Average transaction frequency: {tx_per_month:.1f} transactions per month "
            f"({tx_count} total over {days} trading days)."
        )

    # Bank balance
    final_bank = summary.get('final_bank', 0)
    initial_inv = summary.get('initial_investment', 1)
    bank_pct = (final_bank / initial_inv) * 100 if initial_inv > 0 else 0
    observations.append(
        f"Final cash position: ${final_bank:,.2f} ({bank_pct:.1f}% of initial investment). "
        f"{'Sufficient liquidity maintained.' if bank_pct > 5 else 'Low cash reserves.'}"
    )

    # Volatility harvesting (if applicable)
    buy_count = summary.get('buy_count', 0)
    sell_count = summary.get('sell_count', 0)
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
    algo_name = summary.get('algorithm_name', '')
    if 'sd' in algo_name.lower():
        recommendations.append(
            "Consider running parameter sweep to find optimal rebalancing threshold "
            "for this asset's volatility profile."
        )

    # Risk management
    final_bank = summary.get('final_bank', 0)
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
    tx_count = summary.get('transaction_count', 0)
    if tx_count > 100:
        recommendations.append(
            f"High transaction count ({tx_count}) may incur significant trading costs. "
            "Include commission/slippage in analysis."
        )

    return recommendations


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
            lines.append(' '.join(current_line))
            current_line = [word]
            current_length = len(word) + 1

    if current_line:
        lines.append(' '.join(current_line))

    return '\n  '.join(lines)
