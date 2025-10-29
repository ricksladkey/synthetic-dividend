"""Visualization tools for plotting price charts with trade markers.

This module provides functions to create matplotlib charts showing
historical price data overlaid with buy/sell transaction points.
"""

import re
from typing import Any, Dict, List, Optional

import matplotlib.pyplot as plt
import pandas as pd


def _parse_transaction_line(line: str):
    """Return dict with date (str), action (BUY/SELL), price (float) if parseable."""
    if not line or not line.strip():
        return None

    # Attempt to find an ISO date anywhere in the line
    date_match = re.search(r"(\d{4}-\d{2}-\d{2})", line)
    date = date_match.group(1) if date_match else None

    # Find action token (BUY or SELL)
    action_match = re.search(r"\b(BUY|SELL)\b", line, flags=re.IGNORECASE)
    action = action_match.group(1).upper() if action_match else None

    # Find price after '@' optionally preceded by $ and/or followed by '=' (e.g. '@ $123.45' or '@ 123.45 = 12345.00')
    m = re.search(r"@\s*\$?([0-9,]+(?:\.[0-9]+)?)", line)
    price = None
    if m:
        try:
            price = float(m.group(1).replace(",", ""))
        except Exception:
            price = None

    return {"date": date, "action": action, "price": price}


def plot_price_with_trades(
    df: pd.DataFrame,
    transactions: List[str],
    ticker: str,
    out_png: str,
    summary: Optional[Dict[str, Any]] = None,
):
    """Plot price series and overlay buy/sell markers parsed from transactions.

    Buys = red dots, Sells = green dots. Saves PNG to out_png.
    """
    if df is None or df.empty:
        raise ValueError("Empty price data for plotting")

    # Ensure datetime index
    df_plot = df.copy()
    df_plot.index = pd.to_datetime(df_plot.index)

    # Prefer Close column
    if "Close" in df_plot.columns:
        price_series = df_plot["Close"]
    elif "Adj Close" in df_plot.columns:
        price_series = df_plot["Adj Close"]
    else:
        # fallback to first numeric column
        price_series = df_plot.select_dtypes(include=["number"]).iloc[:, 0]

    buys_x = []
    buys_y = []
    sells_x = []
    sells_y = []

    for line in transactions:
        parsed = _parse_transaction_line(line)
        if not parsed or not parsed.get("date"):
            continue
        try:
            dt = pd.to_datetime(parsed["date"])
        except Exception:
            continue
        price = parsed.get("price")
        # if price missing, try to lookup close price for that date
        if price is None:
            try:
                price = float(price_series.loc[dt])
            except Exception:
                price = None
        if parsed.get("action") == "BUY":
            buys_x.append(dt)
            buys_y.append(price)
        elif parsed.get("action") == "SELL":
            sells_x.append(dt)
            sells_y.append(price)

    fig, ax = plt.subplots(figsize=(12, 6))
    ax.plot(price_series.index, price_series.values, label=f"{ticker} Close", color="blue")

    if buys_x:
        ax.scatter(buys_x, buys_y, color="red", marker="o", s=50, zorder=5, label="BUYS")
    if sells_x:
        ax.scatter(sells_x, sells_y, color="green", marker="o", s=50, zorder=5, label="SELLS")

    ax.set_title(f"{ticker} price with trade markers")
    ax.set_xlabel("Date")
    ax.set_ylabel("Price")
    ax.legend()
    # Optionally annotate the chart with summary metrics (e.g., volatility alpha)
    if summary:
        try:
            va = summary.get("volatility_alpha")
            if va is not None:
                text = f"Volatility alpha: {va*100:.2f}%"
                # Place annotation in the upper-left inside the axes
                ax.text(
                    0.01,
                    0.98,
                    text,
                    transform=ax.transAxes,
                    fontsize=10,
                    verticalalignment="top",
                    bbox=dict(facecolor="white", alpha=0.6, edgecolor="none"),
                )
        except Exception:
            # Non-critical: chart should still render even if annotation fails
            pass
    fig.tight_layout()
    fig.savefig(out_png)
    plt.close(fig)
