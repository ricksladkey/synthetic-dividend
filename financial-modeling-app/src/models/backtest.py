"""Backtest engine for algorithmic trading strategies.

Provides abstract base for strategy implementations and execution framework
for backtesting against historical OHLC price data.
"""

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd


def calculate_synthetic_dividend_orders(
    holdings: int, last_transaction_price: float, rebalance_size: float, profit_sharing: float
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

    Args:
        holdings: Current number of shares held
        last_transaction_price: Price of last transaction
        rebalance_size: Rebalance threshold as decimal (e.g., 0.0905 for 9.05%)
        profit_sharing: Profit sharing ratio as decimal (e.g., 0.5 for 50%)

    Returns:
        Dict with keys: next_buy_price, next_buy_qty, next_sell_price, next_sell_qty
    """
    # Buy at r% below last price
    next_buy_price: float = last_transaction_price / (1 + rebalance_size)
    # Buy quantity: r * H * s, rounded to nearest integer
    next_buy_qty: int = int(rebalance_size * holdings * profit_sharing + 0.5)

    # Sell at r% above last price
    next_sell_price: float = last_transaction_price * (1 + rebalance_size)
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


@dataclass
class Transaction:
    """Represents a single buy or sell transaction."""

    action: str  # 'BUY' or 'SELL'
    qty: int  # Number of shares
    notes: str = ""  # Optional explanation or metadata


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
    # Unwrap Series if needed
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


class AlgorithmBase(ABC):
    """Abstract base class for trading algorithms.

    Subclasses must implement three lifecycle hooks:
    - on_new_holdings: Called after initial purchase
    - on_day: Called each trading day, returns Transaction or None
    - on_end_holding: Called at end of backtest period
    """

    def __init__(self, params: Optional[Dict[str, Any]] = None) -> None:
        """Initialize with optional parameters dict."""
        self.params: Dict[str, Any] = params or {}

    @abstractmethod
    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        """Initialize algorithm state after initial purchase.

        Args:
            holdings: Initial share count
            current_price: Price at initial purchase
        """
        pass

    @abstractmethod
    def on_day(
        self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame
    ) -> Optional[Transaction]:
        """Process one trading day, optionally return transaction.

        Args:
            date_: Current date
            price_row: OHLC prices for current day
            holdings: Current share count
            bank: Current cash balance (may be negative)
            history: All price data up to previous day

        Returns:
            Transaction to execute, or None to hold
        """
        pass

    @abstractmethod
    def on_end_holding(self) -> None:
        """Cleanup/reporting after backtest completes."""
        pass


class BuyAndHoldAlgorithm(AlgorithmBase):
    """Passive buy-and-hold strategy: no trades after initial purchase."""

    def __init__(
        self,
        rebalance_size_pct: float = 0.0,
        profit_sharing_pct: float = 0.0,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize (params ignored for compatibility)."""
        super().__init__(params)

    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        """No-op: no initialization needed."""
        pass

    def on_day(
        self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame
    ) -> Optional[Transaction]:
        """Always returns None: hold position."""
        return None

    def on_end_holding(self) -> None:
        """No-op: no cleanup needed."""
        pass


class SyntheticDividendAlgorithm(AlgorithmBase):
    """Volatility harvesting algorithm that generates synthetic dividends.

    Operates in two modes:
    1. Full (buyback_enabled=True): Buy on dips, sell on rises
    2. ATH-only (buyback_enabled=False): Only sell at new all-time highs

    Parameters:
        rebalance_size_pct: Rebalance threshold (e.g. 9.15 for 9.15%)
        profit_sharing_pct: Portion of rebalance to trade (e.g. 50 for 50%)
        buyback_enabled: True for full algorithm, False for ATH-only

    Examples:
        Full: SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=True)
        ATH-only: SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=False)
    """

    def __init__(
        self,
        rebalance_size_pct: float = 0.0,
        profit_sharing_pct: float = 0.0,
        buyback_enabled: bool = True,
        params: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize algorithm with strategy parameters."""
        super().__init__(params)

        # Convert percentages to decimals
        self.rebalance_size: float = float(rebalance_size_pct) / 100.0
        self.profit_sharing: float = float(profit_sharing_pct) / 100.0
        self.buyback_enabled: bool = buyback_enabled

        # Cumulative alpha from volatility harvesting (full mode only)
        self.total_volatility_alpha: float = 0.0

        # All-time high tracker (ATH-only mode)
        self.ath_price: float = 0.0

        # Buyback stack for FIFO unwinding (full mode only)
        # Each entry: (purchase_price, quantity) for exact lot tracking
        self.buyback_stack: List[Tuple[float, int]] = []

        # State for pending orders
        self.last_transaction_price: float
        self.next_buy_price: float
        self.next_buy_qty: int
        self.next_sell_price: float
        self.next_sell_qty: int

    def place_orders(self, holdings: int, current_price: float) -> None:
        """Calculate and set next buy/sell orders based on current state.

        Updates instance variables with new order prices and quantities.
        """
        # Anchor next orders to this transaction price
        self.last_transaction_price = current_price

        # Calculate symmetric buy/sell orders
        orders = calculate_synthetic_dividend_orders(
            holdings=holdings,
            last_transaction_price=current_price,
            rebalance_size=self.rebalance_size,
            profit_sharing=self.profit_sharing,
        )

        # Update order state
        self.next_buy_price = orders["next_buy_price"]
        self.next_buy_qty = int(orders["next_buy_qty"])
        self.next_sell_price = orders["next_sell_price"]
        self.next_sell_qty = int(orders["next_sell_qty"])

        # Debug output
        if self.buyback_enabled:
            print(f"Placing orders for last transaction price: ${self.last_transaction_price}")
            print(
                f"  Next BUY: {self.next_buy_qty} @ ${self.next_buy_price:.2f} = ${self.next_buy_price * self.next_buy_qty:.2f}"
            )
            print(
                f"  Next SELL: {self.next_sell_qty} @ ${self.next_sell_price:.2f} = ${self.next_sell_price * self.next_sell_qty:.2f}"
            )
        else:
            print(f"ATH-only: New ATH at ${current_price:.2f}, placing sell order:")
            print(
                f"  Next SELL: {self.next_sell_qty} @ ${self.next_sell_price:.2f} = ${self.next_sell_price * self.next_sell_qty:.2f}"
            )

    def on_new_holdings(self, holdings: int, current_price: float) -> None:
        """Initialize algorithm state after initial purchase."""
        # ATH-only mode: seed with initial price as baseline
        if not self.buyback_enabled:
            self.ath_price = current_price

        # Calculate first set of orders
        self.place_orders(holdings, current_price)

    def on_day(
        self, date_: date, price_row: pd.Series, holdings: int, bank: float, history: pd.DataFrame
    ) -> Optional[Transaction]:
        """Evaluate day's price action and conditionally trigger buy/sell.

        Logic:
        - ATH-only mode: Sell only at new all-time highs
        - Full mode: Buy on dips (price ≤ buy_price), sell on rises (price ≥ sell_price)
        - Orders placed as limit orders; actual price may differ due to gaps
        """
        try:
            # Extract OHLC prices as scalars
            open_price: Optional[float] = _get_price_scalar_from_row(price_row, "Open")
            high: Optional[float] = _get_price_scalar_from_row(price_row, "High")
            low: Optional[float] = _get_price_scalar_from_row(price_row, "Low")
            # close: Optional[float] = _get_price_scalar_from_row(price_row, "Close")  # Unused

            # Require high/low to evaluate orders
            if low is None or high is None:
                return None

            # Debug output (disabled by default)
            if False:
                low_s = f"{low:.2f}"
                high_s = f"{high:.2f}"
                print(f"Evaluating orders on {date_.isoformat()}: Low=${low_s}, High=${high_s}")

            # ATH-only mode: only sell at new peaks
            if not self.buyback_enabled:
                if high > self.ath_price:
                    # Record new ATH
                    self.ath_price = high

                    # Execute sell if threshold reached
                    if high >= self.next_sell_price:
                        # Use open if market gapped up, else use limit price
                        actual_price = (
                            max(self.next_sell_price, open_price)
                            if open_price is not None
                            else self.next_sell_price
                        )
                        notes = f"ATH-only sell: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f}, new ATH = {self.ath_price:.2f}"
                        transaction = Transaction(
                            action="SELL", qty=self.next_sell_qty, notes=notes
                        )

                        # Update orders with reduced holdings
                        updated_holdings = holdings - self.next_sell_qty
                        self.place_orders(updated_holdings, self.next_sell_price)

                        return transaction
                return None

            # Full mode: check both buy (on dip) and sell (on rise)

            # Buy trigger: price dropped to or below buy threshold
            if low <= self.next_buy_price:
                # Fill at open if market gapped down, else at limit price
                actual_price = (
                    min(self.next_buy_price, open_price)
                    if open_price is not None
                    else self.next_buy_price
                )

                # Push buyback to stack for FIFO unwinding
                self.buyback_stack.append((actual_price, self.next_buy_qty))

                # Calculate alpha: profit from buying back cheaper shares
                # Note: Alpha will be realized when we unwind this lot during SELL
                current_value = holdings * actual_price
                profit = (self.last_transaction_price - actual_price) * self.next_buy_qty
                alpha = (profit / current_value) * 100 if current_value != 0 else 0.0
                self.total_volatility_alpha += alpha

                notes = f"Buying back: limit price = {self.next_buy_price:.2f}, actual price = {actual_price:.2f}"
                transaction = Transaction(action="BUY", qty=self.next_buy_qty, notes=notes)

                # Recompute orders with increased holdings
                updated_holdings = holdings + self.next_buy_qty
                self.place_orders(updated_holdings, self.next_buy_price)

                return transaction

            # Sell trigger: price rose to or above sell threshold
            if high >= self.next_sell_price:
                # Fill at open if market gapped up, else at limit price
                actual_price = (
                    max(self.next_sell_price, open_price)
                    if open_price is not None
                    else self.next_sell_price
                )

                # Unwind buyback stack FIFO before selling initial shares
                sell_qty_remaining = self.next_sell_qty
                unwound_from_stack = 0

                while sell_qty_remaining > 0 and self.buyback_stack:
                    buy_price, buy_qty = self.buyback_stack[0]
                    to_unwind = min(sell_qty_remaining, buy_qty)

                    # This lot is now fully or partially unwound
                    if to_unwind == buy_qty:
                        # Fully unwound - remove from stack
                        self.buyback_stack.pop(0)
                    else:
                        # Partially unwound - update remaining quantity
                        self.buyback_stack[0] = (buy_price, buy_qty - to_unwind)

                    unwound_from_stack += to_unwind
                    sell_qty_remaining -= to_unwind

                # Note about what we unwound
                if unwound_from_stack > 0:
                    notes = f"Taking profits: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f} (unwound {unwound_from_stack} from buyback stack)"
                else:
                    notes = f"Taking profits: limit price = {self.next_sell_price:.2f}, actual price = {actual_price:.2f}"

                transaction = Transaction(action="SELL", qty=self.next_sell_qty, notes=notes)

                # Recompute orders with reduced holdings
                updated_holdings = holdings - self.next_sell_qty
                self.place_orders(updated_holdings, self.next_sell_price)

                return transaction

        except Exception:
            # Silently ignore errors (e.g., missing price data)
            pass
        return None

    def on_end_holding(self) -> None:
        """Print summary statistics after backtest completes."""
        if self.buyback_enabled:
            print(
                f"Synthetic Dividend Algorithm total volatility alpha: {self.total_volatility_alpha:.2f}%"
            )
            # Show buyback stack status
            if self.buyback_stack:
                total_stack_qty = sum(qty for _, qty in self.buyback_stack)
                print(
                    f"  Buyback stack: {len(self.buyback_stack)} lots with {total_stack_qty} total shares not yet unwound"
                )
            else:
                print("  Buyback stack: empty (all lots unwound)")
        else:
            print(f"ATH-only algorithm: final ATH = ${self.ath_price:.2f}")


def build_algo_from_name(name: str) -> AlgorithmBase:
    """Factory: parse string identifier into algorithm instance.

    Supported formats (priority order):
        'sdN' → N-th root of 2 (exponential scaling), 50% profit sharing default
        'sdN,P' → N-th root of 2, P% profit sharing
        'buy-and-hold' → BuyAndHoldAlgorithm()
        'sd-9.15,50' → SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=True)
        'sd-ath-only-9.15,50' → SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=False)

    Examples (exponential scaling - Nth root of 2):
        'sd8' → 2^(1/8) - 1 = 9.05% rebalance trigger, 50% profit sharing
        'sd8,75' → 2^(1/8) - 1 = 9.05% rebalance trigger, 75% profit sharing
        'sd4' → 2^(1/4) - 1 = 18.92% rebalance trigger, 50% profit sharing
        'sd12' → 2^(1/12) - 1 = 5.95% rebalance trigger, 50% profit sharing
        'sd16' → 2^(1/16) - 1 = 4.43% rebalance trigger, 50% profit sharing

    Rationale: N equal geometric steps to doubling ensures uniform proportional gains
    between rebalances, adapting naturally to asset volatility.

    Legacy formats (backward compatibility):
        'sd/9.15%/50%' → same as 'sd-9.15,50'
        'sd-ath-only/9.15%/50%' → same as 'sd-ath-only-9.15,50'
        'synthetic-dividend/...' → same as 'sd-...'
    """
    name = name.strip()
    print(f"Building algorithm from name: {name}")

    # Buy-and-hold baseline
    if name == "buy-and-hold":
        return BuyAndHoldAlgorithm()

    # Exponential scaling: sdN or sdN,P
    # N = Nth root of 2 (N equal geometric steps to doubling)
    # P = profit sharing % (optional, defaults to 50)
    m = re.match(r"^sd(\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?))?$", name)
    if m:
        n = float(m.group(1))
        profit = float(m.group(2)) if m.group(2) else 50.0
        # Calculate rebalance trigger: Nth root of 2, minus 1, as percentage
        rebalance = (pow(2.0, 1.0 / n) - 1.0) * 100.0
        print(f"  Exponential scaling: 2^(1/{n}) - 1 = {rebalance:.4f}% trigger")
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=True
        )

    # ATH-only variant: modern comma-based format
    m = re.match(r"^(sd|synthetic-dividend)-ath-only-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=False
        )

    # Full algorithm: modern comma-based format
    m = re.match(r"^(sd|synthetic-dividend)-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=True
        )

    # Legacy: ATH-only variant with slash/percent format
    m = re.match(r"^(sd|synthetic-dividend)-ath-only/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=False
        )

    # Legacy: Full algorithm with slash/percent format
    m = re.match(r"^(sd|synthetic-dividend)/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=True
        )

    raise ValueError(f"Unrecognized strategy name: {name}")


def run_algorithm_backtest(
    df: pd.DataFrame,
    ticker: str,
    initial_qty: int,
    start_date: date,
    end_date: date,
    algo: Optional[Union[AlgorithmBase, Callable]] = None,
    algo_params: Optional[Dict[str, Any]] = None,
    reference_return_pct: float = 0.0,
    risk_free_rate_pct: float = 0.0,
    reference_asset_df: Optional[pd.DataFrame] = None,
    risk_free_asset_df: Optional[pd.DataFrame] = None,
    reference_asset_ticker: str = "",
    risk_free_asset_ticker: str = "",
) -> Tuple[List[str], Dict[str, Any]]:
    """Execute backtest of trading algorithm against historical price data.

    Flow:
    1. Initial BUY of initial_qty shares on first trading day ≥ start_date
    2. Each day: call algo.on_day() which may return Transaction or None
    3. SELL: increases bank, decreases holdings (capped at current holdings)
    4. BUY: decreases bank (may go negative), increases holdings
    5. Compute final portfolio value and returns vs buy-and-hold baseline
    6. Calculate opportunity cost (negative bank) and risk-free gains (positive bank)

    Args:
        df: Historical OHLC price data (indexed by date)
        ticker: Stock symbol for reporting
        initial_qty: Number of shares to purchase initially
        start_date: Backtest start date (inclusive)
        end_date: Backtest end date (inclusive)
        algo: Algorithm instance or callable (defaults to buy-and-hold)
        algo_params: Optional parameters dict (for callable algos)
        reference_return_pct: Annual return for opportunity cost calc (fallback if no asset data)
                             Applied when bank balance is negative (borrowing cost)
        risk_free_rate_pct: Annual return on cash (fallback if no asset data)
                           Applied when bank balance is positive (interest earned)
        reference_asset_df: Historical price data for reference asset (e.g., VOO)
                           If provided, uses actual daily returns instead of fixed rate
        risk_free_asset_df: Historical price data for risk-free asset (e.g., BIL)
                           If provided, uses actual daily returns instead of fixed rate
        reference_asset_ticker: Ticker symbol for reference asset (for reporting)
        risk_free_asset_ticker: Ticker symbol for risk-free asset (for reporting)

    Returns:
        Tuple of (transaction_strings, summary_dict)
        - transaction_strings: List of human-readable transaction logs
        - summary_dict: Metrics including returns, holdings, bank, baseline comparison,
                       opportunity cost, and risk-free gains
    """
    if df is None or df.empty:
        raise ValueError("Empty price data")

    # Normalize index to date objects for consistent lookup
    df_indexed = df.copy()
    df_indexed.index = pd.to_datetime(df_indexed.index).date

    # Find first and last trading days within requested range
    try:
        first_idx = min(d for d in df_indexed.index if d >= start_date)
        last_idx = max(d for d in df_indexed.index if d <= end_date)
    except ValueError:
        raise ValueError("No overlapping trading days in requested date range.")

    # Prepare reference asset daily returns (for opportunity cost)
    reference_returns: Dict[date, float] = {}
    if reference_asset_df is not None and not reference_asset_df.empty:
        ref_indexed = reference_asset_df.copy()
        ref_indexed.index = pd.to_datetime(ref_indexed.index).date
        if "Close" in ref_indexed.columns:
            # Calculate daily returns: (today - yesterday) / yesterday
            close_prices = ref_indexed["Close"].values  # Extract as numpy array
            dates = ref_indexed.index.tolist()
            for i in range(1, len(close_prices)):
                prev_price = float(close_prices[i - 1])
                curr_price = float(close_prices[i])
                if prev_price > 0:
                    reference_returns[dates[i]] = (curr_price - prev_price) / prev_price

    # Prepare risk-free asset daily returns (for cash interest)
    risk_free_returns: Dict[date, float] = {}
    if risk_free_asset_df is not None and not risk_free_asset_df.empty:
        rf_indexed = risk_free_asset_df.copy()
        rf_indexed.index = pd.to_datetime(rf_indexed.index).date
        if "Close" in rf_indexed.columns:
            # Calculate daily returns: (today - yesterday) / yesterday
            close_prices = rf_indexed["Close"].values  # Extract as numpy array
            dates = rf_indexed.index.tolist()
            for i in range(1, len(close_prices)):
                prev_price = float(close_prices[i - 1])
                curr_price = float(close_prices[i])
                if prev_price > 0:
                    risk_free_returns[dates[i]] = (curr_price - prev_price) / prev_price

    # Fallback daily rates (if asset data not available)
    daily_reference_rate_fallback = (1 + reference_return_pct / 100.0) ** (1.0 / 365.25) - 1.0
    daily_risk_free_rate_fallback = (1 + risk_free_rate_pct / 100.0) ** (1.0 / 365.25) - 1.0

    # Extract start/end prices for return calculations
    start_price: float = _get_close_scalar(df_indexed, first_idx, "Close")
    end_price: float = _get_close_scalar(df_indexed, last_idx, "Close")

    transactions: List[str] = []

    # Initialize portfolio state
    holdings: int = int(initial_qty)
    bank: float = 0.0  # Cash balance (may go negative)

    # Bank balance tracking for statistics (list of (date, balance) tuples)
    bank_history: List[Tuple[date, float]] = [(first_idx, 0.0)]
    bank_min: float = 0.0
    bank_max: float = 0.0

    # Record initial purchase
    start_value = holdings * start_price
    transactions.append(
        f"{first_idx.isoformat()} BUY {holdings} {ticker} @ {start_price:.2f} = {start_value:.2f}"
    )

    # Prepare sorted list of all trading days in range
    dates = sorted(d for d in df_indexed.index if d >= first_idx and d <= last_idx)

    # Normalize algo to AlgorithmBase interface
    if algo is None:
        algo_obj: AlgorithmBase = BuyAndHoldAlgorithm()
    elif isinstance(algo, AlgorithmBase):
        algo_obj = algo
    elif callable(algo):
        # Wrap legacy callable in adapter
        class _FuncAdapter(AlgorithmBase):
            def __init__(self, fn: Callable) -> None:
                super().__init__()
                self.fn = fn

            def on_new_holdings(self, holdings: int, current_price: float) -> None:
                pass

            def on_day(
                self,
                date_: date,
                price_row: pd.Series,
                holdings: int,
                bank: float,
                history: pd.DataFrame,
            ) -> Optional[Transaction]:
                result = self.fn(date_, price_row, holdings, bank, history, algo_params)
                return result  # type: ignore[no-any-return]

            def on_end_holding(self) -> None:
                pass

        algo_obj = _FuncAdapter(algo)
    else:
        raise ValueError("algo must be AlgorithmBase instance or callable")

    # Initialize algorithm with starting position
    algo_obj.on_new_holdings(holdings, start_price)

    # Main backtest loop: process each trading day
    for i, d in enumerate(dates):
        # Skip initial purchase day (already processed above)
        if d == first_idx:
            continue

        # Get current day's prices
        price_row = df_indexed.loc[d]
        price: float = _get_close_scalar(df_indexed, d, "Close")

        # History includes all data up to previous day
        history = df_indexed.loc[: dates[i - 1]] if i > 0 else df_indexed.loc[:d]

        # Let algorithm evaluate the day
        try:
            tx: Optional[Transaction] = algo_obj.on_day(d, price_row, holdings, bank, history)
        except Exception as e:
            raise RuntimeError(f"Algorithm raised an error on {d}: {e}")

        # No transaction requested
        if tx is None:
            continue

        # Validate transaction type
        if not isinstance(tx, Transaction):
            raise ValueError("Algorithm must return a Transaction or None")

        # Execute SELL transaction
        if tx.action.upper() == "SELL":
            sell_qty = min(int(tx.qty), holdings)  # Cap at available holdings
            proceeds = sell_qty * price
            holdings -= sell_qty
            bank += proceeds
            transactions.append(
                f"{d.isoformat()} SELL {sell_qty} {ticker} @ {price:.2f} = {proceeds:.2f}, "
                f"holdings = {holdings}, bank = {bank:.2f}  # {tx.notes}"
            )
            # Track bank balance statistics
            bank_history.append((d, bank))
            bank_min = min(bank_min, bank)
            bank_max = max(bank_max, bank)

        # Execute BUY transaction
        elif tx.action.upper() == "BUY":
            buy_qty = int(tx.qty)
            cost = buy_qty * price
            holdings += buy_qty
            bank -= cost  # May go negative (margin)
            transactions.append(
                f"{d.isoformat()} BUY {buy_qty} {ticker} @ {price:.2f} = {cost:.2f}, "
                f"holdings = {holdings}, bank = {bank:.2f}  # {tx.notes}"
            )
            # Track bank balance statistics
            bank_history.append((d, bank))
            bank_min = min(bank_min, bank)
            bank_max = max(bank_max, bank)

        else:
            raise ValueError("Transaction action must be 'BUY' or 'SELL'")

    # Calculate final portfolio metrics
    final_price = end_price
    end_value = holdings * final_price  # Market value of remaining shares
    total = bank + end_value  # Total portfolio value

    # Time-based calculations
    days = (last_idx - first_idx).days
    years = days / 365.25 if days > 0 else 0.0
    start_val = initial_qty * start_price

    # Returns calculation
    total_return = (total - start_val) / start_val if start_val != 0 else 0.0
    if years > 0 and start_val > 0:
        annualized = (total / start_val) ** (1.0 / years) - 1.0
    else:
        annualized = 0.0

    # Calculate bank balance statistics
    bank_balances = [b for d, b in bank_history]
    bank_avg: float = sum(bank_balances) / len(bank_balances) if bank_balances else 0.0
    bank_negative_count = sum(1 for b in bank_balances if b < 0)
    bank_positive_count = sum(1 for b in bank_balances if b > 0)

    # Calculate opportunity cost and risk-free gains using actual asset returns
    opportunity_cost_total = 0.0
    risk_free_gains_total = 0.0

    for d, bank_balance in bank_history:
        if bank_balance < 0:
            # Negative balance: opportunity cost of borrowed money
            # Use actual reference asset return for this day, or fallback to fixed rate
            daily_return = reference_returns.get(d, daily_reference_rate_fallback)
            opportunity_cost_total += abs(bank_balance) * daily_return
        elif bank_balance > 0:
            # Positive balance: risk-free interest earned on cash
            # Use actual risk-free asset return for this day, or fallback to fixed rate
            daily_return = risk_free_returns.get(d, daily_risk_free_rate_fallback)
            risk_free_gains_total += bank_balance * daily_return

    # Build summary dict
    summary: Dict[str, Any] = {
        "ticker": ticker,
        "start_date": first_idx,
        "start_price": start_price,
        "start_value": start_val,
        "end_date": last_idx,
        "end_price": final_price,
        "end_value": end_value,
        "holdings": holdings,
        "bank": bank,
        "bank_min": bank_min,
        "bank_max": bank_max,
        "bank_avg": bank_avg,
        "bank_negative_count": bank_negative_count,
        "bank_positive_count": bank_positive_count,
        "opportunity_cost": opportunity_cost_total,
        "risk_free_gains": risk_free_gains_total,
        "total": total,
        "total_return": total_return,
        "annualized": annualized,
        "years": years,
    }

    # Compute buy-and-hold baseline for alpha comparison
    try:
        # Baseline: hold initial_qty shares, no trading
        baseline_end_value = initial_qty * final_price
        baseline_total = baseline_end_value  # No cash, just shares
        baseline_total_return = (baseline_total - start_val) / start_val if start_val != 0 else 0.0

        if years > 0 and start_val > 0:
            baseline_annualized = (baseline_total / start_val) ** (1.0 / years) - 1.0
        else:
            baseline_annualized = 0.0

        baseline_summary: Dict[str, Any] = {
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

        # Alpha = algorithm return - baseline return
        volatility_alpha = total_return - baseline_total_return

        summary["baseline"] = baseline_summary
        summary["volatility_alpha"] = volatility_alpha
    except Exception:
        # Gracefully handle edge cases in baseline computation
        summary["baseline"] = None
        summary["volatility_alpha"] = None

    # Notify algorithm of completion
    algo_obj.on_end_holding()

    return transactions, summary
