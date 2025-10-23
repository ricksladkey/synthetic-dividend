from datetime import date
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import pandas as pd


@dataclass
class Transaction:
    action: str  # 'BUY' or 'SELL'
    qty: int
    notes: str = ""


def _get_close_scalar(df: pd.DataFrame, idx, col_name="Close") -> float:
    """Return a scalar close price for df.loc[idx][col]. Handles both single-value and Series results."""
    val = df.loc[idx]
    if isinstance(val, pd.Series):
        # if multiindexed columns, val may be a Series; try to find Close
        if col_name in val.index:
            v = val[col_name]
        else:
            # fallback to the first numeric value
            v = val.iloc[0]
    else:
        v = val
    # If v is a Series (e.g., single-column DataFrame row), take iloc[0]
    if hasattr(v, "iloc"):
        try:
            return float(v.iloc[0])
        except Exception:
            return float(v)
    return float(v)


def default_algo(date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame, params: Optional[dict] = None) -> Optional[Transaction]:
    """Default algorithm: buy-and-hold -> return None (no transactions).

    Signature: (date, price_row, holdings, bank, history, params) -> Transaction | None
    """
    return None


def run_algorithm_backtest(
    df: pd.DataFrame,
    ticker: str,
    initial_qty: int,
    start_date: date,
    end_date: date,
    algo: Callable = default_algo,
    algo_params: Optional[dict] = None,
) -> Tuple[List[str], Dict[str, object]]:
    """Run a generic per-day algorithmic backtest.

    Behavior:
    - Performs an initial BUY of `initial_qty` shares on the first available trading day >= start_date.
    - For each subsequent trading day up to end_date, calls `algo(date, price_row, holdings, bank, history, algo_params)`
      which may return a Transaction (BUY/SELL) or None.
    - SELL increases bank by qty * close_price (qty capped at holdings).
    - BUY decreases bank by qty * close_price and increases holdings (bank may go negative).

    Returns (transactions, summary)
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

    # determine close column / value for first and last
    start_price = _get_close_scalar(df_indexed, first_idx, "Close")
    end_price = _get_close_scalar(df_indexed, last_idx, "Close")

    transactions: List[str] = []

    holdings = int(initial_qty)
    bank = 0.0

    start_value = holdings * start_price
    transactions.append(f"{first_idx.isoformat()} BUY {holdings} {ticker} @ {start_price:.2f} = {start_value:.2f}")

    # iterate through subsequent trading days and call the algo
    dates = sorted(d for d in df_indexed.index if d >= first_idx and d <= last_idx)
    # history will be the price DataFrame up to but not including current day when passed
    for i, d in enumerate(dates):
        if d == first_idx:
            # skip calling algo on the initial buy day (per spec: buy then call for consecutive days)
            continue

        price_row = df_indexed.loc[d]
        price = _get_close_scalar(df_indexed, d, "Close")

        # pass history up to previous day
        history = df_indexed.loc[:dates[i - 1]] if i > 0 else df_indexed.loc[:d]

        try:
            tx = algo(d, price_row, holdings, bank, history, algo_params)
        except Exception as e:
            raise RuntimeError(f"Algorithm raised an error on {d}: {e}")

        if tx is None:
            continue

        if not isinstance(tx, Transaction):
            raise ValueError("Algorithm must return a Transaction or None")

        if tx.action.upper() == "SELL":
            sell_qty = min(int(tx.qty), holdings)
            proceeds = sell_qty * price
            holdings -= sell_qty
            bank += proceeds
            transactions.append(f"{d.isoformat()} SELL {sell_qty} {ticker} @ {price:.2f} = {proceeds:.2f}  # {tx.notes}")
        elif tx.action.upper() == "BUY":
            buy_qty = int(tx.qty)
            cost = buy_qty * price
            holdings += buy_qty
            bank -= cost
            transactions.append(f"{d.isoformat()} BUY {buy_qty} {ticker} @ {price:.2f} = {cost:.2f}  # {tx.notes}")
        else:
            raise ValueError("Transaction action must be 'BUY' or 'SELL'")

    # final values
    final_price = end_price
    end_value = holdings * final_price
    total = bank + end_value

    days = (last_idx - first_idx).days
    years = days / 365.25 if days > 0 else 0.0
    start_val = initial_qty * start_price
    total_return = (total - start_val) / start_val if start_val != 0 else 0.0
    if years > 0 and start_val > 0:
        annualized = (total / start_val) ** (1.0 / years) - 1.0
    else:
        annualized = 0.0

    summary = {
        "ticker": ticker,
        "start_date": first_idx,
        "start_price": start_price,
        "start_value": start_val,
        "end_date": last_idx,
        "end_price": final_price,
        "end_value": end_value,
        "holdings": holdings,
        "bank": bank,
        "total": total,
        "total_return": total_return,
        "annualized": annualized,
        "years": years,
    }

    return transactions, summary

