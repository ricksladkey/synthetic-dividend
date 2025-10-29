"""Utility functions for backtesting algorithms."""

import math
from typing import Any, Dict, Optional, Union

import pandas as pd


def calculate_synthetic_dividend_orders(
    holdings: int,
    last_transaction_price: float,
    rebalance_size: float,
    profit_sharing: float,
    bracket_seed: Optional[float] = None,
) -> Dict[str, Union[float, int]]:
    """Pure function to calculate synthetic dividend buy/sell orders.

    The formulas ensure perfect symmetry: if you buy Q shares at price P_low,
    then from P_low you can sell exactly Q shares back at price P_current.

    Derivation:
    - Buy price: P_buy = P / (1 + r)
    - Sell price: P_sell = P * (1 + r)
    - Buy quantity: Q_buy = r * H * s
    - Sell quantity: Q_sell = r * H * s / (1 + r)

    Where r = rebalance_size, H = holdings, s = profit_sharing

    When bracket_seed is provided, prices are normalized to align with seed-based
    bracket positions, ensuring all calculations use the same bracket ladder.

    Args:
        holdings: Current number of shares held
        last_transaction_price: Price of last transaction
        rebalance_size: Rebalance threshold as decimal (e.g., 0.0905 for 9.05%)
        profit_sharing: Profit sharing ratio as decimal (e.g., 0.5 for 50%)
        bracket_seed: Optional seed price to align bracket positions (e.g., 100.0)

    Returns:
        Dict with keys: next_buy_price, next_buy_qty, next_sell_price, next_sell_qty
    """
    # If bracket_seed is provided, normalize last_transaction_price to bracket ladder
    anchor_price = last_transaction_price
    if bracket_seed is not None and bracket_seed > 0 and rebalance_size > 0:
        # Calculate which bracket the current price is on
        bracket_n = math.log(last_transaction_price) / math.log(1 + rebalance_size)
        bracket_rounded = round(bracket_n)
        # Normalize to the exact bracket position
        anchor_price = math.pow(1 + rebalance_size, bracket_rounded)

    # Buy at r% below anchor price
    next_buy_price: float = anchor_price / (1 + rebalance_size)
    # Buy quantity: r * H * s, rounded to nearest integer
    next_buy_qty: int = int(rebalance_size * holdings * profit_sharing + 0.5)

    # Sell at r% above anchor price
    next_sell_price: float = anchor_price * (1 + rebalance_size)
    # Sell quantity: symmetric formula ensures roundtrip balance
    next_sell_qty: int = int(
        rebalance_size * holdings * profit_sharing / (1 + rebalance_size) + 0.5
    )

    return {
        "next_buy_price": next_buy_price,
        "next_buy_qty": next_buy_qty,
        "next_sell_price": next_sell_price,
        "next_sell_qty": next_sell_qty,
    }


def _get_close_scalar(df: pd.DataFrame, idx: Any, col_name: str = "Close") -> float:
    """Extract scalar float from DataFrame at given index/column.

    Handles multi-index columns and Series-wrapped values.
    """
    val = df.loc[idx]
    if isinstance(val, pd.Series):
        # Multi-index columns: try to find the requested column
        if col_name in val.index:
            v = val[col_name]
        else:
            # Fallback: first numeric value
            v = val.iloc[0]
    else:
        v = val

    # Unwrap if value is still a Series
    if hasattr(v, "iloc"):
        try:
            return float(v.iloc[0])
        except Exception:
            return float(v)
    return float(v)


def _get_price_scalar_from_row(price_row: pd.Series, col_name: str) -> Optional[float]:
    """Extract scalar float from Series row for given column.

    Handles multi-index scenarios where value may itself be a Series.
    Returns None if column missing or conversion fails.
    """
    if col_name not in price_row.index:
        return None
    val = price_row[col_name]
    # Unwrap Series if ticker-labeled or multi-indexed
    if hasattr(val, "iloc"):
        try:
            return float(val.iloc[0])
        except Exception:
            try:
                return float(val)
            except Exception:
                return None
    try:
        return float(val)
    except Exception:
        return None
