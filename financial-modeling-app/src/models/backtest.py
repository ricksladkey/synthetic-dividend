from datetime import date
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import pandas as pd
from abc import ABC, abstractmethod
import re


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


class AlgorithmBase(ABC):
    """Algorithm instance that can maintain state across days.

    Implement on_day(date, price_row, holdings, bank, history) -> Optional[Transaction]
    """

    def __init__(self, params: Optional[dict] = None):
        self.params = params or {}

    @abstractmethod
    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        pass


class BuyAndHoldAlgorithm(AlgorithmBase):
    """Buy-and-hold algorithm: never issues further transactions after initial buy.
    """
    def __init__(self, rebalance_size_pct: float = 0.0, profit_sharing_pct: float = 0.0, params: Optional[dict] = None):
        super().__init__(params)

    def buy_holdings(self, holdings: int, current_price: float) -> None:
        pass

    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        return None


class SyntheticDividendAlgorithm(AlgorithmBase):
    """Skeleton for the Synthetic Dividend algorithm.

    Parameters parsed from name (example): 'synthetic-dividend/9.15%/50%'
      - rebalance_size_pct: float (e.g. 9.15)
      - profit_sharing_pct: float (0-100)

    This class can maintain state like hi_price_qty and lo_price_qty for internal bookkeeping.
    TODO: implement the actual rebalancing logic.
    """

    def __init__(self, rebalance_size_pct: float = 0.0, profit_sharing_pct: float = 0.0, params: Optional[dict] = None):
        super().__init__(params)
        self.rebalance_size = float(rebalance_size_pct)/100.0
        self.profit_sharing = float(profit_sharing_pct)/100.0

        self.last_transaction_price: float

        self.next_buy_price: float
        self.next_buy_qty: float
        self.next_sell_price: float
        self.next_sell_qty: float

    def buy_holdings(self, holdings: int, current_price: float) -> None:
        
        # Initialize the first buy parameters
        self.place_orders(holdings, current_price)


    def place_orders(self, holdings, current_price: float) -> None:

        # Record the last transaction price
        self.last_transaction_price = current_price
        print(f"Placing orders at current price: {self.last_transaction_price}")

        # Calculate next buy price and quantity
        self.next_buy_price = self.last_transaction_price / (1 + self.rebalance_size)
        next_buy_amount = (self.next_buy_price - self.last_transaction_price) * holdings * self.profit_sharing
        self.next_buy_qty = int(next_buy_amount / self.next_buy_price + 0.5)

        # Calculate next sell price and quantity
        self.next_sell_price = self.last_transaction_price * (1 + self.rebalance_size)
        next_sell_amount = (self.next_sell_price - self.last_transaction_price) * holdings * self.profit_sharing
        self.next_sell_qty = int(next_sell_amount / self.next_sell_price + 0.5)


    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        try:

            # Retrieve high and low prices for the day.
            high = price_row['High'] if 'High' in price_row.index else None
            low = price_row['Low'] if 'Low' in price_row.index else None

            # Validate and execute buy/sell orders based on price thresholds.
            if low is not None and high is not None:

                # Check for buy opportunity
                if low <= self.next_buy_price <= high:

                    # Place orders again to update next prices/quantities
                    self.place_orders(holdings, self.next_buy_price)

                    notes = f"{date_.isoformat()} BUY {holdings} @ {self.next_buy_price:.2f} = {self.next_buy_price * self.next_buy_qty:.2f}"
                    return Transaction(action="BUY", qty=self.next_buy_qty, notes=notes)

                # Check for sell opportunity
                if low <= self.next_sell_price <= high:
                    
                    # Place orders again to update next prices/quantities
                    self.place_orders(holdings, self.next_sell_price)

                    notes = f"{date_.isoformat()} SELL {holdings} @ {self.next_sell_price:.2f} = {self.next_sell_price * self.next_sell_qty:.2f}"
                    return Transaction(action="SELL", qty=self.next_sell_qty, notes=notes)

        except Exception:
            pass
        return None


def build_algo_from_name(name: str) -> AlgorithmBase:
    """Parse strategy name identifiers into algorithm instances.

    Examples:
      - 'buy-and-hold' -> BuyAndHoldAlgorithm()
      - 'synthetic-dividend/9.15%/50%' -> SyntheticDividendAlgorithm(9.15, 50)
    """
    name = name.strip()

    # Record the strategy name supplied by the user
    print(f"Building algorithm from name: {name}")

    if name == "buy-and-hold":
        return BuyAndHoldAlgorithm()

    m = re.match(r"^synthetic-dividend/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%$", name)
    if m:
        rebalance = float(m.group(1))
        profit = float(m.group(2))
        return SyntheticDividendAlgorithm(rebalance_size_pct=rebalance, profit_sharing_pct=profit)

    raise ValueError(f"Unrecognized strategy name: {name}")


def run_algorithm_backtest(
    df: pd.DataFrame,
    ticker: str,
    initial_qty: int,
    start_date: date,
    end_date: date,
    algo: Optional[object] = None,
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

    # Set the initial conditions for the backtesting of the algorithm
    holdings = int(initial_qty)
    bank = 0.0

    start_value = holdings * start_price
    transactions.append(f"{first_idx.isoformat()} BUY {holdings} {ticker} @ {start_price:.2f} = {start_value:.2f}")

    # iterate through subsequent trading days and call the algo
    dates = sorted(d for d in df_indexed.index if d >= first_idx and d <= last_idx)
    # history will be the price DataFrame up to but not including current day when passed
    # normalize algo into an object with on_day(date, price_row, holdings, bank, history)
    if algo is None:
        algo_obj = BuyAndHoldAlgorithm()
    elif isinstance(algo, AlgorithmBase):
        algo_obj = algo
    elif callable(algo):
        # adapt a simple callable to AlgorithmBase
        class _FuncAdapter(AlgorithmBase):
            def __init__(self, fn):
                super().__init__()
                self.fn = fn

            def on_day(self, date_, price_row, holdings, bank, history):
                return self.fn(date_, price_row, holdings, bank, history, algo_params)

        algo_obj = _FuncAdapter(algo)
    else:
        raise ValueError("algo must be AlgorithmBase instance or callable")

    # initial buy holdings setup
    algo_obj.buy_holdings(holdings, start_price)

    # iterate through dates
    for i, d in enumerate(dates):
        if d == first_idx:
            # skip calling algo on the initial buy day (per spec: buy then call for consecutive days)
            continue

        price_row = df_indexed.loc[d]
        price = _get_close_scalar(df_indexed, d, "Close")

        # pass history up to previous day
        history = df_indexed.loc[:dates[i - 1]] if i > 0 else df_indexed.loc[:d]

        try:
            tx = algo_obj.on_day(d, price_row, holdings, bank, history)
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

