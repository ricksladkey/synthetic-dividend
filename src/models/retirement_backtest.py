"""Retirement planning backtest with CPI-adjusted withdrawals.

This module extends the standard backtest to support periodic withdrawals
(e.g., monthly income) adjusted for inflation. This simulates retirement
scenarios where you need to withdraw a percentage of the initial portfolio
value each year, adjusted for CPI.

Key features:
- Monthly withdrawals (annual rate / 12)
- CPI-adjusted withdrawal amounts
- Track withdrawal sustainability (did portfolio survive?)
- Calculate "safe withdrawal rate" for given time period
"""

from datetime import date
from typing import Any, Dict, List, Tuple

import pandas as pd

from src.algorithms.base import AlgorithmBase
from src.data.cpi_fetcher import CPIFetcher
from src.models.backtest import Data, run_algorithm_backtest
from src.models.model_types import Transaction


def run_retirement_backtest(
    df: Data,
    ticker: str,
    initial_qty: int,
    start_date: date,
    end_date: date,
    algo_obj: AlgorithmBase,
    annual_withdrawal_rate: float,  # e.g., 0.05 for 5%
    withdrawal_frequency: str = "monthly",  # 'monthly', 'quarterly', 'annual'
    cpi_adjust: bool = True,
    simple_mode: bool = False,
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """Run backtest with periodic CPI-adjusted withdrawals.

    Simulates retirement income by withdrawing a fixed percentage of the initial
    portfolio value each year, adjusted for inflation. This tests whether a
    portfolio can sustain withdrawals over a given time period.

    Args:
        df: Price history DataFrame
        ticker: Asset ticker symbol
        initial_qty: Initial shares owned
        start_date: Backtest start date
        end_date: Backtest end date
        algo_obj: Trading algorithm instance
        annual_withdrawal_rate: Percentage of initial value to withdraw annually (decimal)
        withdrawal_frequency: How often to withdraw ('monthly', 'quarterly', 'annual')
        cpi_adjust: If True, adjust withdrawals for CPI inflation
        simple_mode: If True, disable transaction costs and risk-free rate

    Returns:
        (transactions, summary) tuple where summary includes:
            - All standard backtest metrics
            - total_withdrawn: Total dollars withdrawn
            - withdrawal_count: Number of withdrawal transactions
            - withdrawal_adjusted_return: Return after accounting for withdrawals
            - portfolio_survived: True if portfolio value never hit zero
            - final_purchasing_power: Final value adjusted for inflation

    Example:
        >>> # Test if $1M NVDA position can sustain 5% annual withdrawals (CPI-adjusted)
        >>> df = fetcher.get_history('NVDA', date(2020, 1, 1), date(2024, 12, 31))
        >>> algo = build_algo_from_name('sd8')
        >>> initial_qty = int(1_000_000 / df.iloc[0]['Close'])
        >>> txns, summary = run_retirement_backtest(
        ...     df, 'NVDA', initial_qty, start, end, algo,
        ...     annual_withdrawal_rate=0.05,  # 5% per year
        ...     cpi_adjust=True
        ... )
        >>> print(f"Portfolio survived: {summary['portfolio_survived']}")
        >>> print(f"Total withdrawn: ${summary['total_withdrawn']:,.0f}")
    """
    # Get CPI data if adjusting for inflation
    cpi_adjustment_df = None
    if cpi_adjust:
        try:
            cpi_fetcher = CPIFetcher()
            cpi_adjustment_df = cpi_fetcher.get_cpi(start_date, end_date)
        except Exception as e:
            print(f"Warning: CPI data unavailable: {e}. Proceeding without CPI adjustment.")
            cpi_adjustment_df = None

    # Convert withdrawal frequency to days
    if withdrawal_frequency == "monthly":
        frequency_days = 30
    elif withdrawal_frequency == "quarterly":
        frequency_days = 90
    elif withdrawal_frequency == "annual":
        frequency_days = 365
    else:
        raise ValueError(f"Invalid withdrawal_frequency: {withdrawal_frequency}")

    # Convert annual rate from decimal to percentage for backtest API
    withdrawal_rate_percentage = annual_withdrawal_rate * 100.0

    # Run backtest WITH actual withdrawals
    transactions, summary = run_algorithm_backtest(
        df,
        ticker,
        initial_qty,
        start_date,
        end_date,
        algo_obj,
        withdrawal_rate_pct=withdrawal_rate_percentage,
        withdrawal_frequency_days=frequency_days,
        cpi_data=cpi_adjustment_df,
        simple_mode=simple_mode,
    )

    # The backtest already calculated withdrawal metrics
    # Just add a few retirement-specific fields
    final_value = summary.get("end_value", summary.get("total", 0))

    # Calculate final purchasing power if CPI data available
    if cpi_adjust and cpi_adjustment_df is not None and not cpi_adjustment_df.empty:
        try:
            base_cpi = cpi_adjustment_df.iloc[0]["CPI"]
            final_cpi = cpi_adjustment_df.iloc[-1]["CPI"]
            inflation_factor = final_cpi / base_cpi
            final_purchasing_power = final_value / inflation_factor
        except Exception:
            final_purchasing_power = final_value
    else:
        final_purchasing_power = final_value

    # Add retirement-specific metrics
    summary.update(
        {
            "annual_withdrawal_rate": annual_withdrawal_rate,
            "withdrawal_frequency": withdrawal_frequency,
            "final_value": final_value,  # For consistency
            "final_purchasing_power": final_purchasing_power,
            "portfolio_survived": final_value > 0,
            "cpi_adjusted": cpi_adjust and cpi_adjustment_df is not None,
        }
    )

    return transactions, summary


def calculate_safe_withdrawal_rate(
    df: Data,
    ticker: str,
    initial_qty: int,
    start_date: date,
    end_date: date,
    algo_obj: AlgorithmBase,
    target_final_value_pct: float = 1.0,  # 100% = preserve principal
    cpi_adjust: bool = True,
    simple_mode: bool = False,
    tolerance: float = 0.01,  # 1% tolerance for binary search
) -> float:
    """Calculate maximum sustainable withdrawal rate for a portfolio.

    Uses binary search to find the highest annual withdrawal rate where the
    portfolio survives the entire period and maintains target final value.

    Args:
        df: Price history DataFrame
        ticker: Asset ticker symbol
        initial_qty: Initial shares owned
        start_date: Backtest start date
        end_date: Backtest end date
        algo_obj: Trading algorithm instance
        target_final_value_pct: Minimum final value as percentage of initial (default 1.0 = preserve principal)
        cpi_adjust: If True, adjust withdrawals for CPI inflation
        simple_mode: If True, disable transaction costs
        tolerance: Convergence tolerance for binary search (decimal)

    Returns:
        Maximum safe withdrawal rate (decimal, e.g., 0.05 for 5%)

    Example:
        >>> # What's the max I can withdraw from NVDA over 2020-2024?
        >>> swr = calculate_safe_withdrawal_rate(
        ...     df, 'NVDA', initial_qty, start, end, algo,
        ...     target_final_value_pct=1.0  # Preserve principal
        ... )
        >>> print(f"Safe withdrawal rate: {swr*100:.2f}%")
    """
    # Binary search for maximum withdrawal rate
    low = 0.0
    high = 0.20  # Start search at 20% (unlikely to be sustainable)

    initial_value = df.iloc[0]["Close"] * initial_qty
    target_final_value = initial_value * target_final_value_pct

    while (high - low) > tolerance:
        mid = (low + high) / 2

        # Test this withdrawal rate
        _, summary = run_retirement_backtest(
            df,
            ticker,
            initial_qty,
            start_date,
            end_date,
            algo_obj,
            annual_withdrawal_rate=mid,
            cpi_adjust=cpi_adjust,
            simple_mode=simple_mode,
        )

        # Check if portfolio survived with target final value
        if summary["portfolio_survived"] and summary["final_value"] >= target_final_value:
            # This rate is sustainable, try higher
            low = mid
        else:
            # This rate depleted portfolio, try lower
            high = mid

    return low


def compare_withdrawal_strategies(
    df: Data,
    ticker: str,
    initial_investment: float,
    start_date: date,
    end_date: date,
    algorithms: Dict[str, AlgorithmBase],
    withdrawal_rates: List[float],
    cpi_adjust: bool = True,
) -> pd.DataFrame:
    """Compare multiple algorithms across various withdrawal rates.

    Tests each algorithm at each withdrawal rate to find which strategy
    best sustains retirement income.

    Args:
        df: Price history DataFrame
        ticker: Asset ticker symbol
        initial_investment: Starting portfolio value in dollars
        start_date: Backtest start date
        end_date: Backtest end date
        algorithms: Dict of {name: algorithm_instance}
        withdrawal_rates: List of annual withdrawal rates to test (decimals)
        cpi_adjust: If True, adjust withdrawals for CPI

    Returns:
        DataFrame with columns: [Algorithm, WithdrawalRate, FinalValue, TotalWithdrawn, Survived]

    Example:
        >>> algos = {
        ...     'Buy-Hold': build_algo_from_name('buy-and-hold'),
        ...     'SD8': build_algo_from_name('sd8'),
        ...     'ATH-Only': build_algo_from_name('sd-ath-only-9.05,50')
        ... }
        >>> rates = [0.03, 0.04, 0.05, 0.06, 0.07]
        >>> results = compare_withdrawal_strategies(df, 'NVDA', 1_000_000, start, end, algos, rates)
        >>> print(results)
    """
    results = []

    first_price = df.iloc[0]["Close"]
    initial_qty = int(initial_investment / first_price)

    for algo_name, algo_obj in algorithms.items():
        for rate in withdrawal_rates:
            _, summary = run_retirement_backtest(
                df,
                ticker,
                initial_qty,
                start_date,
                end_date,
                algo_obj,
                annual_withdrawal_rate=rate,
                cpi_adjust=cpi_adjust,
                simple_mode=True,
            )

            results.append(
                {
                    "Algorithm": algo_name,
                    "WithdrawalRate": f"{rate*100:.1f}%",
                    "FinalValue": summary["final_value"],
                    "TotalWithdrawn": summary["total_withdrawn"],
                    "Survived": summary["portfolio_survived"],
                    "FinalPurchasingPower": summary["final_purchasing_power"],
                }
            )

    return pd.DataFrame(results)
