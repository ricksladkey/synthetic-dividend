from datetime import date
from typing import Dict, List, Tuple
import pandas as pd


def buy_and_hold_backtest(df: pd.DataFrame, ticker: str, qty: int, start_date: date, end_date: date) -> Tuple[List[str], Dict[str, object]]:
    """Perform a simple buy-and-hold backtest over `df` which must contain a 'Close' column.

    Returns (transactions, summary) where transactions is a list of strings and summary is a dict
    with keys matching the GUI summary fields.
    """
    if df is None or df.empty:
        raise ValueError("Empty price data")

    df_indexed = df.copy()
    df_indexed.index = pd.to_datetime(df_indexed.index).date

    try:
        first_idx = min(d for d in df_indexed.index if d >= start_date)
        last_idx = max(d for d in df_indexed.index if d <= end_date)
    except ValueError:
        raise ValueError("No overlapping trading days in requested date range.")

    start_price = float(df_indexed.loc[first_idx]["Close"])
    end_price = float(df_indexed.loc[last_idx]["Close"])

    start_value = qty * start_price
    end_value = qty * end_price
    total_return = (end_value - start_value) / start_value if start_value != 0 else 0.0

    days = (last_idx - first_idx).days
    years = days / 365.25 if days > 0 else 0.0
    if years > 0 and start_value > 0:
        annualized = (end_value / start_value) ** (1.0 / years) - 1.0
    else:
        annualized = 0.0

    transactions = [f"{first_idx.isoformat()} BUY {qty} {ticker} @ {start_price:.2f} = {start_value:.2f}"]

    summary = {
        "ticker": ticker,
        "start_date": first_idx,
        "start_price": start_price,
        "start_value": start_value,
        "end_date": last_idx,
        "end_price": end_price,
        "end_value": end_value,
        "total_return": total_return,
        "annualized": annualized,
        "years": years,
    }

    return transactions, summary
