"""Backtest engine for algorithmic trading strategies.

Provides abstract base for strategy implementations and execution framework
for backtesting against historical OHLC price data.
"""

import math
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import pandas as pd

# Import algorithm classes from dedicated package
from src.algorithms import (
    AlgorithmBase,
    BuyAndHoldAlgorithm,
    PortfolioAlgorithmBase,
    SyntheticDividendAlgorithm,
)
from src.models.backtest_utils import (  # noqa: F401; (re-exported for backwards compatibility)
    calculate_synthetic_dividend_orders,
)

# Import common types
from src.models.model_types import Transaction

# Import utility functions


# Type aliases for clean abstraction
Data = pd.DataFrame  # Pure data concept with no implementation baggage


def calculate_time_weighted_average_holdings(
    holdings_history: List[Tuple[date, int]], period_start: date, period_end: date
) -> float:
    """Calculate time-weighted average holdings over a period.

    This computes the IRS-approved average holdings by integrating daily holdings
    over the time period, weighted by the number of days at each holding level.

    Formula: ∑(holdings_i × days_i) / total_days

    Args:
        holdings_history: List of (date, holdings) tuples sorted by date
        period_start: Start of accrual period (inclusive)
        period_end: End of accrual period (inclusive, typically ex-dividend date)

    Returns:
        Time-weighted average holdings as float (can be fractional)

    Example:
        Holdings: 100 shares for 60 days, then 150 shares for 30 days
        Average: (100×60 + 150×30) / 90 = 116.67 shares
    """
    if not holdings_history:
        return 0.0

    # Filter to holdings changes within or before the period
    relevant_history = [(d, h) for d, h in holdings_history if d <= period_end]
    if not relevant_history:
        return 0.0

    total_share_days = 0.0
    total_days = (period_end - period_start).days + 1  # Inclusive

    # Process each holdings level
    for i, (change_date, holdings) in enumerate(relevant_history):
        # Determine when this holdings level starts
        level_start = max(change_date, period_start)

        # Determine when this holdings level ends
        if i + 1 < len(relevant_history):
            next_change_date = relevant_history[i + 1][0]
            level_end = min(next_change_date - pd.Timedelta(days=1).to_pytimedelta(), period_end)
        else:
            level_end = period_end

        # Skip if this level doesn't overlap with our period
        if level_start > period_end or level_end < period_start:
            continue

        # Calculate days at this level
        days_at_level = (level_end - level_start).days + 1
        if days_at_level > 0:
            total_share_days += holdings * days_at_level

    return total_share_days / total_days if total_days > 0 else 0.0


def run_algorithm_backtest(
    df: pd.DataFrame,
    ticker: str,
    initial_qty: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    algo: Optional[Union[AlgorithmBase, Callable]] = None,
    algo_params: Optional[Dict[str, Any]] = None,
    reference_return_pct: float = 0.0,
    risk_free_rate_pct: float = 0.0,
    reference_data: Optional[pd.DataFrame] = None,
    risk_free_data: Optional[pd.DataFrame] = None,
    # Backward-compat legacy params (alias of *_data)
    reference_asset_df: Optional[pd.DataFrame] = None,
    risk_free_asset_df: Optional[pd.DataFrame] = None,
    reference_asset_ticker: str = "",
    risk_free_asset_ticker: str = "",
    # Dividend/interest payments
    dividend_series: Optional[pd.Series] = None,
    # Withdrawal policy parameters
    withdrawal_rate_pct: float = 0.0,
    withdrawal_frequency_days: int = 30,
    cpi_data: Optional[pd.DataFrame] = None,
    simple_mode: bool = False,
    # Price normalization
    normalize_prices: bool = False,
    # Bank behavior
    allow_margin: bool = True,
    # Investment amount (alternative to initial_qty)
    initial_investment: Optional[float] = None,
    **kwargs: Any,
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """Execute backtest of trading algorithm against historical price data.

    Flow:
    1. Initial BUY of initial_qty shares on first trading day ≥ start_date
    2. Each day: call algo.on_day() which may return Transaction or None
    3. SELL: increases bank, decreases holdings (capped at current holdings)
    4. BUY: decreases bank (may go negative), increases holdings
    5. Process withdrawals (if configured) - withdraw from bank or sell shares if needed
    6. Compute final portfolio value and returns vs buy-and-hold baseline
    7. Calculate opportunity cost (negative bank) and risk-free gains (positive bank)

    Args:
        df: Historical OHLC price data (indexed by date)
        ticker: Stock symbol for reporting
        initial_qty: Number of shares to purchase initially (optional)
                    Either initial_qty OR initial_investment must be provided
        start_date: Backtest start date (inclusive, optional - defaults to first date)
        end_date: Backtest end date (inclusive, optional - defaults to last date)
        algo: Algorithm instance or callable (defaults to buy-and-hold)
        algo_params: Optional parameters dict (for callable algos)
        reference_return_pct: Annual return for opportunity cost calc (fallback if no asset data)
                             Applied when bank balance is negative (borrowing cost)
                             Ignored if simple_mode=True
        risk_free_rate_pct: Annual return on cash (fallback if no asset data)
                           Applied when bank balance is positive (interest earned)
                           Ignored if simple_mode=True
        reference_data: Historical price data for reference asset (e.g., VOO)
                           If provided, uses actual daily returns instead of fixed rate
                           Ignored if simple_mode=True
        risk_free_data: Historical price data for risk-free asset (e.g., BIL)
                           If provided, uses actual daily returns instead of fixed rate
                           Ignored if simple_mode=True
        reference_asset_ticker: Ticker symbol for reference asset (for reporting)
        risk_free_asset_ticker: Ticker symbol for risk-free asset (for reporting)
        dividend_series: Historical dividend/interest payments (Series indexed by ex-date)
                        Each value is dividend amount per share on that date
                        Works for equity dividends (AAPL) and ETF distributions (BIL)
                        If provided, dividends are credited to bank on ex-date
                        If None, no dividend income is tracked
        withdrawal_rate_pct: Annual withdrawal rate as % of initial portfolio value
                            (e.g., 4.0 for 4% withdrawal rate)
                            Withdrawals are taken monthly and CPI-adjusted
        withdrawal_frequency_days: Days between withdrawals (default 30 for monthly)
        cpi_data: Historical CPI data for inflation adjustment
                          If provided, withdrawals adjust with inflation
                          If None, withdrawals remain constant in nominal terms
        simple_mode: If True, disables opportunity cost, risk-free gains, and CPI adjustment
                    Useful for unit tests where we want clean, simple behavior
                    (free borrowing, cash holds value, no inflation)
        normalize_prices: If True, normalize all prices so brackets are at standard positions
                         relative to 1.0 based on rebalance_trigger.
                         This makes bracket placement deterministic across different backtests.
                         For sd8 (9.05% trigger): brackets at 1.0, 1.0905, 1.1893, 1.2968, ...
                         The first price is scaled so it lands on a standard bracket.
        allow_margin: If True (default), bank can go negative (borrowing from yourself)
                     BUY transactions always execute, withdrawals cover amount only.
                     If False (strict mode), bank never goes negative (closed system)
                     BUY transactions skipped if insufficient cash,
                     withdrawals must cover both amount AND repay any deficit.
        initial_investment: Dollar amount to invest (optional, preferred method)
                           If provided, calculates initial_qty based on start price
                           Default: $1,000,000 (psychologically meaningful amount)
                           Either initial_qty OR initial_investment must be provided
                           If both provided, initial_qty takes precedence

    Returns:
        Tuple of (transaction_strings, summary_dict)
        - transaction_strings: List of human-readable transaction logs
        - summary_dict: Metrics including:
            * Primary: total_return, annualized, volatility_alpha
            * Holdings: holdings, bank, end_value, total
            * Bank stats: bank_min, bank_max, bank_avg, negative/positive counts
            * Costs/Gains: opportunity_cost, risk_free_gains
            * Withdrawals: total_withdrawn, withdrawal_count, shares_sold_for_withdrawals
            * Deployment (supplementary): capital_utilization, return_on_deployed_capital,
              deployment_min/max, avg_deployed_capital
            * Baseline: buy-and-hold comparison data
    """
    # Backwards-compatible aliases: accept older kwarg names used in tests/older code
    # (e.g., reference_asset_df -> reference_data, risk_free_asset_df -> risk_free_data)
    if "reference_asset_df" in kwargs and reference_data is None:
        reference_data = kwargs.pop("reference_asset_df")
    if "risk_free_asset_df" in kwargs and risk_free_data is None:
        risk_free_data = kwargs.pop("risk_free_asset_df")
    # Check for any remaining unexpected kwargs
    if kwargs:
        # List all parameters that can be passed to this function, including
        # backwards-compatible aliases (even though they're consumed above)
        valid_params = [
            "df",
            "ticker",
            "initial_qty",
            "start_date",
            "end_date",
            "algo",
            "algo_params",
            "reference_return_pct",
            "risk_free_rate_pct",
            "reference_data",
            "risk_free_data",
            "reference_asset_ticker",
            "risk_free_asset_ticker",
            "dividend_series",
            "withdrawal_rate_pct",
            "withdrawal_frequency_days",
            "cpi_data",
            "simple_mode",
            "normalize_prices",
            "allow_margin",
            "initial_investment",
            "reference_asset_df",
            "risk_free_asset_df",  # Backwards-compatible aliases
        ]
        raise TypeError(
            "run_algorithm_backtest() got unexpected keyword argument(s): "
            f"{', '.join(repr(k) for k in kwargs.keys())}. "
            f"Valid parameters are: {', '.join(valid_params)}"
        )

    if df is None or df.empty:
        raise ValueError("Empty price data")

    # Backward compatibility: map legacy args if provided
    if reference_data is None and reference_asset_df is not None:
        reference_data = reference_asset_df
    if risk_free_data is None and risk_free_asset_df is not None:
        risk_free_data = risk_free_asset_df

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
    if reference_data is not None and not reference_data.empty:
        ref_indexed = reference_data.copy()
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
    if risk_free_data is not None and not risk_free_data.empty:
        rf_indexed = risk_free_data.copy()
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

    # Fallback daily rates (if asset data not available or simple_mode)
    if simple_mode:
        daily_reference_rate_fallback = 0.0
        daily_risk_free_rate_fallback = 0.0
    else:
        daily_reference_rate_fallback = (1 + reference_return_pct / 100.0) ** (1.0 / 365.25) - 1.0
        daily_risk_free_rate_fallback = (1 + risk_free_rate_pct / 100.0) ** (1.0 / 365.25) - 1.0

    # Extract start/end prices for return calculations
    start_price: float = df_indexed.loc[first_idx, "Close"].item()
    end_price: float = df_indexed.loc[last_idx, "Close"].item()

    # Calculate initial quantity from investment amount or shares
    # Prefer initial_qty if both are provided, otherwise use initial_investment
    calculated_qty: int
    investment_method: str

    if initial_qty is not None:
        # Explicit share count provided
        calculated_qty = int(initial_qty)
        investment_method = "shares"
        investment_amount = calculated_qty * start_price
    elif initial_investment is not None:
        # Dollar amount provided - calculate shares
        calculated_qty = int(initial_investment / start_price)
        investment_method = "investment"
        investment_amount = initial_investment
    else:
        # Default to $1,000,000 investment (psychologically meaningful)
        default_investment = 1_000_000.0
        calculated_qty = int(default_investment / start_price)
        investment_method = "default_investment"
        investment_amount = default_investment

    # Display initial purchase info
    actual_invested = calculated_qty * start_price
    print(
        f"Initial purchase: {calculated_qty} shares × ${start_price:.2f} = ${actual_invested:,.2f}"
    )
    if investment_method in ("investment", "default_investment"):
        if investment_method == "default_investment":
            print(f"  (using default investment amount: ${investment_amount:,.2f})")
        else:
            print(f"  (target investment: ${investment_amount:,.2f})")
        if abs(actual_invested - investment_amount) > 0.01:
            print(
                f"  (difference due to whole shares: ${actual_invested - investment_amount:+,.2f})"
            )

    # Price normalization (if enabled)
    # Normalize so that brackets are at standard positions relative to 1.0
    # For example, with sd8 (9.05% trigger), brackets at: 1.0, 1.0905, 1.1893, 1.2968, ...
    price_scale_factor: float = 1.0
    if normalize_prices:
        # Get rebalance trigger from algorithm
        rebalance_trigger = 0.0
        if algo is not None:
            if isinstance(algo, SyntheticDividendAlgorithm):
                rebalance_trigger = algo.rebalance_size  # Already in decimal form
            elif hasattr(algo, "rebalance_size"):
                rebalance_trigger = algo.rebalance_size

        if rebalance_trigger > 0:
            # Find which bracket the start_price should be on
            # Brackets are at: 1.0 * (1 + r)^n for integer n
            # We want: start_price * scale = 1.0 * (1 + r)^n for some integer n
            # So: n = log(start_price * scale) / log(1 + r)
            # We want n to be an integer, so find closest integer bracket

            # Start by assuming scale=1, find which bracket that gives us
            n_float = math.log(start_price) / math.log(1 + rebalance_trigger)
            n_int = round(n_float)  # Round to nearest integer bracket

            # Now calculate the scale to land exactly on that bracket
            # target_price = 1.0 * (1 + r)^n
            # scale = target_price / start_price
            target_price = math.pow(1 + rebalance_trigger, n_int)
            price_scale_factor = target_price / start_price

            # Scale all prices in the dataframe
            df_indexed = df_indexed.copy()
            for col in ["Open", "High", "Low", "Close"]:
                if col in df_indexed.columns:
                    df_indexed[col] = df_indexed[col] * price_scale_factor

            # Update start/end prices
            start_price = start_price * price_scale_factor
            end_price = end_price * price_scale_factor

            print(f"Price normalization: scaling factor = {price_scale_factor:.6f}")
            print(f"  Original start price: ${start_price / price_scale_factor:.2f}")
            print(f"  Normalized start price: ${start_price:.2f} (bracket n={n_int})")
            print(f"  Rebalance trigger: {rebalance_trigger * 100:.4f}%")
            print(f"  Next bracket up: ${start_price * (1 + rebalance_trigger):.2f}")
            print(f"  Next bracket down: ${start_price / (1 + rebalance_trigger):.2f}")

    transactions: List[Transaction] = []

    # Initialize portfolio state
    holdings: int = calculated_qty
    bank: float = 0.0  # Cash balance (may go negative)

    # Bank balance tracking for statistics (list of (date, balance) tuples)
    bank_history: List[Tuple[date, float]] = [(first_idx, 0.0)]
    bank_min: float = 0.0
    bank_max: float = 0.0

    # Deployed capital tracking for capital utilization metrics
    deployment_history: List[Tuple[date, float]] = []  # (date, deployed_capital)

    # Withdrawal tracking
    total_withdrawn: float = 0.0
    withdrawal_count: int = 0
    shares_sold_for_withdrawals: int = 0
    last_withdrawal_date: Optional[date] = None

    # Dividend/interest income tracking
    total_dividends: float = 0.0
    dividend_payment_count: int = 0

    # Holdings history for time-weighted dividend calculation
    # Each entry: (date, holdings_after_transactions)
    holdings_history: List[Tuple[date, int]] = []

    # Skipped transaction tracking (for strict mode)
    skipped_buys: int = 0
    skipped_buy_value: float = 0.0

    # Opportunity cost and risk-free gains tracking
    opportunity_cost_total: float = 0.0
    risk_free_gains_total: float = 0.0

    # Calculate initial withdrawal amount (if withdrawal policy enabled)
    start_value = holdings * start_price
    if withdrawal_rate_pct > 0:
        # Annual withdrawal based on initial portfolio value
        annual_withdrawal = start_value * (withdrawal_rate_pct / 100.0)
        # Convert to per-period withdrawal
        base_withdrawal_amount = annual_withdrawal * (withdrawal_frequency_days / 365.25)
    else:
        base_withdrawal_amount = 0.0

    # CPI adjustment setup
    cpi_returns: Dict[date, float] = {}
    if cpi_data is not None and not cpi_data.empty and not simple_mode:
        cpi_indexed = cpi_data.copy()
        cpi_indexed.index = pd.to_datetime(cpi_indexed.index).date
        if "Close" in cpi_indexed.columns or "Value" in cpi_indexed.columns:
            value_col = "Value" if "Value" in cpi_indexed.columns else "Close"
            cpi_values = cpi_indexed[value_col].values
            cpi_dates = cpi_indexed.index.tolist()
            # Calculate cumulative CPI adjustment from start
            if len(cpi_values) > 0 and first_idx in cpi_dates:
                start_cpi_idx = cpi_dates.index(first_idx)
                start_cpi = float(cpi_values[start_cpi_idx])
                for i, d in enumerate(cpi_dates):
                    if d >= first_idx:
                        cpi_returns[d] = float(cpi_values[i]) / start_cpi

    # Record initial purchase
    transactions.append(
        Transaction(
            transaction_date=first_idx,
            action="BUY",
            qty=holdings,
            price=start_price,
            ticker=ticker,
            notes="Initial purchase",
        )
    )

    # Record initial holdings for time-weighted calculations
    holdings_history.append((first_idx, holdings))

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
            """Adapter that wraps a callable function as an AlgorithmBase.

            This allows using simple functions as algorithms without implementing
            the full AlgorithmBase interface. Useful for quick prototyping and
            backward compatibility with function-based algorithms.
            """

            def __init__(self, fn: Callable) -> None:
                """Initialize adapter with callable.

                Args:
                    fn: Callable that implements algorithm logic
                """
                super().__init__()
                self.fn = fn

            def on_new_holdings(self, holdings: int, current_price: float) -> None:
                """Initialize algorithm state - no-op for function adapters."""
                pass

            def on_day(
                self,
                date_: date,
                price_row: pd.Series,
                holdings: int,
                bank: float,
                history: pd.DataFrame,
            ) -> List[Transaction]:
                """Execute algorithm by calling wrapped function.

                Args:
                    date_: Current date
                    price_row: OHLC prices for current day
                    holdings: Current share count
                    bank: Current cash balance
                    history: All price data up to previous day

                Returns:
                    List of transactions (converted from function return value)
                """
                result = self.fn(date_, price_row, holdings, bank, history, algo_params)
                return [result] if result is not None else []

            def on_end_holding(self) -> None:
                """Cleanup - no-op for function adapters."""
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
            # Track initial deployment
            deployment_history.append((d, holdings * start_price))
            continue

        # Get current day's prices
        price_row = df_indexed.loc[d]
        price: float = df_indexed.loc[d, "Close"].item()

        # Apply daily gains/costs to bank balance (if not in simple mode)
        if not simple_mode:
            if bank < 0:
                # Negative balance: opportunity cost of borrowed money
                daily_return = reference_returns.get(d, daily_reference_rate_fallback)
                opportunity_cost_today = abs(bank) * daily_return
                bank -= opportunity_cost_today  # Makes bank more negative
                opportunity_cost_total += opportunity_cost_today
            elif bank > 0:
                # Positive balance: risk-free interest earned on cash
                daily_return = risk_free_returns.get(d, daily_risk_free_rate_fallback)
                risk_free_gain_today = bank * daily_return
                bank += risk_free_gain_today  # Adds to cash balance
                risk_free_gains_total += risk_free_gain_today

        # Track deployed capital (market value of holdings) at start of day
        deployed_capital = holdings * price
        deployment_history.append((d, deployed_capital))

        # History includes all data up to previous day
        history = df_indexed.loc[: dates[i - 1]] if i > 0 else df_indexed.loc[:d]

        # Let algorithm evaluate the day (may return multiple transactions for multi-bracket gaps)
        try:
            daily_transactions: List[Transaction] = algo_obj.on_day(
                d, price_row, holdings, bank, history
            )
        except Exception as e:
            raise RuntimeError(f"Algorithm raised an error on {d}: {e}")

        # Process all transactions from this day
        for tx in daily_transactions:
            # Validate transaction type
            if not isinstance(tx, Transaction):
                raise ValueError("Algorithm must return a list of Transactions")

            # Enhance transaction with date, price, and ticker (algorithms don't know these)
            tx.transaction_date = d
            tx.price = price
            tx.ticker = ticker

            # Execute SELL transaction
            if tx.action.upper() == "SELL":
                sell_qty = min(int(tx.qty), holdings)  # Cap at available holdings
                proceeds = sell_qty * price
                holdings -= sell_qty
                bank += proceeds
                transactions.append(
                    Transaction(
                        transaction_date=d,
                        action="SELL",
                        qty=sell_qty,
                        price=price,
                        ticker=ticker,
                        notes=f"{tx.notes}, holdings = {holdings}, bank = {bank:.2f}",
                        limit_price=tx.limit_price,
                    )
                )
                # Record holdings change for time-weighted calculations
                holdings_history.append((d, holdings))
                # Track bank balance statistics
                bank_history.append((d, bank))
                bank_min = min(bank_min, bank)
                bank_max = max(bank_max, bank)

            # Execute BUY transaction
            elif tx.action.upper() == "BUY":
                buy_qty = int(tx.qty)
                cost = buy_qty * price

                # Check if we can afford this buy
                if not allow_margin and bank < cost:
                    # Strict mode: skip buy if insufficient cash
                    skipped_buys += 1
                    skipped_buy_value += cost
                    transactions.append(
                        Transaction(
                            transaction_date=d,
                            action="SKIP BUY",
                            qty=buy_qty,
                            price=price,
                            ticker=ticker,
                            notes=f"{tx.notes}, insufficient cash: ${bank:.2f} < ${cost:.2f}",
                        )
                    )
                else:
                    # Execute buy (allow_margin=True OR sufficient cash)
                    holdings += buy_qty
                    bank -= cost  # May go negative if allow_margin=True
                    transactions.append(
                        Transaction(
                            transaction_date=d,
                            action="BUY",
                            qty=buy_qty,
                            price=price,
                            ticker=ticker,
                            notes=f"{tx.notes}, holdings = {holdings}, bank = {bank:.2f}",
                            limit_price=tx.limit_price,
                        )
                    )
                    # Record holdings change for time-weighted calculations
                    holdings_history.append((d, holdings))
                    # Track bank balance statistics
                    bank_history.append((d, bank))
                    bank_min = min(bank_min, bank)
                    bank_max = max(bank_max, bank)

            else:
                raise ValueError("Transaction action must be 'BUY' or 'SELL'")

        # Process dividend/interest payments (if available for this date)
        if dividend_series is not None and not dividend_series.empty:
            # Check if this date has a dividend payment
            # Convert date index to date objects for comparison
            div_dates = pd.to_datetime(dividend_series.index).date
            if d in div_dates:
                # Find the dividend amount for this date
                div_idx = list(div_dates).index(d)
                div_per_share = dividend_series.iloc[div_idx]

                # Calculate time-weighted average holdings over accrual period
                # Use 90-day lookback (typical for quarterly dividends)
                accrual_period_days = 90
                period_start = d - pd.Timedelta(days=accrual_period_days).to_pytimedelta()
                avg_holdings = calculate_time_weighted_average_holdings(
                    holdings_history, period_start, d
                )

                # Dividend payment based on average holdings during accrual period
                div_payment = div_per_share * avg_holdings

                bank += div_payment
                total_dividends += div_payment
                dividend_payment_count += 1

                transactions.append(
                    Transaction(
                        transaction_date=d,
                        action="DIVIDEND",
                        qty=int(avg_holdings),  # Display average holdings (rounded for display)
                        price=div_per_share,
                        ticker=ticker,
                        notes=f"${div_payment:.2f} (avg {avg_holdings:.2f} shares over 90 days), bank = {bank:.2f}",
                    )
                )

                # Track bank balance statistics
                bank_history.append((d, bank))
                bank_max = max(bank_max, bank)

        # Process withdrawals (if enabled and due)
        if base_withdrawal_amount > 0:
            # Check if withdrawal is due
            days_since_last = None
            if last_withdrawal_date is None:
                # First withdrawal after start date
                days_since_last = (d - first_idx).days
            else:
                days_since_last = (d - last_withdrawal_date).days

            if days_since_last is not None and days_since_last >= withdrawal_frequency_days:
                # Calculate CPI-adjusted withdrawal amount
                cpi_multiplier = cpi_returns.get(d, 1.0)
                withdrawal_amount = base_withdrawal_amount * cpi_multiplier

                # Let algorithm decide how to fulfill withdrawal
                withdrawal_result = algo_obj.on_withdrawal(
                    date_=d,
                    requested_amount=withdrawal_amount,
                    current_price=price,
                    holdings=holdings,
                    bank=bank,
                    allow_margin=allow_margin,
                )

                # Execute share sale if algorithm decided to liquidate
                if withdrawal_result.shares_to_sell > 0:
                    shares_to_sell = withdrawal_result.shares_to_sell
                    proceeds = shares_to_sell * price
                    holdings -= shares_to_sell
                    bank += proceeds
                    shares_sold_for_withdrawals += shares_to_sell

                    transactions.append(
                        Transaction(
                            transaction_date=d,
                            action="SELL",
                            qty=shares_to_sell,
                            price=price,
                            ticker=ticker,
                            notes=f"For withdrawal, {withdrawal_result.notes}, holdings = {holdings}, bank = {bank:.2f}",
                        )
                    )
                    # Record holdings change for time-weighted calculations
                    holdings_history.append((d, holdings))

                # Withdraw cash from bank
                actual_withdrawal = min(withdrawal_result.cash_from_bank, bank)
                bank -= actual_withdrawal
                transactions.append(
                    Transaction(
                        transaction_date=d,
                        action="WITHDRAWAL",
                        qty=0,
                        price=0.0,
                        ticker=ticker,
                        notes=f"${actual_withdrawal:.2f} from bank, bank = {bank:.2f}",
                    )
                )

                total_withdrawn += actual_withdrawal
                withdrawal_count += 1
                last_withdrawal_date = d

                # Track bank balance after withdrawal
                bank_history.append((d, bank))
                bank_min = min(bank_min, bank)
                bank_max = max(bank_max, bank)

    # Calculate final portfolio metrics
    final_price = end_price
    end_value = holdings * final_price  # Market value of remaining shares
    total = bank + end_value  # Total portfolio value

    # Time-based calculations
    days = (last_idx - first_idx).days
    years = days / 365.25 if days > 0 else 0.0
    start_val = calculated_qty * start_price

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

    # Calculate capital deployment statistics
    deployed_amounts = [dep for d, dep in deployment_history]
    avg_deployed_capital: float = (
        sum(deployed_amounts) / len(deployed_amounts) if deployed_amounts else 0.0
    )
    min_deployed_capital: float = min(deployed_amounts) if deployed_amounts else 0.0
    max_deployed_capital: float = max(deployed_amounts) if deployed_amounts else 0.0

    # Capital utilization rate: average deployed capital as % of initial investment
    capital_utilization: float = avg_deployed_capital / start_val if start_val > 0 else 0.0

    # Deployment range as percentages
    deployment_min_pct: float = min_deployed_capital / start_val if start_val > 0 else 0.0
    deployment_max_pct: float = max_deployed_capital / start_val if start_val > 0 else 0.0

    # opportunity_cost_total and risk_free_gains_total were accumulated during daily loop
    # (No longer need post-processing calculation)

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
        # Withdrawal metrics
        "total_withdrawn": total_withdrawn,
        "withdrawal_count": withdrawal_count,
        "shares_sold_for_withdrawals": shares_sold_for_withdrawals,
        "withdrawal_rate_pct": withdrawal_rate_pct,
        # Dividend/interest income metrics
        "total_dividends": total_dividends,
        "dividend_payment_count": dividend_payment_count,
        # Strict mode metrics
        "skipped_buys": skipped_buys,
        "skipped_buy_value": skipped_buy_value,
        "allow_margin": allow_margin,
        # Capital deployment supplementary metrics
        "avg_deployed_capital": avg_deployed_capital,
        "capital_utilization": capital_utilization,
        "deployment_min": min_deployed_capital,
        "deployment_max": max_deployed_capital,
        "deployment_min_pct": deployment_min_pct,
        "deployment_max_pct": deployment_max_pct,
    }

    # Compute buy-and-hold baseline for alpha comparison
    try:
        # Baseline: hold initial_qty shares, no trading
        assert initial_qty is not None, "initial_qty should be set for baseline calculation"
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

        # Return on deployed capital: measures efficiency when capital was actually at risk
        # This adjusts for strategies that hold significant cash positions
        return_on_deployed_capital: float = 0.0
        if capital_utilization > 0:
            return_on_deployed_capital = total_return / capital_utilization

        # Income Classification Framework
        # Calculate three-tier income breakdown for reporting

        # Universal Income: Real dividends (already tracked)
        universal_income_dollars = total_dividends
        universal_income_pct = (total_dividends / start_val * 100) if start_val > 0 else 0.0

        # Secondary Income: Volatility alpha (algorithm vs buy-and-hold)
        # This is the outperformance from mean-reversion trading
        secondary_income_dollars = (
            volatility_alpha * start_val if start_val > 0 and volatility_alpha is not None else 0.0
        )
        secondary_income_pct = volatility_alpha * 100 if volatility_alpha is not None else 0.0

        # Primary Income: Everything else (ATH selling + general trading)
        # Total gains = dividends + primary + secondary
        # So: primary = total_gains - dividends - secondary
        total_gains = total - start_val  # Absolute dollar gain
        primary_income_dollars = total_gains - universal_income_dollars - secondary_income_dollars
        primary_income_pct = (primary_income_dollars / start_val * 100) if start_val > 0 else 0.0

        summary["baseline"] = baseline_summary
        summary["volatility_alpha"] = volatility_alpha
        summary["return_on_deployed_capital"] = return_on_deployed_capital

        # Add income classification metrics
        summary["income_classification"] = {
            "universal_dollars": universal_income_dollars,
            "universal_pct": universal_income_pct,
            "primary_dollars": primary_income_dollars,
            "primary_pct": primary_income_pct,
            "secondary_dollars": secondary_income_dollars,
            "secondary_pct": secondary_income_pct,
        }
    except Exception:
        # Gracefully handle edge cases in baseline computation
        summary["baseline"] = None
        summary["volatility_alpha"] = None

    # Notify algorithm of completion
    try:
        algo_obj.on_end_holding()
    except Exception:
        # Ensure backtest completion proceeds even if algorithm cleanup prints/logs fail
        pass

    # Include algorithm-specific final stats when available for tests and reporting
    try:
        # Buyback stack final size (used by volatility-alpha tests)
        summary["final_stack_size"] = getattr(algo_obj, "buyback_stack_count", 0)
        # Total volatility alpha accumulated by algorithm (percentage)
        summary["total_volatility_alpha"] = getattr(algo_obj, "total_volatility_alpha", 0.0)
    except Exception:
        # Be tolerant of algorithms that don't expose these attributes
        summary.setdefault("final_stack_size", 0)
        summary.setdefault("total_volatility_alpha", 0.0)

    return transactions, summary


def print_income_classification(summary: Dict[str, Any], verbose: bool = True) -> None:
    """Print three-tier income classification breakdown.

    Args:
        summary: Backtest summary dict containing income_classification
        verbose: If True, print detailed breakdown. If False, print compact summary.
    """
    if "income_classification" not in summary:
        return

    ic = summary["income_classification"]

    if verbose:
        print("\n" + "=" * 70)
        print("INCOME CLASSIFICATION (Three-Tier Framework)")
        print("=" * 70)
        print()
        print("Universal Income (Asset Dividends):")
        print(f"  Total Dividends:              ${ic['universal_dollars']:>12,.2f}")
        print(f"  Yield on Initial Investment:  {ic['universal_pct']:>12.2f}%")
        if summary.get("dividend_payment_count", 0) > 0:
            avg_payment = ic["universal_dollars"] / summary["dividend_payment_count"]
            print(f"  Payment Count:                {summary['dividend_payment_count']:>12,}")
            print(f"  Average per Payment:          ${avg_payment:>12,.2f}")
        print()
        print("Primary Income (ATH Profit-Taking):")
        print(f"  Total ATH Gains:              ${ic['primary_dollars']:>12,.2f}")
        print(f"  Return on Initial:            {ic['primary_pct']:>12.2f}%")
        print()
        print("Secondary Income (Volatility Alpha):")
        print(f"  Total Harvested:              ${ic['secondary_dollars']:>12,.2f}")
        print(f"  Alpha vs Buy-and-Hold:        {ic['secondary_pct']:>12.2f}%")
        print()
        print("-" * 70)
        total_income = ic["universal_dollars"] + ic["primary_dollars"] + ic["secondary_dollars"]
        total_pct = ic["universal_pct"] + ic["primary_pct"] + ic["secondary_pct"]
        print(f"Total Income:                   ${total_income:>12,.2f}")
        print(f"Total Return:                   {total_pct:>12.2f}%")
        print(f"Annualized Return:              {summary.get('annualized', 0) * 100:>12.2f}%")
        print("=" * 70)
    else:
        # Compact one-liner
        print(
            f"Income: Universal=${ic['universal_dollars']:.2f} ({ic['universal_pct']:.2f}%), "
            f"Primary=${ic['primary_dollars']:.2f} ({ic['primary_pct']:.2f}%), "
            f"Secondary=${ic['secondary_dollars']:.2f} ({ic['secondary_pct']:.2f}%)"
        )


# NOTE: Old run_portfolio_backtest (v1) with separate banks per asset was removed 2025-10-31.
# The function below (formerly run_portfolio_backtest_v2) is now the canonical implementation.
# It uses a shared cash pool architecture which is more realistic and enables portfolio coordination.
#
# Migration: Old code using algo="buy-and-hold" should use portfolio_algo="per-asset:buy-and-hold"


def run_portfolio_backtest(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    portfolio_algo: Union[PortfolioAlgorithmBase, str],
    initial_investment: float = 1_000_000.0,
    allow_margin: bool = True,
    withdrawal_rate_pct: float = 0.0,
    withdrawal_frequency_days: int = 30,
    cash_interest_rate_pct: float = 0.0,
    dividend_data: Optional[Dict[str, pd.Series]] = None,
    reference_rate_ticker: Optional[str] = None,
    risk_free_rate_ticker: Optional[str] = None,
    inflation_rate_ticker: Optional[str] = None,
    # Legacy compatibility parameters (deprecated, ignored with warnings)
    algo: Optional[Union[AlgorithmBase, Callable, str]] = None,
    simple_mode: bool = False,
    **kwargs: Any,
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """Execute portfolio backtest with shared cash pool and portfolio-level algorithm.

    This is the unified backtest runner that implements shared bank architecture:
    - Uses a single shared cash pool across all assets
    - Calls portfolio algorithm once per day with full portfolio state
    - Executes transactions sequentially against shared bank

    Args:
        allocations: Dict mapping ticker → target allocation (must sum to 1.0)
        start_date: Backtest start date
        end_date: Backtest end date
        portfolio_algo: Portfolio algorithm or string name:
            - "per-asset:buy-and-hold" - Buy and hold each asset independently
            - "quarterly-rebalance" - Rebalance quarterly to target allocations
            - "per-asset:sd8" - Synthetic dividend (sd8) per asset
            - PortfolioAlgorithmBase instance
        initial_investment: Total starting capital
        allow_margin: Whether to allow negative bank balance
        withdrawal_rate_pct: Annual withdrawal rate (0-100)
        withdrawal_frequency_days: Days between withdrawals (default 30)
        cash_interest_rate_pct: Annual interest rate on cash reserves (default 0.0)
            Typical values: ~5% for money market, ~0% for non-interest checking
        dividend_data: Optional dict mapping ticker → pandas Series of dividend payments
            Series index should be payment dates, values are per-share dividend amounts
            Uses 90-day time-weighted average holdings for IRS-compliant calculation
        reference_rate_ticker: Optional ticker for reference benchmark (e.g., "VOO", "SPY")
            Used to calculate market-adjusted returns (alpha vs benchmark)
            If provided, fetches data and computes baseline buy-and-hold comparison
        risk_free_rate_ticker: Optional ticker for risk-free asset (e.g., "BIL", "^IRX")
            Used to model opportunity cost on cash holdings
            Daily returns applied to positive cash balance (replaces cash_interest_rate_pct)
            If not provided, falls back to cash_interest_rate_pct
        inflation_rate_ticker: Optional ticker for inflation data (e.g., "CPI" via custom provider)
            Used to calculate inflation-adjusted (real) returns
            Tracks cumulative inflation adjustment from start date
            Adds real_return and inflation_adjusted metrics to summary
        algo: DEPRECATED - Use portfolio_algo instead
        simple_mode: DEPRECATED - No longer used
        **kwargs: DEPRECATED - Ignored legacy parameters

    Returns:
        Tuple of (all_transactions, portfolio_summary)
    """
    import warnings

    from src.algorithms.portfolio_factory import build_portfolio_algo_from_name
    from src.data.fetcher import HistoryFetcher
    from src.models.model_types import AssetState

    # Validate allocations
    total_allocation = sum(allocations.values())
    if abs(total_allocation - 1.0) > 0.01:
        raise ValueError(f"Allocations must sum to 1.0, got {total_allocation:.3f}")

    # Handle string interface
    if isinstance(portfolio_algo, str):
        portfolio_algo = build_portfolio_algo_from_name(portfolio_algo, allocations)

    # Handle deprecated 'algo' parameter
    if algo is not None:
        warnings.warn(
            "The 'algo' parameter is deprecated. Use 'portfolio_algo' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if isinstance(algo, str):
            if algo == "buy-and-hold":
                portfolio_algo = build_portfolio_algo_from_name(
                    "per-asset:buy-and-hold", allocations
                )
            else:
                portfolio_algo = build_portfolio_algo_from_name(f"per-asset:{algo}", allocations)

    # Warn about ignored legacy kwargs
    if kwargs:
        ignored = ", ".join(kwargs.keys())
        warnings.warn(f"Ignored deprecated parameters: {ignored}", DeprecationWarning, stacklevel=2)

    # Validate portfolio_algo type (after string conversion)
    if not isinstance(portfolio_algo, PortfolioAlgorithmBase):
        raise TypeError(
            f"portfolio_algo must be PortfolioAlgorithmBase or string, got {type(portfolio_algo).__name__}"
        )

    # Fetch price data for all assets
    fetcher = HistoryFetcher()
    price_data: Dict[str, pd.DataFrame] = {}

    print(f"Fetching data for {len(allocations)} assets...")
    for ticker in allocations.keys():
        print(f"  - {ticker}...", end=" ")
        df = fetcher.get_history(ticker, start_date, end_date)
        if df is None or df.empty:
            raise ValueError(f"No data available for {ticker}")
        price_data[ticker] = df
        print(f"OK ({len(df)} days)")

    # Find common trading dates
    all_dates: Set[date] = set()
    for df in price_data.values():
        dates = set(pd.to_datetime(df.index).date)
        all_dates = all_dates.intersection(dates) if all_dates else dates

    common_dates = sorted([d for d in all_dates if start_date <= d <= end_date])
    if not common_dates:
        raise ValueError("No common trading dates across all assets")

    print(f"Common trading days: {len(common_dates)} ({common_dates[0]} to {common_dates[-1]})")

    # Index price data by date for fast lookup
    price_data_indexed: Dict[str, pd.DataFrame] = {}
    for ticker, df in price_data.items():
        df_copy = df.copy()
        df_copy.index = pd.to_datetime(df_copy.index).date
        price_data_indexed[ticker] = df_copy

    # Fetch reference rate data if provided (for market-adjusted returns)
    reference_data: Optional[pd.DataFrame] = None
    if reference_rate_ticker:
        print(f"Fetching reference benchmark ({reference_rate_ticker})...", end=" ")
        reference_data = fetcher.get_history(reference_rate_ticker, start_date, end_date)
        if reference_data is not None and not reference_data.empty:
            print(f"OK ({len(reference_data)} days)")
        else:
            print("WARN: No data available, skipping baseline calculation")
            reference_data = None

    # Fetch risk-free rate data if provided (for cash interest modeling)
    risk_free_data: Optional[pd.DataFrame] = None
    risk_free_returns: Dict[date, float] = {}
    if risk_free_rate_ticker:
        print(f"Fetching risk-free asset ({risk_free_rate_ticker})...", end=" ")
        risk_free_data = fetcher.get_history(risk_free_rate_ticker, start_date, end_date)
        if risk_free_data is not None and not risk_free_data.empty:
            print(f"OK ({len(risk_free_data)} days)")
            # Calculate daily returns from price data
            rf_indexed = risk_free_data.copy()
            rf_indexed.index = pd.to_datetime(rf_indexed.index).date
            if "Close" in rf_indexed.columns:
                close_prices = rf_indexed["Close"].values
                rf_dates = list(rf_indexed.index)
                for i in range(1, len(close_prices)):
                    prev_price = float(close_prices[i - 1])
                    curr_price = float(close_prices[i])
                    if prev_price > 0:
                        risk_free_returns[rf_dates[i]] = (curr_price - prev_price) / prev_price
        else:
            print("WARN: No data available, falling back to cash_interest_rate_pct")
            risk_free_data = None

    # Fetch inflation data if provided (for real returns calculation)
    inflation_data: Optional[pd.DataFrame] = None
    cumulative_inflation: Dict[date, float] = {}
    if inflation_rate_ticker:
        print(f"Fetching inflation data ({inflation_rate_ticker})...", end=" ")
        inflation_data = fetcher.get_history(inflation_rate_ticker, start_date, end_date)
        if inflation_data is not None and not inflation_data.empty:
            print(f"OK ({len(inflation_data)} days)")
            # Calculate cumulative inflation adjustment from start
            infl_indexed = inflation_data.copy()
            infl_indexed.index = pd.to_datetime(infl_indexed.index).date
            value_col = "Close" if "Close" in infl_indexed.columns else "Value"
            if value_col in infl_indexed.columns:
                infl_values = infl_indexed[value_col].values
                infl_dates = list(infl_indexed.index)
                # Find start CPI value
                if common_dates[0] in infl_dates:
                    start_cpi_idx = infl_dates.index(common_dates[0])
                    start_cpi = float(infl_values[start_cpi_idx])
                    # Calculate cumulative multiplier for each date
                    for i, d in enumerate(infl_dates):
                        if d >= common_dates[0]:
                            curr_cpi = float(infl_values[i])
                            cumulative_inflation[d] = curr_cpi / start_cpi if start_cpi > 0 else 1.0
        else:
            print("WARN: No data available, skipping inflation adjustment")
            inflation_data = None

    # Initialize portfolio state
    shared_bank = initial_investment
    holdings: Dict[str, int] = {}
    all_transactions: List[Transaction] = []

    # Initial purchase
    print("\nInitial purchase:")
    for ticker, alloc_pct in allocations.items():
        first_price = price_data_indexed[ticker].loc[common_dates[0], "Close"].item()
        qty = int((initial_investment * alloc_pct) / first_price)
        cost = qty * first_price
        holdings[ticker] = qty
        shared_bank -= cost
        print(f"  {ticker}: {qty} shares × ${first_price:.2f} = ${cost:,.2f}")

        all_transactions.append(
            Transaction(
                transaction_date=common_dates[0],
                action="BUY",
                qty=qty,
                price=first_price,
                ticker=ticker,
                notes="Initial purchase",
            )
        )

    print(f"Initial bank balance: ${shared_bank:,.2f}\n")

    # Initialize per-asset algorithms (if using PerAssetPortfolioAlgorithm)
    from src.algorithms import PerAssetPortfolioAlgorithm

    if isinstance(portfolio_algo, PerAssetPortfolioAlgorithm):
        print("Initializing per-asset algorithms...")
        for ticker, algo in portfolio_algo.strategies.items():
            if hasattr(algo, "on_new_holdings"):
                first_price = price_data_indexed[ticker].loc[common_dates[0], "Close"].item()
                algo.on_new_holdings(holdings[ticker], first_price)
                print(
                    f"  {ticker}: initialized with {holdings[ticker]} shares @ ${first_price:.2f}"
                )
        print()

    # Track daily portfolio values
    daily_portfolio_values: Dict[date, float] = {}
    daily_bank_values: Dict[date, float] = {}
    daily_asset_values: Dict[str, Dict[date, float]] = {ticker: {} for ticker in allocations.keys()}
    daily_withdrawals: Dict[date, float] = {}  # Track withdrawals by date

    # Withdrawal tracking
    total_withdrawn: float = 0.0
    withdrawal_count: int = 0
    last_withdrawal_date: Optional[date] = None

    # Calculate withdrawal amounts if enabled
    if withdrawal_rate_pct > 0:
        annual_withdrawal = initial_investment * (withdrawal_rate_pct / 100.0)
        base_withdrawal_amount = annual_withdrawal * (withdrawal_frequency_days / 365.25)
    else:
        base_withdrawal_amount = 0.0

    # Cash interest tracking
    total_interest_earned: float = 0.0
    daily_interest_rate = (
        (cash_interest_rate_pct / 100.0) / 365.25 if cash_interest_rate_pct > 0 else 0.0
    )

    # Dividend tracking (per-asset)
    total_dividends_by_asset: Dict[str, float] = {ticker: 0.0 for ticker in allocations.keys()}
    dividend_payment_count_by_asset: Dict[str, int] = {ticker: 0 for ticker in allocations.keys()}

    # Holdings history for time-weighted dividend calculation (per-asset)
    holdings_history: Dict[str, List[Tuple[date, int]]] = {
        ticker: [(common_dates[0], holdings[ticker])] for ticker in allocations.keys()
    }

    # Main backtest loop
    for current_date in common_dates:
        # Build current asset states
        assets: Dict[str, AssetState] = {}
        for ticker in allocations.keys():
            current_price = price_data_indexed[ticker].loc[current_date, "Close"].item()
            assets[ticker] = AssetState(
                ticker=ticker, holdings=holdings[ticker], price=current_price
            )

        # Build today's price data (OHLC)
        prices: Dict[str, pd.Series] = {}
        for ticker in allocations.keys():
            prices[ticker] = price_data_indexed[ticker].loc[current_date]

        # Build history (all data up to yesterday)
        history: Dict[str, pd.DataFrame] = {}
        for ticker in allocations.keys():
            history[ticker] = price_data_indexed[ticker][
                price_data_indexed[ticker].index < current_date
            ]

        # Ask portfolio algorithm for transactions
        transactions_by_ticker = portfolio_algo.on_portfolio_day(
            date_=current_date,
            assets=assets,
            bank=shared_bank,
            prices=prices,
            history=history,
        )

        # Execute all transactions (update holdings and shared bank)
        for ticker, txns in transactions_by_ticker.items():
            for tx in txns:
                # Fill in execution details
                tx.transaction_date = current_date
                tx.ticker = ticker
                if tx.price == 0.0:
                    tx.price = assets[ticker].price

                if tx.action.upper() == "BUY":
                    cost = tx.qty * tx.price
                    if shared_bank >= cost or allow_margin:
                        holdings[ticker] += tx.qty
                        shared_bank -= cost
                        all_transactions.append(tx)
                    else:
                        # Insufficient cash - skip transaction
                        skipped_tx = Transaction(
                            transaction_date=current_date,
                            action="SKIP BUY",
                            qty=tx.qty,
                            price=tx.price,
                            ticker=ticker,
                            notes=f"{tx.notes}, insufficient cash: ${shared_bank:.2f} < ${cost:.2f}",
                        )
                        all_transactions.append(skipped_tx)

                elif tx.action.upper() == "SELL":
                    if holdings[ticker] >= tx.qty:
                        proceeds = tx.qty * tx.price
                        holdings[ticker] -= tx.qty
                        shared_bank += proceeds
                        all_transactions.append(tx)
                    else:
                        # Insufficient holdings - skip transaction
                        skipped_tx = Transaction(
                            transaction_date=current_date,
                            action="SKIP SELL",
                            qty=tx.qty,
                            price=tx.price,
                            ticker=ticker,
                            notes=f"{tx.notes}, insufficient holdings: {holdings[ticker]} < {tx.qty}",
                        )
                        all_transactions.append(skipped_tx)

        # Track holdings changes for time-weighted dividend calculation
        for ticker in allocations.keys():
            # If holdings changed from last recorded value, track the change
            if (
                len(holdings_history[ticker]) == 0
                or holdings_history[ticker][-1][1] != holdings[ticker]
            ):
                holdings_history[ticker].append((current_date, holdings[ticker]))

        # Process withdrawals (if enabled and due)
        if base_withdrawal_amount > 0:
            # Check if withdrawal is due
            days_since_last = None
            if last_withdrawal_date is None:
                # First withdrawal happens on first day
                days_since_last = withdrawal_frequency_days
            else:
                days_since_last = (current_date - last_withdrawal_date).days

            if days_since_last >= withdrawal_frequency_days:
                # Withdraw from shared bank (portfolio-level, not per-asset)
                withdrawal_amount = base_withdrawal_amount

                # Check if we have enough cash
                if shared_bank >= withdrawal_amount:
                    # Simple case: withdraw from cash
                    actual_withdrawal = withdrawal_amount
                    shared_bank -= actual_withdrawal
                    withdrawal_notes = (
                        f"${actual_withdrawal:.2f} withdrawn from cash, bank=${shared_bank:.2f}"
                    )
                else:
                    # Need to sell assets to meet withdrawal
                    # First, withdraw all available cash
                    cash_available = max(0, shared_bank)
                    shortfall = withdrawal_amount - cash_available

                    if not allow_margin and shortfall > 0:
                        # Sell assets proportionally to raise cash for shortfall
                        total_asset_value = sum(
                            holdings[t] * assets[t].price for t in allocations.keys()
                        )

                        if total_asset_value > 0:
                            # Sell proportionally from each asset
                            for ticker in allocations.keys():
                                if holdings[ticker] > 0:
                                    asset_value = holdings[ticker] * assets[ticker].price
                                    proportion = asset_value / total_asset_value
                                    amount_to_raise = shortfall * proportion
                                    shares_to_sell = int(amount_to_raise / assets[ticker].price)

                                    if shares_to_sell > 0:
                                        shares_to_sell = min(shares_to_sell, holdings[ticker])
                                        proceeds = shares_to_sell * assets[ticker].price
                                        holdings[ticker] -= shares_to_sell
                                        shared_bank += proceeds

                                        # Record forced sale
                                        all_transactions.append(
                                            Transaction(
                                                transaction_date=current_date,
                                                action="SELL",
                                                qty=shares_to_sell,
                                                price=assets[ticker].price,
                                                ticker=ticker,
                                                notes=f"Forced sale to fund withdrawal (raised ${proceeds:.2f})",
                                            )
                                        )

                        # Now withdraw what we can (cash available + proceeds from sales)
                        actual_withdrawal = min(withdrawal_amount, shared_bank)
                        shared_bank -= actual_withdrawal
                        withdrawal_notes = f"${actual_withdrawal:.2f} withdrawn (${cash_available:.2f} cash + ${actual_withdrawal-cash_available:.2f} from asset sales), bank=${shared_bank:.2f}"
                    else:
                        # allow_margin=True: allow negative bank balance
                        actual_withdrawal = withdrawal_amount
                        shared_bank -= actual_withdrawal
                        withdrawal_notes = f"${actual_withdrawal:.2f} withdrawn (margin used), bank=${shared_bank:.2f}"

                total_withdrawn += actual_withdrawal
                withdrawal_count += 1
                last_withdrawal_date = current_date

                # Record withdrawal transaction
                all_transactions.append(
                    Transaction(
                        transaction_date=current_date,
                        action="WITHDRAWAL",
                        qty=0,
                        price=0.0,
                        ticker="CASH",
                        notes=withdrawal_notes,
                    )
                )

                # Track daily withdrawals for visualization
                daily_withdrawals[current_date] = actual_withdrawal

        # Process dividend/interest payments (if available)
        if dividend_data:
            for ticker in allocations.keys():
                if ticker in dividend_data and dividend_data[ticker] is not None:
                    div_series = dividend_data[ticker]
                    if not div_series.empty:
                        # Check if this date has a dividend payment
                        div_dates = pd.to_datetime(div_series.index).date
                        if current_date in div_dates:
                            # Find the dividend amount for this date
                            div_idx = list(div_dates).index(current_date)
                            div_per_share = div_series.iloc[div_idx]

                            # Calculate time-weighted average holdings over accrual period
                            # Use 90-day lookback (typical for quarterly dividends)
                            accrual_period_days = 90
                            period_start = (
                                current_date
                                - pd.Timedelta(days=accrual_period_days).to_pytimedelta()
                            )
                            avg_holdings = calculate_time_weighted_average_holdings(
                                holdings_history[ticker], period_start, current_date
                            )

                            # Dividend payment based on average holdings during accrual period
                            div_payment = div_per_share * avg_holdings

                            shared_bank += div_payment
                            total_dividends_by_asset[ticker] += div_payment
                            dividend_payment_count_by_asset[ticker] += 1

                            all_transactions.append(
                                Transaction(
                                    transaction_date=current_date,
                                    action="DIVIDEND",
                                    qty=int(
                                        avg_holdings
                                    ),  # Display average holdings (rounded for display)
                                    price=div_per_share,
                                    ticker=ticker,
                                    notes=f"${div_payment:.2f} (avg {avg_holdings:.2f} shares over 90 days), bank = {shared_bank:.2f}",
                                )
                            )

        # Accrue daily interest on cash reserves (if positive balance)
        if shared_bank > 0:
            # Use risk-free asset returns if available, otherwise fall back to fixed rate
            if risk_free_returns and current_date in risk_free_returns:
                daily_return = risk_free_returns[current_date]
                daily_interest = shared_bank * daily_return
            elif daily_interest_rate > 0:
                daily_interest = shared_bank * daily_interest_rate
            else:
                daily_interest = 0.0

            if daily_interest > 0:
                shared_bank += daily_interest
                total_interest_earned += daily_interest

        # Record daily portfolio value
        total_asset_value = sum(holdings[t] * assets[t].price for t in allocations.keys())
        daily_portfolio_values[current_date] = shared_bank + total_asset_value
        daily_bank_values[current_date] = shared_bank

        # Record per-asset daily values
        for ticker in allocations.keys():
            daily_asset_values[ticker][current_date] = holdings[ticker] * assets[ticker].price

    # Calculate final portfolio metrics
    final_date = common_dates[-1]
    final_asset_value = sum(
        holdings[ticker] * price_data_indexed[ticker].loc[final_date, "Close"].item()
        for ticker in allocations.keys()
    )
    final_total_value = shared_bank + final_asset_value

    # Returns
    total_return_pct = ((final_total_value - initial_investment) / initial_investment) * 100
    days = (final_date - common_dates[0]).days
    years = days / 365.25
    annualized_return_pct = (
        (((final_total_value / initial_investment) ** (1 / years)) - 1) * 100 if years > 0 else 0
    )

    # Build per-asset summaries
    asset_results = {}
    for ticker, alloc_pct in allocations.items():
        final_price = price_data_indexed[ticker].loc[final_date, "Close"].item()
        final_value = holdings[ticker] * final_price
        initial_value = initial_investment * alloc_pct

        asset_results[ticker] = {
            "allocation": alloc_pct,
            "initial_investment": initial_value,
            "final_holdings": holdings[ticker],
            "final_price": final_price,
            "final_value": final_value,
            "total_return": (
                ((final_value - initial_value) / initial_value) * 100 if initial_value > 0 else 0
            ),
        }

    # Build portfolio summary
    portfolio_summary = {
        "total_final_value": final_total_value,
        "final_bank": shared_bank,
        "final_asset_value": final_asset_value,
        "total_return": total_return_pct,
        "annualized_return": annualized_return_pct,
        "initial_investment": initial_investment,
        "start_date": common_dates[0],
        "end_date": final_date,
        "trading_days": len(common_dates),
        "assets": asset_results,
        "allocations": allocations,
        "daily_values": daily_portfolio_values,
        "daily_bank_values": daily_bank_values,
        "daily_asset_values": daily_asset_values,  # Per-asset daily values for visualization
        "daily_withdrawals": daily_withdrawals,  # Daily withdrawal amounts for horn chart
        "transaction_count": len(
            [tx for tx in all_transactions if "SKIP" not in tx.action and tx.action != "WITHDRAWAL"]
        ),
        "skipped_count": len([tx for tx in all_transactions if "SKIP" in tx.action]),
        "total_withdrawn": total_withdrawn,
        "withdrawal_count": withdrawal_count,
        "withdrawal_rate_pct": withdrawal_rate_pct,
        "cash_interest_earned": total_interest_earned,
        "cash_interest_rate_pct": cash_interest_rate_pct,
        "risk_free_rate_ticker": risk_free_rate_ticker,  # Track which method was used
        "total_dividends_by_asset": total_dividends_by_asset,
        "total_dividends": sum(total_dividends_by_asset.values()),
        "dividend_payment_count_by_asset": dividend_payment_count_by_asset,
    }

    # Compute reference benchmark baseline (if provided)
    if reference_data is not None and not reference_data.empty:
        try:
            # Index reference data by date
            ref_indexed = reference_data.copy()
            ref_indexed.index = pd.to_datetime(ref_indexed.index).date

            # Get reference prices on first and last common dates
            if common_dates[0] in ref_indexed.index and final_date in ref_indexed.index:
                ref_start_price = ref_indexed.loc[common_dates[0], "Close"]
                ref_end_price = ref_indexed.loc[final_date, "Close"]

                # Calculate buy-and-hold return for reference benchmark
                # Invest same initial_investment in reference asset
                ref_shares = initial_investment / ref_start_price
                ref_end_value = ref_shares * ref_end_price
                ref_total_return = (
                    (ref_end_value - initial_investment) / initial_investment
                    if initial_investment > 0
                    else 0
                )

                # Calculate annualized return
                if years > 0 and initial_investment > 0:
                    ref_annualized = (ref_end_value / initial_investment) ** (1.0 / years) - 1.0
                else:
                    ref_annualized = 0.0

                baseline_summary = {
                    "ticker": reference_rate_ticker,
                    "start_date": common_dates[0],
                    "end_date": final_date,
                    "start_price": ref_start_price,
                    "end_price": ref_end_price,
                    "start_value": initial_investment,
                    "end_value": ref_end_value,
                    "total_return": ref_total_return,
                    "annualized": ref_annualized,
                }

                # Alpha = portfolio return - benchmark return
                volatility_alpha = total_return_pct / 100.0 - ref_total_return

                portfolio_summary["baseline"] = baseline_summary
                portfolio_summary["volatility_alpha"] = volatility_alpha
                portfolio_summary["alpha_pct"] = volatility_alpha * 100.0
            else:
                # Reference data doesn't cover our date range
                portfolio_summary["baseline"] = None
                portfolio_summary["volatility_alpha"] = None
        except Exception:
            # Gracefully handle edge cases in baseline computation
            portfolio_summary["baseline"] = None
            portfolio_summary["volatility_alpha"] = None
    else:
        portfolio_summary["baseline"] = None
        portfolio_summary["volatility_alpha"] = None

    # Compute inflation-adjusted (real) returns if inflation data provided
    if cumulative_inflation and final_date in cumulative_inflation:
        try:
            # Get cumulative inflation from start to end
            inflation_multiplier = cumulative_inflation[final_date]

            # Calculate real (inflation-adjusted) final value
            real_final_value = final_total_value / inflation_multiplier

            # Calculate real return
            real_total_return_pct = (
                (real_final_value - initial_investment) / initial_investment * 100.0
                if initial_investment > 0
                else 0.0
            )

            # Calculate real annualized return
            if years > 0 and initial_investment > 0:
                real_annualized_pct = (real_final_value / initial_investment) ** (1.0 / years) - 1.0
                real_annualized_pct *= 100.0
            else:
                real_annualized_pct = 0.0

            portfolio_summary["inflation_rate_ticker"] = inflation_rate_ticker
            portfolio_summary["cumulative_inflation"] = (
                inflation_multiplier - 1.0
            ) * 100.0  # As percentage
            portfolio_summary["real_final_value"] = real_final_value
            portfolio_summary["real_total_return"] = real_total_return_pct
            portfolio_summary["real_annualized_return"] = real_annualized_pct
        except Exception:
            # Gracefully handle edge cases
            portfolio_summary["inflation_rate_ticker"] = None
            portfolio_summary["cumulative_inflation"] = None
            portfolio_summary["real_final_value"] = None
            portfolio_summary["real_total_return"] = None
            portfolio_summary["real_annualized_return"] = None
    else:
        portfolio_summary["inflation_rate_ticker"] = None
        portfolio_summary["cumulative_inflation"] = None
        portfolio_summary["real_final_value"] = None
        portfolio_summary["real_total_return"] = None
        portfolio_summary["real_annualized_return"] = None

    return all_transactions, portfolio_summary
