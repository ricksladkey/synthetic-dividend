from datetime import date
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import pandas as pd
from abc import ABC, abstractmethod
import re


def calculate_synthetic_dividend_orders(
    holdings: int,
    last_transaction_price: float,
    rebalance_size: float,
    profit_sharing: float
) -> dict:
    """Pure function to calculate synthetic dividend buy/sell orders.
    
    The formulas ensure perfect symmetry: if you buy Q shares at price P_low,
    then from P_low you can sell exactly Q shares back at price P_current.
    
    Derivation:
    - Buy price: P_buy = P / (1 + r)
    - Sell price: P_sell = P * (1 + r)
    - Buy quantity: Q_buy = r * H * s
    - Sell quantity: Q_sell = r * H * s / (1 + r)
    
    Where r = rebalance_size, H = holdings, s = profit_sharing
    
    Args:
        holdings: Current number of shares held
        last_transaction_price: Price of last transaction
        rebalance_size: Rebalance threshold as decimal (e.g., 0.0905 for 9.05%)
        profit_sharing: Profit sharing ratio as decimal (e.g., 0.5 for 50%)
    
    Returns:
        Dict with keys: next_buy_price, next_buy_qty, next_sell_price, next_sell_qty
    """
    # Calculate next buy price and quantity
    next_buy_price = last_transaction_price / (1 + rebalance_size)
    next_buy_qty = int(rebalance_size * holdings * profit_sharing + 0.5)
    
    # Calculate next sell price and quantity
    next_sell_price = last_transaction_price * (1 + rebalance_size)
    next_sell_qty = int(rebalance_size * holdings * profit_sharing / (1 + rebalance_size) + 0.5)
    
    return {
        "next_buy_price": next_buy_price,
        "next_buy_qty": next_buy_qty,
        "next_sell_price": next_sell_price,
        "next_sell_qty": next_sell_qty,
    }


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


def _get_price_scalar_from_row(price_row: pd.Series, col_name: str) -> Optional[float]:
    """Extract a float scalar from a price_row Series for the given column name.

    Handles cases where price_row[col_name] may itself be a Series (e.g., multi-index or
    when a single-row DataFrame is returned). Returns None if the column isn't present.
    """
    if col_name not in price_row.index:
        return None
    val = price_row[col_name]
    # If val is a Series (e.g., labelled by ticker), take the first numeric value
    if hasattr(val, 'iloc'):
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


class AlgorithmBase(ABC):
    """Algorithm instance that can maintain state across days.

    Implement on_day(date, price_row, holdings, bank, history) -> Optional[Transaction]
    """

    def __init__(self, params: Optional[dict] = None):
        self.params = params or {}

    @abstractmethod
    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        pass

    @abstractmethod
    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        pass

    @abstractmethod
    def on_end_holding(self) -> None:
        pass


class BuyAndHoldAlgorithm(AlgorithmBase):
    """Buy-and-hold algorithm: never issues further transactions after initial buy.
    """
    def __init__(self, rebalance_size_pct: float = 0.0, profit_sharing_pct: float = 0.0, params: Optional[dict] = None):
        super().__init__(params)

    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        pass

    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        return None

    def on_end_holding(self) -> None:
        pass


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

        self.total_volatility_alpha: float = 0.0

        self.last_transaction_price: float

        self.next_buy_price: float
        self.next_buy_qty: float
        self.next_sell_price: float
        self.next_sell_qty: float


    def place_orders(self, holdings, current_price: float) -> None:
        """Update internal state with new orders based on current price."""
        # Record the last transaction price
        self.last_transaction_price = current_price

        # Use pure function to calculate orders
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=current_price,
            rebalance_size=self.rebalance_size,
            profit_sharing=self.profit_sharing
        )
        
        self.next_buy_price = orders["next_buy_price"]
        self.next_buy_qty = orders["next_buy_qty"]
        self.next_sell_price = orders["next_sell_price"]
        self.next_sell_qty = orders["next_sell_qty"]

        print(f"Placing orders for last transaction price: ${self.last_transaction_price}")
        print(f"  Next BUY: {self.next_buy_qty} @ ${self.next_buy_price:.2f} = ${self.next_buy_price * self.next_buy_qty:.2f}")
        print(f"  Next SELL: {self.next_sell_qty} @ ${self.next_sell_price:.2f} = ${self.next_sell_price * self.next_sell_qty:.2f}")


    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        
        # Initialize the first buy parameters
        self.place_orders(holdings, current_price)


    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        try:

            # Retrieve high and low prices for the day as float scalars.
            open = _get_price_scalar_from_row(price_row, 'Open')
            high = _get_price_scalar_from_row(price_row, 'High')
            low = _get_price_scalar_from_row(price_row, 'Low')
            close = _get_price_scalar_from_row(price_row, 'Close')

            # Validate and execute buy/sell orders based on price thresholds.
            if low is not None and high is not None:

                if False:  # Set to True to enable debug output

                    # Evaluate buy/sell orders based on the day's price range
                    # Format as numeric floats for clearer debug output
                    low_s = f"{low:.2f}" if low is not None else "N/A"
                    high_s = f"{high:.2f}" if high is not None else "N/A"
                    print(f"Evaluating orders on {date_.isoformat()}: Low=${low_s}, High=${high_s}")

                # Check for buy opportunity
                if low <= self.next_buy_price:

                    # Account for market gapping down, assuming
                    # a standing limit order at next_buy_price.
                    actual_price = min(self.next_buy_price, open)
                    current_value = holdings * actual_price
                    profit = (self.last_transaction_price - actual_price) * self.next_buy_qty
                    alpha = (profit / current_value) * 100 if current_value != 0 else 0.0
                    self.total_volatility_alpha += alpha
                    notes = f"Buying back: limit price = {self.next_buy_price:.2f}, actual price = {actual_price:.2f}"
                    transaction = Transaction(action="BUY", qty=self.next_buy_qty, notes=notes)

                    # Place orders again with UPDATED holdings (after the buy)
                    updated_holdings = holdings + self.next_buy_qty
                    self.place_orders(updated_holdings, self.next_buy_price)

                    return transaction


                # Check for sell opportunity
                if high >= self.next_sell_price:

                    # Account for market gapping up, assuming
                    # a standing limit order at next_sell_price.
                    actual_price = max(self.next_sell_price, open)
                    notes = f"Taking profits: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f}"
                    transaction = Transaction(action="SELL", qty=self.next_sell_qty, notes=notes)

                    # Place orders again with UPDATED holdings (after the sell)
                    updated_holdings = holdings - self.next_sell_qty
                    self.place_orders(updated_holdings, self.next_sell_price)

                    return transaction

        except Exception:
            pass
        return None


    def on_end_holding(self) -> None:
        print(f"Synthetic Dividend Algorithm total volatility alpha: {self.total_volatility_alpha:.2f}%")


class SyntheticDividendATHOnlyAlgorithm(AlgorithmBase):
    """ATH-only variant: sells only at all-time highs, never buybacks.
    
    This serves as a baseline to validate the full SyntheticDividendAlgorithm.
    At every new ATH, both algorithms should have the same share count.
    The full algorithm makes additional buyback/resell cycles that should net to zero.
    
    Parameters parsed from name (example): 'synthetic-dividend-ath-only/9.15%/50%'
      - rebalance_size_pct: float (e.g. 9.15)
      - profit_sharing_pct: float (0-100)
    """

    def __init__(self, rebalance_size_pct: float = 0.0, profit_sharing_pct: float = 0.0, params: Optional[dict] = None):
        super().__init__(params)

        self.rebalance_size = float(rebalance_size_pct)/100.0
        self.profit_sharing = float(profit_sharing_pct)/100.0

        # Track all-time high price
        self.ath_price: float = 0.0
        
        # Order state (only for sell orders at ATH)
        self.last_transaction_price: float
        self.next_sell_price: float
        self.next_sell_qty: int

    def place_orders(self, holdings: int, current_price: float) -> None:
        """Calculate next sell order at new ATH."""
        self.last_transaction_price = current_price
        
        # Use same formula as full algorithm for sell orders
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=current_price,
            rebalance_size=self.rebalance_size,
            profit_sharing=self.profit_sharing
        )
        
        self.next_sell_price = orders["next_sell_price"]
        self.next_sell_qty = orders["next_sell_qty"]
        
        print(f"ATH-only: New ATH at ${current_price:.2f}, placing sell order:")
        print(f"  Next SELL: {self.next_sell_qty} @ ${self.next_sell_price:.2f} = ${self.next_sell_price * self.next_sell_qty:.2f}")

    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        # Initialize ATH and place first sell order
        self.ath_price = current_price
        self.place_orders(holdings, current_price)

    def on_day(self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame) -> Optional[Transaction]:
        try:
            # Retrieve prices for the day
            open_price = _get_price_scalar_from_row(price_row, 'Open')
            high = _get_price_scalar_from_row(price_row, 'High')
            low = _get_price_scalar_from_row(price_row, 'Low')
            close = _get_price_scalar_from_row(price_row, 'Close')

            if high is not None:
                # Check if we reached a new ATH
                if high > self.ath_price:
                    # Update ATH
                    self.ath_price = high
                    
                    # Check if we should execute the sell order
                    if high >= self.next_sell_price:
                        # Account for market gapping up
                        actual_price = max(self.next_sell_price, open_price) if open_price is not None else self.next_sell_price
                        notes = f"ATH-only sell: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f}, new ATH = {self.ath_price:.2f}"
                        transaction = Transaction(action="SELL", qty=self.next_sell_qty, notes=notes)
                        
                        # Place next sell order with UPDATED holdings (after the sell)
                        updated_holdings = holdings - self.next_sell_qty
                        self.place_orders(updated_holdings, self.next_sell_price)
                        
                        return transaction

        except Exception:
            pass
        return None

    def on_end_holding(self) -> None:
        print(f"ATH-only algorithm: final ATH = ${self.ath_price:.2f}")


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

    # Match ATH-only variant first (more specific pattern)
    m = re.match(r"^synthetic-dividend-ath-only/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%$", name)
    if m:
        rebalance = float(m.group(1))
        profit = float(m.group(2))
        return SyntheticDividendATHOnlyAlgorithm(rebalance_size_pct=rebalance, profit_sharing_pct=profit)

    # Match full synthetic-dividend
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

    # tell algo about initial holdings
    algo_obj.on_new_holdings(holdings, start_price)

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

            # give algo the day to process
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
            transactions.append(f"{d.isoformat()} SELL {sell_qty} {ticker} @ {price:.2f} = {proceeds:.2f}, holdings = {holdings}, bank = {bank:.2f}  # {tx.notes}")
        elif tx.action.upper() == "BUY":
            buy_qty = int(tx.qty)
            cost = buy_qty * price
            holdings += buy_qty
            bank -= cost
            transactions.append(f"{d.isoformat()} BUY {buy_qty} {ticker} @ {price:.2f} = {cost:.2f}, holdings = {holdings}, bank = {bank:.2f}  # {tx.notes}")
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

    # Notify the algorithm that the holding period has ended
    # Compute a buy-and-hold baseline on the same date range for simple alpha comparison.
    try:
        # baseline holdings = initial_qty, baseline end value = initial_qty * end_price
        baseline_end_value = initial_qty * final_price
        baseline_total = baseline_end_value  # bank is zero for buy-and-hold
        baseline_total_return = (baseline_total - start_val) / start_val if start_val != 0 else 0.0
        if years > 0 and start_val > 0:
            baseline_annualized = (baseline_total / start_val) ** (1.0 / years) - 1.0
        else:
            baseline_annualized = 0.0

        baseline_summary = {
            "start_date": first_idx,
            "end_date": last_idx,
            "start_price": start_price,
            "end_price": final_price,
            "start_value": start_val,
            "end_value": baseline_end_value,
            "total": baseline_total,
            "total_return": baseline_total_return,
            "annualized": baseline_annualized,
        }

        # volatility_alpha defined as difference in total_return vs buy-and-hold baseline
        volatility_alpha = total_return - baseline_total_return

        summary["baseline"] = baseline_summary
        summary["volatility_alpha"] = volatility_alpha
    except Exception:
        # Do not fail the backtest if baseline computation has an edge-case; omit alpha
        summary["baseline"] = None
        summary["volatility_alpha"] = None
    algo_obj.on_end_holding()

    return transactions, summary

