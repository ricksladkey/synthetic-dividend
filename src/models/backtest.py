"""Backtest engine for algorithmic trading strategies.

Provides abstract base for strategy implementations and execution framework
for backtesting against historical OHLC price data.
"""

import warnings
from datetime import date
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import pandas as pd

# Import algorithm classes from dedicated package
from src.algorithms import (  # noqa: F401; (re-exported for backwards compatibility)
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


def _create_portfolio_algorithm_from_single_ticker(
    algo: Optional[Union[AlgorithmBase, Callable]],
    algo_params: Optional[Dict[str, Any]],
    ticker: str,
) -> PortfolioAlgorithmBase:
    """Convert single-ticker algorithm to portfolio algorithm.

    Args:
        algo: Single-ticker algorithm (AlgorithmBase instance or None)
        algo_params: Parameters for callable algorithms (not used if algo is AlgorithmBase)
        ticker: Ticker symbol

    Returns:
        PortfolioAlgorithmBase wrapping the single-ticker algorithm

    Raises:
        ValueError: If algo is a callable (not yet supported in wrapper)
    """
    from src.algorithms import PerAssetPortfolioAlgorithm

    # Callables not yet supported in portfolio wrapper path
    if callable(algo) and not isinstance(algo, AlgorithmBase):
        raise ValueError("Callable algorithms not supported in portfolio wrapper path")

    # Default to buy-and-hold if no algorithm
    if algo is None:
        algo_obj: AlgorithmBase = BuyAndHoldAlgorithm()
    elif isinstance(algo, AlgorithmBase):
        algo_obj = algo
    else:
        raise ValueError(f"Unsupported algo type: {type(algo)}")

    # Wrap in portfolio algorithm
    return PerAssetPortfolioAlgorithm({ticker: algo_obj})


def _map_portfolio_to_single_ticker_summary(
    portfolio_summary: Dict[str, Any],
    ticker: str,
    df_indexed: pd.DataFrame,
    start_date: date,
    end_date: date,
    algo_obj: Optional[AlgorithmBase],
    transactions: Optional[List[Transaction]] = None,
) -> Dict[str, Any]:
    """Map portfolio backtest summary to single-ticker format.

    Args:
        portfolio_summary: Summary from run_portfolio_backtest()
        ticker: Ticker symbol
        df_indexed: Price data (date-indexed)
        start_date: Backtest start date
        end_date: Backtest end date
        algo_obj: Algorithm instance (for extracting algorithm-specific stats)

    Returns:
        Summary dict in single-ticker format
    """
    # Get asset-specific results
    asset_results = portfolio_summary["assets"][ticker]

    # Extract prices from dataframe
    first_date = portfolio_summary["start_date"]
    last_date = portfolio_summary["end_date"]
    start_price = float(df_indexed.loc[first_date, "Close"])
    end_price = float(df_indexed.loc[last_date, "Close"])
    start_value = asset_results["initial_investment"]

    # Calculate years for annualized return
    days = (last_date - first_date).days
    years = days / 365.25 if days > 0 else 0.0

    # Calculate bank balance statistics from daily_bank_values
    daily_bank_balances = list(portfolio_summary.get("daily_bank_values", {}).values())
    if daily_bank_balances:
        bank_min = min(daily_bank_balances)
        bank_max = max(daily_bank_balances)
        bank_avg = sum(daily_bank_balances) / len(daily_bank_balances)
        bank_negative_count = sum(1 for b in daily_bank_balances if b < 0)
        bank_positive_count = sum(1 for b in daily_bank_balances if b > 0)
    else:
        # Fallback if no daily values (shouldn't happen)
        bank_min = portfolio_summary["final_bank"]
        bank_max = portfolio_summary["final_bank"]
        bank_avg = portfolio_summary["final_bank"]
        bank_negative_count = 0
        bank_positive_count = 0

    # Build single-ticker summary
    summary = {
        "ticker": ticker,
        "start_date": first_date,
        "start_price": start_price,
        "start_value": start_value,
        "end_date": last_date,
        "end_price": end_price,
        "end_value": asset_results["final_value"],
        "holdings": asset_results["final_holdings"],
        "bank": portfolio_summary["final_bank"],
        # Bank statistics - now calculated from daily_bank_values
        "bank_min": bank_min,
        "bank_max": bank_max,
        "bank_avg": bank_avg,
        "bank_negative_count": bank_negative_count,
        "bank_positive_count": bank_positive_count,
        # Costs/Gains - now supported in portfolio backtest
        "opportunity_cost": portfolio_summary.get("opportunity_cost", 0.0),
        "risk_free_gains": portfolio_summary.get("cash_interest_earned", 0.0),
        # Returns
        "total": portfolio_summary["total_final_value"],
        "total_return": portfolio_summary["total_return"] / 100.0,  # Convert from percentage
        "annualized": portfolio_summary["annualized_return"] / 100.0,  # Convert from percentage
        "years": years,
        # Withdrawals
        "total_withdrawn": portfolio_summary["total_withdrawn"],
        "withdrawal_count": portfolio_summary["withdrawal_count"],
        "shares_sold_for_withdrawals": (
            sum(
                tx.qty
                for tx in transactions
                if tx.action == "SELL" and "withdrawal" in tx.notes.lower()
            )
            if transactions
            else 0
        ),
        "withdrawal_rate_pct": portfolio_summary["withdrawal_rate_pct"],
        # Dividends - now supported in portfolio backtest
        "total_dividends": portfolio_summary.get("total_dividends", 0.0),
        "dividend_payment_count": sum(
            portfolio_summary.get("dividend_payment_count_by_asset", {}).values()
        ),
        # Strict mode
        "skipped_buys": portfolio_summary["skipped_count"],
        "skipped_buy_value": (
            sum(
                tx.price * tx.qty
                for tx in transactions
                if tx.action == "SKIP BUY" and "insufficient cash" in tx.notes.lower()
            )
            if transactions
            else 0.0
        ),
        "allow_margin": True,  # TODO: Get from params
        # Capital deployment - not tracked in portfolio
        "avg_deployed_capital": 0.0,
        "capital_utilization": 0.0,
        "deployment_min": 0.0,
        "deployment_max": 0.0,
        "deployment_min_pct": 0.0,
        "deployment_max_pct": 0.0,
    }

    # Calculate baseline (buy-and-hold)
    initial_qty = int(asset_results["initial_investment"] / start_price)
    baseline_end_value = initial_qty * end_price
    baseline_total = baseline_end_value
    baseline_total_return = (baseline_total - start_value) / start_value if start_value > 0 else 0.0

    if years > 0 and start_value > 0:
        baseline_annualized = (baseline_total / start_value) ** (1.0 / years) - 1.0
    else:
        baseline_annualized = 0.0

    baseline_summary = {
        "start_date": first_date,
        "end_date": last_date,
        "start_price": start_price,
        "end_price": end_price,
        "start_value": start_value,
        "end_value": baseline_end_value,
        "total": baseline_total,
        "total_return": baseline_total_return,
        "annualized": baseline_annualized,
    }

    # Calculate volatility alpha
    volatility_alpha = summary["total_return"] - baseline_total_return

    # Return on deployed capital
    return_on_deployed_capital = 0.0

    # Income classification
    universal_income_dollars = summary["total_dividends"]
    universal_income_pct = (
        (universal_income_dollars / start_value * 100) if start_value > 0 else 0.0
    )

    secondary_income_dollars = volatility_alpha * start_value if start_value > 0 else 0.0
    secondary_income_pct = volatility_alpha * 100

    total_gains = summary["total"] - start_value
    primary_income_dollars = total_gains - universal_income_dollars - secondary_income_dollars
    primary_income_pct = (primary_income_dollars / start_value * 100) if start_value > 0 else 0.0

    summary["baseline"] = baseline_summary
    summary["volatility_alpha"] = volatility_alpha
    summary["return_on_deployed_capital"] = return_on_deployed_capital
    summary["income_classification"] = {
        "universal_dollars": universal_income_dollars,
        "universal_pct": universal_income_pct,
        "primary_dollars": primary_income_dollars,
        "primary_pct": primary_income_pct,
        "secondary_dollars": secondary_income_dollars,
        "secondary_pct": secondary_income_pct,
    }

    # Algorithm-specific stats
    if algo_obj is not None:
        summary["total_volatility_alpha"] = getattr(algo_obj, "total_volatility_alpha", 0.0)
    else:
        summary["total_volatility_alpha"] = portfolio_summary.get("total_volatility_alpha", 0.0)

    summary["final_stack_size"] = portfolio_summary.get("final_stack_size", 0)

    return summary


def run_algorithm_backtest(
    # Single-ticker parameters (legacy interface) - maintain backward compatibility order
    df: Optional[pd.DataFrame] = None,
    ticker: str = "",
    initial_qty: Optional[float] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    algo: Optional[Union[AlgorithmBase, Callable]] = None,
    # Multi-asset parameters (portfolio interface)
    allocations: Optional[Dict[str, float]] = None,
    portfolio_algo: Optional[Union[PortfolioAlgorithmBase, str]] = None,
    # Common parameters
    algo_params: Optional[Dict[str, Any]] = None,
    reference_rate_ticker: str = "",
    risk_free_rate_ticker: str = "",
    # Dividend/interest payments
    dividend_series: Optional[pd.Series] = None,
    # Withdrawal policy parameters
    withdrawal_rate_pct: float = 0.0,
    withdrawal_frequency_days: int = 30,
    inflation_rate_ticker: Optional[str] = None,
    simple_mode: bool = False,
    # Bank behavior
    allow_margin: bool = True,
    # Investment amount (alternative to initial_qty)
    initial_investment: Optional[float] = None,
    # Test/development parameters
    cache_dir: str = "cache",
    **kwargs: Any,
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """Execute backtest of trading algorithm against historical price data.

    .. deprecated::
        Use :func:`run_portfolio_backtest` instead. This wrapper function is maintained for
        backward compatibility but will be removed in a future version. For single-ticker
        backtests, use ``run_portfolio_backtest(allocations={ticker: 1.0}, ...)`` with the
        ``per-asset:`` algorithm prefix.

    **Unified Interface (Phase 3)**:
    This function provides a unified interface for both single-ticker and multi-asset backtesting.
    Use single-ticker parameters (df, ticker, algo) for traditional single-asset backtests,
    or portfolio parameters (allocations, portfolio_algo) for multi-asset portfolio backtests.

    **Single-Ticker Mode** (legacy interface):
    - Provide: df, ticker, algo (and optionally initial_qty/initial_investment)
    - Returns: Single-ticker summary with holdings, bank, returns, etc.

    **Multi-Asset Mode** (portfolio interface):
    - Provide: allocations, portfolio_algo (and optionally initial_investment)
    - Returns: Portfolio summary with per-asset breakdowns and shared cash pool metrics

    **Implementation Note (Phase 3 Consolidation)**:
    For single-ticker backtests, this function routes to run_portfolio_backtest(),
    treating the single ticker as a 100% allocated portfolio. This eliminates
    ~800 lines of duplicate backtest logic.

    Flow:
    1. Initial BUY of initial_qty shares on first trading day ≥ start_date
    2. Each day: call algo.on_day() which may return Transaction or None
    3. SELL: increases bank, decreases holdings (capped at current holdings)
    4. BUY: decreases bank (may go negative), increases holdings
    5. Process withdrawals (if configured) - withdraw from bank or sell shares if needed
    6. Compute final portfolio value and returns vs buy-and-hold baseline
    7. Calculate opportunity cost (negative bank) and risk-free gains (positive bank)

    Args:
        # Single-ticker parameters (legacy interface)
        df: Historical OHLC price data (indexed by date) - for single-ticker mode
        ticker: Stock symbol for reporting - for single-ticker mode
        initial_qty: Number of shares to purchase initially (optional) - for single-ticker mode
                    Either initial_qty OR initial_investment must be provided for single-ticker mode
        start_date: Backtest start date (inclusive, optional - defaults to first date)
        end_date: Backtest end date (inclusive, optional - defaults to last date)
        algo: Algorithm instance or callable (defaults to buy-and-hold) - for single-ticker mode
        # Multi-asset parameters (portfolio interface)
        allocations: Dict mapping ticker → target allocation (must sum to 1.0) - for portfolio mode
        portfolio_algo: Portfolio algorithm or string name - for portfolio mode
        # Common parameters
        algo_params: Optional parameters dict (for callable algos)
        reference_rate_ticker: Ticker symbol for reference asset (for reporting)
        risk_free_rate_ticker: Ticker symbol for risk-free asset (for reporting)
        dividend_series: Historical dividend/interest payments (Series indexed by ex-date)
                        Each value is dividend amount per share on that date
                        Works for equity dividends (AAPL) and ETF distributions (BIL)
                        If provided, dividends are credited to bank on ex-date
                        If None, no dividend income is tracked
        withdrawal_rate_pct: Annual withdrawal rate as % of initial portfolio value
                            (e.g., 4.0 for 4% withdrawal rate)
                            Withdrawals are taken monthly and CPI-adjusted
        withdrawal_frequency_days: Days between withdrawals (default 30 for monthly)
        inflation_rate_ticker: Optional ticker for inflation data (e.g., "CPI" via custom provider)
                          Used to calculate inflation-adjusted (real) returns
                          If provided, adds real_return and inflation_adjusted metrics to summary
        simple_mode: If True, disables opportunity cost, risk-free gains, and CPI adjustment
                    Useful for unit tests where we want clean, simple behavior
                    (free borrowing, cash holds value, no inflation)
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
    # Note: reference_data and risk_free_data parameters removed - these are now ignored
    if "reference_asset_df" in kwargs:
        kwargs.pop("reference_asset_df")  # Remove deprecated parameter
    if "risk_free_asset_df" in kwargs:
        kwargs.pop("risk_free_asset_df")  # Remove deprecated parameter
    # Handle deprecated parameter name aliases
    if "reference_asset_ticker" in kwargs:
        reference_rate_ticker = kwargs.pop("reference_asset_ticker")
    if "risk_free_asset_ticker" in kwargs:
        risk_free_rate_ticker = kwargs.pop("risk_free_asset_ticker")
    # Handle deprecated cpi_data parameter
    if "cpi_data" in kwargs:
        warnings.warn(
            "The 'cpi_data' parameter is deprecated. Use 'inflation_rate_ticker' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if kwargs["cpi_data"] is not None and inflation_rate_ticker is None:
            inflation_rate_ticker = "CPI"  # Assume CPI ticker if raw data was provided
        kwargs.pop("cpi_data")

    # ========================================================================
    # PHASE 3: Unified Interface - Detect which mode to use
    # ========================================================================
    # Determine if this is a single-ticker or multi-asset backtest
    is_portfolio_mode = allocations is not None
    is_single_ticker_mode = df is not None and ticker

    if is_portfolio_mode and is_single_ticker_mode:
        raise ValueError(
            "Cannot specify both single-ticker parameters (df, ticker) and portfolio parameters (allocations)"
        )

    if not is_portfolio_mode and not is_single_ticker_mode:
        raise ValueError(
            "Must specify either single-ticker parameters (df, ticker) or portfolio parameters (allocations)"
        )

    # Route to appropriate implementation
    if is_portfolio_mode:
        # Multi-asset portfolio backtest
        # Validate required parameters for portfolio mode
        if allocations is None:
            raise ValueError("allocations must be provided for portfolio mode")
        if start_date is None:
            raise ValueError("start_date must be provided for portfolio mode")
        if end_date is None:
            raise ValueError("end_date must be provided for portfolio mode")
        if portfolio_algo is None:
            raise ValueError("portfolio_algo must be provided for portfolio mode")
        if initial_investment is None:
            initial_investment = 1_000_000.0  # Default for portfolio mode

        return run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=initial_investment,
            allow_margin=allow_margin,
            withdrawal_rate_pct=withdrawal_rate_pct,
            withdrawal_frequency_days=withdrawal_frequency_days,
            reference_rate_ticker=reference_rate_ticker,
            risk_free_rate_ticker=risk_free_rate_ticker,
        )

    # ========================================================================
    # PHASE 3: Single-ticker mode
    # ========================================================================

    # Check for any remaining unexpected kwargs
    if kwargs:
        # List all parameters that can be passed to this function, including
        # backwards-compatible aliases (even though they're consumed above)
        valid_params = [
            "df",
            "ticker",
            "initial_qty",
            "allocations",
            "portfolio_algo",
            "start_date",
            "end_date",
            "algo",
            "algo_params",
            "reference_rate_ticker",
            "risk_free_rate_ticker",
            "dividend_series",
            "withdrawal_rate_pct",
            "withdrawal_frequency_days",
            "inflation_rate_ticker",
            "simple_mode",
            "allow_margin",
            "initial_investment",
            "reference_asset_df",
            "risk_free_asset_df",  # Backwards-compatible aliases
            "reference_asset_ticker",
            "risk_free_asset_ticker",  # Backwards-compatible aliases
        ]
        raise TypeError(
            "run_algorithm_backtest() got unexpected keyword argument(s): "
            f"{', '.join(repr(k) for k in kwargs.keys())}. "
            f"Valid parameters are: {', '.join(valid_params)}"
        )

    if df is None or df.empty:
        raise ValueError("Empty price data")

    # Use portfolio backtest for single-ticker backtest
    # Create single-asset portfolio (100% allocation to this ticker)
    # Prepare data
    df_indexed = df.copy()
    df_indexed.index = pd.to_datetime(df_indexed.index).date

    # Set default start/end dates if not provided
    if start_date is None:
        start_date = min(df_indexed.index)
    if end_date is None:
        end_date = max(df_indexed.index)

    # Ensure the data is cached so run_portfolio_backtest can fetch it
    from src.data.asset import Asset

    asset = Asset(ticker, cache_dir=cache_dir)
    asset._save_price_cache(df_indexed)
    # Force use of cache by disabling provider
    asset._provider = None

    # Convert algorithm to portfolio algorithm
    portfolio_algo = _create_portfolio_algorithm_from_single_ticker(
        algo=algo,
        algo_params=algo_params,
        ticker=ticker,
    )

    # Calculate investment amount
    first_idx = min(d for d in df_indexed.index if d >= start_date)
    start_price = float(df_indexed.loc[first_idx, "Close"])

    if initial_qty is not None:
        investment = initial_qty * start_price
    elif initial_investment is not None:
        investment = initial_investment
    else:
        investment = 1_000_000.0  # Default

    # Call portfolio backtest with single asset at 100% allocation
    allocations = {ticker: 1.0}

    # Convert dividend_series to dividend_data format for portfolio backtest
    dividend_data = {ticker: dividend_series} if dividend_series is not None else None

    # Mock the fetcher to return cached data for single-ticker mode
    from unittest.mock import patch

    import src.data.fetcher as fetcher_module

    def mock_get_history(self, ticker_arg, start_date_arg, end_date_arg):
        if ticker_arg == ticker:
            return df_indexed
        return None

    with patch.object(fetcher_module.HistoryFetcher, "get_history", mock_get_history):
        # Call portfolio backtest
        transactions, portfolio_summary = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=investment,
            allow_margin=allow_margin,
            withdrawal_rate_pct=withdrawal_rate_pct,
            withdrawal_frequency_days=withdrawal_frequency_days,
            reference_rate_ticker=reference_rate_ticker,
            risk_free_rate_ticker=risk_free_rate_ticker,
            inflation_rate_ticker=inflation_rate_ticker,
            dividend_data=dividend_data,
        )

    # Map portfolio results to single-ticker format
    summary = _map_portfolio_to_single_ticker_summary(
        portfolio_summary=portfolio_summary,
        ticker=ticker,
        df_indexed=df_indexed,
        start_date=start_date,
        end_date=end_date,
        algo_obj=(
            portfolio_algo.strategies[ticker] if hasattr(portfolio_algo, "strategies") else None
        ),
        transactions=transactions,
    )

    # Update allow_margin in summary
    summary["allow_margin"] = allow_margin

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
            Also used for opportunity cost calculation on negative cash balances
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
    # CUTOVER: Forward all calls to the simpy-based discrete event simulation
    # The simulation.py implementation provides identical functionality with better
    # conceptual clarity through explicit event modeling and coroutine-based processes.
    from src.models.simulation import run_portfolio_simulation

    return run_portfolio_simulation(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=portfolio_algo,
        initial_investment=initial_investment,
        allow_margin=allow_margin,
        withdrawal_rate_pct=withdrawal_rate_pct,
        withdrawal_frequency_days=withdrawal_frequency_days,
        cash_interest_rate_pct=cash_interest_rate_pct,
        dividend_data=dividend_data,
        reference_rate_ticker=reference_rate_ticker,
        risk_free_rate_ticker=risk_free_rate_ticker,
        inflation_rate_ticker=inflation_rate_ticker,
        algo=algo,
        simple_mode=simple_mode,
        **kwargs,
    )
