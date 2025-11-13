"""
Discrete event simulation framework for portfolio backtesting using simpy.

This module provides an alternative implementation of portfolio backtesting using
simpy's discrete event simulation framework. It maintains the same API as the
traditional loop-based backtest.py but models the system as a series of events
and processes over time.

Key differences from loop-based approach:
- Time advances through discrete events rather than date iteration
- Portfolio algorithms run as continuous processes
- Transactions, withdrawals, and dividends are scheduled events
- More flexible for modeling complex timing dependencies
"""

import math
import warnings
from datetime import date, timedelta
from typing import Any, Dict, Generator, List, Optional, Tuple, Union, cast

import pandas as pd
import simpy

# Import algorithm classes from dedicated package
from src.algorithms import PortfolioAlgorithmBase
from src.models.backtest_utils import calculate_time_weighted_average_holdings
from src.models.model_types import AssetState, Transaction


def run_portfolio_simulation(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    portfolio_algo: Union[PortfolioAlgorithmBase, str],
    initial_investment: float = 1_000_000.0,
    allow_margin: bool = False,  # Default: no margin (realistic retail mode)
    withdrawal_rate_pct: float = 0.0,
    withdrawal_frequency_days: int = 30,
    cash_interest_rate_pct: float = 0.0,
    dividend_data: Optional[Dict[str, pd.Series]] = None,
    reference_rate_ticker: Optional[str] = None,
    risk_free_rate_ticker: Optional[str] = None,
    inflation_rate_ticker: Optional[str] = None,
    # Legacy compatibility parameters (deprecated, ignored with warnings)
    algo: Optional[Union[object, str]] = None,
    simple_mode: bool = False,
    **kwargs: Any,
) -> Tuple[List[Transaction], Dict[str, Any]]:
    """
    Execute portfolio simulation with shared cash pool using discrete event simulation.

    This function uses simpy to model the portfolio as a discrete event system:
    - Time advances through scheduled events (transactions, withdrawals, dividends)
    - Portfolio algorithm runs as a continuous process monitoring market conditions
    - Events are triggered at specific times based on market data and schedules

    Args:
        allocations: Dict mapping ticker → target allocation (must sum to 1.0)
        start_date: Simulation start date
        end_date: Simulation end date
        portfolio_algo: Portfolio algorithm or string name
        initial_investment: Total starting capital
        allow_margin: Whether to allow negative bank balance
        withdrawal_rate_pct: Annual withdrawal rate (0-100)
        withdrawal_frequency_days: Days between withdrawals (default 30)
        cash_interest_rate_pct: Annual interest rate on cash reserves (default 0.0)
        dividend_data: Optional dict mapping ticker → pandas Series of dividend payments.
                      If None (default), dividends will be auto-fetched for each ticker.
        reference_rate_ticker: Optional ticker for reference benchmark
        risk_free_rate_ticker: Optional ticker for risk-free asset
        inflation_rate_ticker: Optional ticker for inflation data
        algo: DEPRECATED - Use portfolio_algo instead
        simple_mode: DEPRECATED - No longer used
        **kwargs: DEPRECATED - Ignored legacy parameters

    Returns:
        Tuple of (all_transactions, portfolio_summary)
    """
    # Handle legacy parameters (same as backtest.py)
    if algo is not None:
        warnings.warn(
            "The 'algo' parameter is deprecated. Use 'portfolio_algo' instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    if "simple_mode" in kwargs:
        simple_mode = kwargs.pop("simple_mode")
        if simple_mode:
            cash_interest_rate_pct = 0.0

    if kwargs:
        ignored = ", ".join(kwargs.keys())
        warnings.warn(f"Ignored deprecated parameters: {ignored}", DeprecationWarning, stacklevel=2)

    # Validate allocations
    total_allocation = sum(allocations.values())
    if abs(total_allocation - 1.0) > 0.01:
        raise ValueError(f"Allocations must sum to 1.0, got {total_allocation:.3f}")

    # Handle string interface for portfolio_algo
    if isinstance(portfolio_algo, str):
        from src.algorithms.portfolio_factory import build_portfolio_algo_from_name

        portfolio_algo = build_portfolio_algo_from_name(portfolio_algo, allocations)

    # Validate portfolio_algo type
    if not isinstance(portfolio_algo, PortfolioAlgorithmBase):
        raise TypeError(
            f"portfolio_algo must be PortfolioAlgorithmBase or string, got {type(portfolio_algo).__name__}"
        )

    # Fetch price data (same as backtest.py)
    from src.data.fetcher import HistoryFetcher

    fetcher = HistoryFetcher()
    price_data: Dict[str, pd.DataFrame] = {}

    # Separate actual tickers from CASH reserve
    real_tickers = [t for t in allocations.keys() if t != "CASH"]

    print(f"Fetching data for {len(real_tickers)} assets...")
    for ticker in real_tickers:
        print(f"  - {ticker}...", end=" ")
        df = fetcher.get_history(ticker, start_date, end_date)
        if df is None or df.empty:
            raise ValueError(f"No data available for {ticker}")
        price_data[ticker] = df
        print(f"OK ({len(df)} days)")

    # If CASH allocation exists, fetch BIL data for sweep account interest
    has_cash_allocation = "CASH" in allocations
    bil_price_data = None

    if has_cash_allocation:
        cash_pct = allocations["CASH"] * 100
        print(f"  - CASH: {cash_pct:.1f}% reserve (sweep account earning BIL yields)")

        # Fetch BIL price data for interest calculations
        print(f"  - BIL (sweep account yields)...", end=" ")
        bil_df = fetcher.get_history("BIL", start_date, end_date)
        if bil_df is not None and not bil_df.empty:
            bil_price_data = bil_df
            print(f"OK ({len(bil_df)} days)")
        else:
            print("WARNING: No BIL data, CASH will earn 0% interest")

    # Auto-fetch dividend data if not provided
    if dividend_data is None:
        print(f"Auto-fetching dividend data for {len(real_tickers)} assets...")
        from src.data.asset import Asset

        dividend_data_auto: Dict[str, pd.Series] = {}
        for ticker in real_tickers:  # Skip CASH
            print(f"  - {ticker} dividends...", end=" ")
            try:
                asset = Asset(ticker)
                div_series = asset.get_dividends(start_date, end_date)
                if div_series is not None and not div_series.empty:
                    # Normalize timezone-aware timestamps to naive dates
                    div_series_copy = div_series.copy()
                    div_series_copy.index = pd.to_datetime(div_series_copy.index).tz_localize(None)
                    dividend_data_auto[ticker] = div_series_copy
                    print(f"OK ({len(div_series_copy)} dividends)")
                else:
                    print("None")
            except Exception as e:
                print(f"ERROR: {e}")

        # If CASH allocation exists, fetch BIL dividends for interest
        if has_cash_allocation:
            print(f"  - BIL (CASH interest) dividends...", end=" ")
            try:
                asset = Asset("BIL")
                div_series = asset.get_dividends(start_date, end_date)
                if div_series is not None and not div_series.empty:
                    div_series_copy = div_series.copy()
                    div_series_copy.index = pd.to_datetime(div_series_copy.index).tz_localize(None)
                    dividend_data_auto["CASH"] = div_series_copy  # Store as CASH dividends
                    print(
                        f"OK ({len(div_series_copy)} payments, ~{div_series.sum():.2f}% annual yield)"
                    )
                else:
                    print("None")
            except Exception as e:
                print(f"ERROR: {e}")

        dividend_data = dividend_data_auto if dividend_data_auto else None

    # Find common trading dates
    all_dates: set[date] = set()
    for df in price_data.values():
        dates = set(pd.to_datetime(df.index).date)
        all_dates = all_dates.intersection(dates) if all_dates else dates

    common_dates = sorted([d for d in all_dates if start_date <= d <= end_date])
    if not common_dates:
        raise ValueError("No common trading dates across all assets")

    print(f"Common trading days: {len(common_dates)} ({common_dates[0]} to {common_dates[-1]})")

    # Index price data by date
    price_data_indexed: Dict[str, pd.DataFrame] = {}
    for ticker, df in price_data.items():
        df_copy = df.copy()
        df_copy.index = pd.to_datetime(df_copy.index).date
        price_data_indexed[ticker] = df_copy

    # Fetch reference, risk-free, and inflation data (same logic as backtest.py)
    reference_returns: Dict[date, float] = {}
    risk_free_returns: Dict[date, float] = {}
    cumulative_inflation: Dict[date, float] = {}
    reference_data: Optional[pd.DataFrame] = None

    if reference_rate_ticker:
        print(f"Fetching reference benchmark ({reference_rate_ticker})...", end=" ")
        ref_data = fetcher.get_history(reference_rate_ticker, start_date, end_date)
        if ref_data is not None and not ref_data.empty:
            print(f"OK ({len(ref_data)} days)")
            ref_indexed = ref_data.copy()
            ref_indexed.index = pd.to_datetime(ref_indexed.index).date
            reference_data = ref_indexed  # Store for baseline calculation
            if "Close" in ref_indexed.columns:
                close_prices = ref_indexed["Close"].values
                ref_dates = list(ref_indexed.index)
                for i in range(1, len(close_prices)):
                    prev_price = float(close_prices[i - 1])
                    curr_price = float(close_prices[i])
                    if prev_price > 0:
                        reference_returns[ref_dates[i]] = (curr_price - prev_price) / prev_price
        else:
            print("WARN: No data available, skipping baseline calculation")

    if risk_free_rate_ticker:
        print(f"Fetching risk-free asset ({risk_free_rate_ticker})...", end=" ")
        rf_data = fetcher.get_history(risk_free_rate_ticker, start_date, end_date)
        if rf_data is not None and not rf_data.empty:
            print(f"OK ({len(rf_data)} days)")
            rf_indexed = rf_data.copy()
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

    if inflation_rate_ticker:
        print(f"Fetching inflation data ({inflation_rate_ticker})...", end=" ")
        infl_data = fetcher.get_history(inflation_rate_ticker, start_date, end_date)
        if infl_data is not None and not infl_data.empty:
            print(f"OK ({len(infl_data)} days)")
            infl_indexed = infl_data.copy()
            infl_indexed.index = pd.to_datetime(infl_indexed.index).date
            value_col = "Close" if "Close" in infl_indexed.columns else "Value"
            if value_col in infl_indexed.columns:
                infl_values = infl_indexed[value_col].values
                infl_dates = list(infl_indexed.index)
                if common_dates[0] in infl_dates:
                    start_cpi_idx = infl_dates.index(common_dates[0])
                    start_cpi = float(infl_values[start_cpi_idx])
                    for i, d in enumerate(infl_dates):
                        if d >= common_dates[0]:
                            curr_cpi = float(infl_values[i])
                            cumulative_inflation[d] = curr_cpi / start_cpi if start_cpi > 0 else 1.0
        else:
            print("WARN: No data available, skipping inflation adjustment")

    # Create simulation environment
    env = simpy.Environment()

    # Initialize simulation state
    sim_state = SimulationState(
        env=env,
        allocations=allocations,
        price_data=price_data_indexed,
        common_dates=common_dates,
        initial_investment=initial_investment,
        allow_margin=allow_margin,
        withdrawal_rate_pct=withdrawal_rate_pct,
        withdrawal_frequency_days=withdrawal_frequency_days,
        cash_interest_rate_pct=cash_interest_rate_pct,
        dividend_data=dividend_data,
        reference_returns=reference_returns,
        risk_free_returns=risk_free_returns,
        reference_rate_ticker=reference_rate_ticker,
        risk_free_rate_ticker=risk_free_rate_ticker,
        simple_mode=simple_mode,
        portfolio_algo=portfolio_algo,
        reference_data=reference_data,
        cumulative_inflation=cumulative_inflation,
        inflation_rate_ticker=inflation_rate_ticker,
        bil_price_data=bil_price_data,
    )

    # Start the simulation processes
    env.process(market_process(env, sim_state, portfolio_algo))

    # Schedule dividend events
    if dividend_data:
        env.process(dividend_process(env, sim_state))

    # Run simulation
    print("\nRunning simulation...")
    env.run(until=len(common_dates))  # Run for number of trading days
    print("Simulation complete.\n")

    # Build results (same format as backtest.py)
    return sim_state.build_results()


class SimulationState:
    """Holds the state of the portfolio simulation."""

    def __init__(self, env: simpy.Environment, **kwargs):
        self.env = env
        self.allocations = kwargs["allocations"]
        self.price_data = kwargs["price_data"]
        self.common_dates = kwargs["common_dates"]
        self.initial_investment = kwargs["initial_investment"]
        self.allow_margin = kwargs["allow_margin"]
        self.withdrawal_rate_pct = kwargs["withdrawal_rate_pct"]
        self.withdrawal_frequency_days = kwargs["withdrawal_frequency_days"]
        self.cash_interest_rate_pct = kwargs["cash_interest_rate_pct"]
        self.dividend_data = kwargs["dividend_data"]
        self.reference_returns = kwargs["reference_returns"]
        self.risk_free_returns = kwargs["risk_free_returns"]
        self.reference_rate_ticker = kwargs["reference_rate_ticker"]
        self.risk_free_rate_ticker = kwargs["risk_free_rate_ticker"]
        self.simple_mode = kwargs["simple_mode"]
        self.portfolio_algo = kwargs.get("portfolio_algo", None)
        self.reference_data = kwargs.get("reference_data", None)
        self.cumulative_inflation = kwargs.get("cumulative_inflation", {})
        self.inflation_rate_ticker = kwargs.get("inflation_rate_ticker", None)
        self.bil_price_data = kwargs.get("bil_price_data", None)

        # Separate real tickers from CASH
        self.real_tickers = [t for t in self.allocations.keys() if t != "CASH"]

        # Initialize portfolio state
        self.shared_bank = self.initial_investment
        self.holdings: Dict[str, int] = {}
        self.all_transactions: List[Transaction] = []

        # Track daily values
        self.daily_portfolio_values: Dict[date, float] = {}
        self.daily_bank_values: Dict[date, float] = {}
        self.daily_asset_values: Dict[str, Dict[date, float]] = {
            ticker: {} for ticker in self.allocations.keys()
        }
        self.daily_withdrawals: Dict[date, float] = {}

        # Withdrawal tracking
        self.total_withdrawn = 0.0
        self.withdrawal_count = 0
        self.last_withdrawal_date = None
        self.base_withdrawal_amount = 0.0

        # Calculate withdrawal amounts if enabled
        if self.withdrawal_rate_pct > 0:
            annual_withdrawal = self.initial_investment * (self.withdrawal_rate_pct / 100.0)
            self.base_withdrawal_amount = annual_withdrawal * (
                self.withdrawal_frequency_days / 365.25
            )

        # Interest tracking
        self.total_interest_earned = 0.0
        self.opportunity_cost_total = 0.0
        self.daily_interest_rate = (
            (self.cash_interest_rate_pct / 100.0) / 365.25
            if self.cash_interest_rate_pct > 0
            else 0.0
        )
        self.daily_reference_rate_fallback = 0.00027 if self.reference_rate_ticker else 0.0

        # Dividend tracking
        self.total_dividends_by_asset = {ticker: 0.0 for ticker in self.allocations}
        self.dividend_payment_count_by_asset = {ticker: 0 for ticker in self.allocations}
        self.holdings_history = {
            ticker: [(self.common_dates[0], 0)] for ticker in self.real_tickers
        }

        # Bank balance tracking
        self.bank_min = self.shared_bank
        self.bank_max = self.shared_bank

        # Initial purchase
        print("\nInitial purchase:")
        for ticker, alloc_pct in self.allocations.items():
            # Skip CASH - it stays in the bank
            if ticker == "CASH":
                cash_reserve = self.initial_investment * alloc_pct
                print(f"  {ticker}: ${cash_reserve:,.2f} reserve (kept in bank)")
                continue

            first_price = self.price_data[ticker].loc[self.common_dates[0], "Close"].item()
            qty = int((self.initial_investment * alloc_pct) / first_price)
            cost = qty * first_price
            self.holdings[ticker] = qty
            self.shared_bank -= cost
            print(f"  {ticker}: {qty} shares × ${first_price:.2f} = ${cost:,.2f}")

            self.all_transactions.append(
                Transaction(
                    transaction_date=self.common_dates[0],
                    action="BUY",
                    qty=qty,
                    price=first_price,
                    ticker=ticker,
                    notes="Initial purchase",
                )
            )

            # Update holdings history
            self.holdings_history[ticker].append((self.common_dates[0], qty))

        print(f"Initial bank balance: ${self.shared_bank:,.2f}\n")

    def get_current_date(self) -> date:
        """Get current simulation date based on environment time."""
        day_index = int(self.env.now)
        return cast(date, self.common_dates[min(day_index, len(self.common_dates) - 1)])

    def execute_transaction(self, tx: Transaction, ticker: str) -> None:
        """Execute a transaction against the portfolio state."""
        current_date = self.get_current_date()

        # Fill in execution details
        tx.transaction_date = current_date
        tx.ticker = ticker  # Ensure ticker is set correctly
        if tx.price == 0.0:
            tx.price = self.price_data[tx.ticker].loc[current_date, "Close"].item()

        ticker = tx.ticker
        if tx.action.upper() == "BUY":
            cost = tx.qty * tx.price
            if self.shared_bank >= cost or self.allow_margin:
                self.holdings[ticker] += tx.qty
                self.shared_bank -= cost
                self.all_transactions.append(tx)
                # Update holdings history
                self.holdings_history[ticker].append((current_date, self.holdings[ticker]))
            else:
                # Insufficient cash - skip transaction
                skipped_tx = Transaction(
                    transaction_date=current_date,
                    action="SKIP BUY",
                    qty=tx.qty,
                    price=tx.price,
                    ticker=ticker,
                    notes=f"{tx.notes}, insufficient cash: ${self.shared_bank:.2f} < ${cost:.2f}",
                )
                self.all_transactions.append(skipped_tx)

        elif tx.action.upper() == "SELL":
            if self.holdings[ticker] >= tx.qty:
                proceeds = tx.qty * tx.price
                self.holdings[ticker] -= tx.qty
                self.shared_bank += proceeds
                self.all_transactions.append(tx)
                # Update holdings history
                self.holdings_history[ticker].append((current_date, self.holdings[ticker]))
            else:
                # Insufficient holdings - skip transaction
                skipped_tx = Transaction(
                    transaction_date=current_date,
                    action="SKIP SELL",
                    qty=tx.qty,
                    price=tx.price,
                    ticker=ticker,
                    notes=f"{tx.notes}, insufficient holdings: {self.holdings[ticker]} < {tx.qty}",
                )
                self.all_transactions.append(skipped_tx)

    def process_daily_interest(self) -> None:
        """Process daily interest and opportunity cost."""
        current_date = self.get_current_date()

        # Apply opportunity cost on negative balance
        if self.shared_bank < 0 and not self.simple_mode:
            daily_return = self.reference_returns.get(
                current_date, self.daily_reference_rate_fallback
            )
            opportunity_cost_today = abs(self.shared_bank) * daily_return
            self.shared_bank -= opportunity_cost_today
            self.opportunity_cost_total += opportunity_cost_today

        # Accrue interest on positive balance
        if self.shared_bank > 0:
            if self.risk_free_returns and current_date in self.risk_free_returns:
                daily_return = self.risk_free_returns[current_date]
                daily_interest = self.shared_bank * daily_return
            elif self.daily_interest_rate > 0:
                daily_interest = self.shared_bank * self.daily_interest_rate
            else:
                daily_interest = 0.0

            if daily_interest > 0:
                self.shared_bank += daily_interest
                self.total_interest_earned += daily_interest

    def record_daily_values(self) -> None:
        """Record daily portfolio and bank values."""
        current_date = self.get_current_date()

        # Calculate current asset values
        total_asset_value = 0.0
        for ticker in self.real_tickers:
            current_price = self.price_data[ticker].loc[current_date, "Close"].item()
            asset_value = self.holdings[ticker] * current_price
            self.daily_asset_values[ticker][current_date] = asset_value
            total_asset_value += asset_value

        # Record values
        self.daily_portfolio_values[current_date] = self.shared_bank + total_asset_value
        self.daily_bank_values[current_date] = self.shared_bank

        # Update bank min/max
        self.bank_min = min(self.bank_min, self.shared_bank)
        self.bank_max = max(self.bank_max, self.shared_bank)

    def build_results(self) -> Tuple[List[Transaction], Dict[str, Any]]:
        """Build final results in the same format as backtest.py."""
        final_date = self.common_dates[-1]
        final_asset_value = sum(
            self.holdings[ticker] * self.price_data[ticker].loc[final_date, "Close"].item()
            for ticker in self.real_tickers
        )
        final_total_value = self.shared_bank + final_asset_value

        # Calculate returns
        total_return_pct = (
            (final_total_value - self.initial_investment) / self.initial_investment
        ) * 100
        days = (final_date - self.common_dates[0]).days
        years = days / 365.25
        annualized_return_pct = (
            (((final_total_value / self.initial_investment) ** (1 / years)) - 1) * 100
            if years > 0
            else 0
        )

        # Build per-asset summaries
        asset_results = {}
        for ticker, alloc_pct in self.allocations.items():
            if ticker == "CASH":
                # CASH is held in bank, not as asset holdings
                asset_results[ticker] = {
                    "allocation": alloc_pct,
                    "initial_investment": self.initial_investment * alloc_pct,
                    "final_holdings": 0,
                    "final_price": 1.0,
                    "final_value": 0.0,
                    "total_return": 0.0,  # Bank balance is tracked separately
                }
            else:
                final_price = self.price_data[ticker].loc[final_date, "Close"].item()
                final_value = self.holdings[ticker] * final_price
                initial_value = self.initial_investment * alloc_pct

                asset_results[ticker] = {
                    "allocation": alloc_pct,
                    "initial_investment": initial_value,
                    "final_holdings": self.holdings[ticker],
                    "final_price": final_price,
                    "final_value": final_value,
                    "total_return": (
                        ((final_value - initial_value) / initial_value) * 100
                        if initial_value > 0
                        else 0
                    ),
                }

        # Build portfolio summary
        portfolio_summary = {
            "total_final_value": final_total_value,
            "final_bank": self.shared_bank,
            "final_asset_value": final_asset_value,
            "total_return": total_return_pct,
            "annualized_return": annualized_return_pct,
            "initial_investment": self.initial_investment,
            "start_date": self.common_dates[0],
            "end_date": final_date,
            "trading_days": len(self.common_dates),
            "assets": asset_results,
            "allocations": self.allocations,
            "daily_values": self.daily_portfolio_values,
            "daily_bank_values": self.daily_bank_values,
            "daily_asset_values": self.daily_asset_values,
            "daily_withdrawals": self.daily_withdrawals,
            "transaction_count": len(
                [
                    tx
                    for tx in self.all_transactions
                    if "SKIP" not in tx.action and tx.action != "WITHDRAWAL"
                ]
            ),
            "skipped_count": len([tx for tx in self.all_transactions if "SKIP" in tx.action]),
            "total_withdrawn": self.total_withdrawn,
            "withdrawal_count": self.withdrawal_count,
            "withdrawal_rate_pct": self.withdrawal_rate_pct,
            "cash_interest_earned": self.total_interest_earned,
            "opportunity_cost": self.opportunity_cost_total,
            "cash_interest_rate_pct": self.cash_interest_rate_pct,
            "risk_free_rate_ticker": self.risk_free_rate_ticker,
            "total_dividends_by_asset": self.total_dividends_by_asset,
            "total_dividends": sum(self.total_dividends_by_asset.values()),
            "dividend_payment_count_by_asset": self.dividend_payment_count_by_asset,
            "bank_min": self.bank_min,
            "bank_max": self.bank_max,
        }

        # Compute baseline (buy-and-hold reference benchmark) if reference data provided
        if self.reference_data is not None and not self.reference_data.empty:
            first_date = self.common_dates[0]
            ref_start_price = float(self.reference_data.loc[first_date, "Close"])
            ref_end_price = float(self.reference_data.loc[final_date, "Close"])

            # Calculate baseline buy-and-hold return for reference benchmark
            ref_shares = self.initial_investment / ref_start_price
            ref_end_value = ref_shares * ref_end_price
            ref_total_return = (ref_end_value - self.initial_investment) / self.initial_investment

            if years > 0:
                ref_annualized = (ref_end_value / self.initial_investment) ** (1.0 / years) - 1.0
            else:
                ref_annualized = 0.0

            baseline_summary = {
                "ticker": self.reference_rate_ticker,
                "start_date": first_date,
                "end_date": final_date,
                "start_price": ref_start_price,
                "end_price": ref_end_price,
                "start_value": self.initial_investment,
                "end_value": ref_end_value,
                "total": ref_end_value,
                "total_return": ref_total_return,
                "annualized": ref_annualized,
            }

            # Alpha = portfolio return - benchmark return
            volatility_alpha = (
                final_total_value - self.initial_investment
            ) / self.initial_investment - ref_total_return

            portfolio_summary["baseline"] = baseline_summary
            portfolio_summary["volatility_alpha"] = volatility_alpha
            portfolio_summary["alpha_pct"] = volatility_alpha * 100.0
        else:
            portfolio_summary["baseline"] = None
            portfolio_summary["volatility_alpha"] = None

        # Compute inflation-adjusted (real) returns if inflation data provided
        if self.cumulative_inflation and final_date in self.cumulative_inflation:
            inflation_multiplier = self.cumulative_inflation[final_date]
            real_final_value = final_total_value / inflation_multiplier
            real_total_return_pct = (
                (real_final_value - self.initial_investment) / self.initial_investment * 100.0
            )

            if years > 0:
                real_annualized_pct = (real_final_value / self.initial_investment) ** (
                    1.0 / years
                ) - 1.0
                real_annualized_pct *= 100.0
            else:
                real_annualized_pct = 0.0

            portfolio_summary["inflation_rate_ticker"] = self.inflation_rate_ticker
            portfolio_summary["cumulative_inflation"] = (inflation_multiplier - 1.0) * 100.0
            portfolio_summary["real_final_value"] = real_final_value
            portfolio_summary["real_total_return"] = real_total_return_pct
            portfolio_summary["real_annualized_return"] = real_annualized_pct
        else:
            portfolio_summary["inflation_rate_ticker"] = None
            portfolio_summary["cumulative_inflation"] = None
            portfolio_summary["real_final_value"] = None
            portfolio_summary["real_total_return"] = None
            portfolio_summary["real_annualized_return"] = None

        # Extract algorithm-specific stats (final_stack_size, total_volatility_alpha)
        # These are used by SyntheticDividendAlgorithm and tests
        from src.algorithms import PerAssetPortfolioAlgorithm
        from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm

        if self.portfolio_algo and isinstance(self.portfolio_algo, PerAssetPortfolioAlgorithm):
            # For per-asset portfolio algorithms, extract stats from the first SyntheticDividendAlgorithm
            for ticker, algo in self.portfolio_algo.strategies.items():
                if isinstance(algo, SyntheticDividendAlgorithm):
                    portfolio_summary["final_stack_size"] = getattr(algo, "buyback_stack_count", 0)
                    portfolio_summary["total_volatility_alpha"] = getattr(
                        algo, "total_volatility_alpha", 0.0
                    )
                    break  # Only use the first one (for single-ticker tests)
            else:
                # No SyntheticDividendAlgorithm found
                portfolio_summary["final_stack_size"] = 0
                portfolio_summary["total_volatility_alpha"] = 0.0
        else:
            # For other portfolio algorithms, no stack
            portfolio_summary["final_stack_size"] = 0
            portfolio_summary["total_volatility_alpha"] = 0.0

        return self.all_transactions, portfolio_summary


def market_process(
    env: simpy.Environment, state: SimulationState, portfolio_algo: PortfolioAlgorithmBase
) -> Generator[simpy.events.Event, Any, Any]:
    """Main market process that advances through trading days."""
    # Initialize per-asset algorithms if needed
    from src.algorithms import PerAssetPortfolioAlgorithm

    if isinstance(portfolio_algo, PerAssetPortfolioAlgorithm):
        print("Initializing per-asset algorithms...")
        for ticker, algo in portfolio_algo.strategies.items():
            if hasattr(algo, "on_new_holdings"):
                first_price = state.price_data[ticker].loc[state.common_dates[0], "Close"].item()
                algo.on_new_holdings(state.holdings[ticker], first_price)
                print(
                    f"  {ticker}: initialized with {state.holdings[ticker]} shares @ ${first_price:.2f}"
                )
        print()

    # Process each trading day
    for day_index in range(len(state.common_dates)):
        current_date = state.common_dates[day_index]

        # Build current state for algorithm
        assets = {}
        prices = {}
        history = {}

        for ticker in state.real_tickers:
            current_price = state.price_data[ticker].loc[current_date, "Close"].item()
            assets[ticker] = AssetState(
                ticker=ticker, holdings=state.holdings[ticker], price=current_price
            )
            prices[ticker] = state.price_data[ticker].loc[current_date]
            history[ticker] = state.price_data[ticker][
                state.price_data[ticker].index < current_date
            ]

        # Ask portfolio algorithm for transactions
        transactions_by_ticker = portfolio_algo.on_portfolio_day(
            date_=current_date,
            assets=assets,
            bank=state.shared_bank,
            prices=prices,
            history=history,
        )

        # Execute transactions
        for ticker, txns in transactions_by_ticker.items():
            for tx in txns:
                state.execute_transaction(tx, ticker)

        # Process withdrawals (if enabled and due)
        if state.base_withdrawal_amount > 0:
            # Check if withdrawal is due
            days_since_last = None
            if state.last_withdrawal_date is None:
                # First withdrawal happens after withdrawal_frequency_days from start
                days_since_last = (current_date - state.common_dates[0]).days
            else:
                days_since_last = (current_date - state.last_withdrawal_date).days

            if days_since_last >= state.withdrawal_frequency_days:
                # Withdraw from shared bank (portfolio-level, not per-asset)
                withdrawal_amount = state.base_withdrawal_amount

                # Check if we have enough cash
                if state.shared_bank >= withdrawal_amount:
                    # Simple case: withdraw from cash
                    actual_withdrawal = withdrawal_amount
                    state.shared_bank -= actual_withdrawal
                    withdrawal_notes = f"${actual_withdrawal:.2f} withdrawn from cash, bank=${state.shared_bank:.2f}"
                else:
                    # Need to sell assets to meet withdrawal
                    # First, withdraw all available cash
                    cash_available = max(0, state.shared_bank)
                    shortfall = withdrawal_amount - cash_available

                    # Sell assets proportionally to raise cash for shortfall
                    total_asset_value = sum(
                        state.holdings[t] * state.price_data[t].loc[current_date, "Close"].item()
                        for t in state.real_tickers
                    )

                    if total_asset_value > 0:
                        # Sell proportionally from each asset
                        for ticker in state.real_tickers:
                            if state.holdings[ticker] > 0:
                                asset_value = (
                                    state.holdings[ticker]
                                    * state.price_data[ticker].loc[current_date, "Close"].item()
                                )
                                proportion = asset_value / total_asset_value
                                amount_to_raise = shortfall * proportion
                                shares_to_sell = math.ceil(
                                    amount_to_raise
                                    / state.price_data[ticker].loc[current_date, "Close"].item()
                                )

                                if shares_to_sell > 0:
                                    shares_to_sell = min(shares_to_sell, state.holdings[ticker])
                                    proceeds = (
                                        shares_to_sell
                                        * state.price_data[ticker].loc[current_date, "Close"].item()
                                    )
                                    state.holdings[ticker] -= shares_to_sell
                                    state.shared_bank += proceeds

                                    # Record forced sale
                                    state.all_transactions.append(
                                        Transaction(
                                            transaction_date=current_date,
                                            action="SELL",
                                            qty=shares_to_sell,
                                            price=state.price_data[ticker]
                                            .loc[current_date, "Close"]
                                            .item(),
                                            ticker=ticker,
                                            notes=f"Forced sale to fund withdrawal (raised ${proceeds:.2f})",
                                        )
                                    )

                    # Now withdraw what we can (cash available + proceeds from sales)
                    actual_withdrawal = min(withdrawal_amount, state.shared_bank)
                    state.shared_bank -= actual_withdrawal
                    withdrawal_notes = f"${actual_withdrawal:.2f} withdrawn (${cash_available:.2f} cash + ${actual_withdrawal - cash_available:.2f} from asset sales), bank=${state.shared_bank:.2f}"

                state.total_withdrawn += actual_withdrawal
                state.withdrawal_count += 1
                state.last_withdrawal_date = current_date

                # Record withdrawal transaction
                state.all_transactions.append(
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
                state.daily_withdrawals[current_date] = actual_withdrawal

        # Process daily interest/opportunity cost
        state.process_daily_interest()

        # Record daily values
        state.record_daily_values()

        # Advance to next day
        if day_index < len(state.common_dates) - 1:
            yield env.timeout(1)


def withdrawal_process(
    env: simpy.Environment, state: SimulationState, base_amount: float, frequency_days: int
) -> Generator[simpy.events.Event, Any, Any]:
    """Process that handles periodic withdrawals."""
    withdrawal_number = 1
    while True:
        # Find the next withdrawal day based on calendar days, not simulation time
        start_date = state.common_dates[0]
        current_day_index = int(env.now)
        current_date = (
            state.common_dates[current_day_index]
            if current_day_index < len(state.common_dates)
            else state.common_dates[-1]
        )

        # Calculate days since start or last withdrawal
        if state.last_withdrawal_date is None:
            days_since_last = (current_date - start_date).days
        else:
            days_since_last = (current_date - state.last_withdrawal_date).days

        # If withdrawal is due, do it now
        if days_since_last >= frequency_days:
            # Perform withdrawal
            withdrawal_amount = base_amount

            if state.shared_bank >= withdrawal_amount:
                actual_withdrawal = withdrawal_amount
                state.shared_bank -= actual_withdrawal
                notes = (
                    f"${actual_withdrawal:.2f} withdrawn from cash, bank=${state.shared_bank:.2f}"
                )
            else:
                # Need to sell assets
                cash_available = max(0, state.shared_bank)
                shortfall = withdrawal_amount - cash_available

                total_asset_value = sum(
                    state.holdings[t] * state.price_data[t].loc[current_date, "Close"].item()
                    for t in state.real_tickers
                )

                if total_asset_value > 0:
                    for ticker in state.real_tickers:
                        if state.holdings[ticker] > 0:
                            asset_value = (
                                state.holdings[ticker]
                                * state.price_data[ticker].loc[current_date, "Close"].item()
                            )
                            proportion = asset_value / total_asset_value
                            amount_to_raise = shortfall * proportion
                            shares_to_sell = max(
                                1,
                                int(
                                    amount_to_raise
                                    / state.price_data[ticker].loc[current_date, "Close"].item()
                                ),
                            )

                            if shares_to_sell > 0:
                                shares_to_sell = min(shares_to_sell, state.holdings[ticker])
                                proceeds = (
                                    shares_to_sell
                                    * state.price_data[ticker].loc[current_date, "Close"].item()
                                )
                                state.holdings[ticker] -= shares_to_sell
                                state.shared_bank += proceeds

                                state.all_transactions.append(
                                    Transaction(
                                        transaction_date=current_date,
                                        action="SELL",
                                        qty=shares_to_sell,
                                        price=state.price_data[ticker]
                                        .loc[current_date, "Close"]
                                        .item(),
                                        ticker=ticker,
                                        notes=f"Forced sale to fund withdrawal (raised ${proceeds:.2f})",
                                    )
                                )

                actual_withdrawal = min(withdrawal_amount, state.shared_bank)
                state.shared_bank -= actual_withdrawal
                notes = f"${actual_withdrawal:.2f} withdrawn (${cash_available:.2f} cash + ${actual_withdrawal - cash_available:.2f} from asset sales), bank=${state.shared_bank:.2f}"

            state.total_withdrawn += actual_withdrawal
            state.withdrawal_count += 1
            state.last_withdrawal_date = current_date
            state.daily_withdrawals[current_date] = actual_withdrawal

            state.all_transactions.append(
                Transaction(
                    transaction_date=current_date,
                    action="WITHDRAWAL",
                    qty=0,
                    price=0.0,
                    ticker="CASH",
                    notes=notes,
                )
            )

            withdrawal_number += 1

        # Wait for next day
        if current_day_index < len(state.common_dates) - 1:
            yield env.timeout(1)
        else:
            break  # End of simulation


def dividend_process(
    env: simpy.Environment, state: SimulationState
) -> Generator[simpy.events.Event, Any, Any]:
    """Process that handles dividend payments."""
    # Collect all dividend events
    dividend_events = []

    for ticker in state.allocations.keys():
        if ticker in state.dividend_data and state.dividend_data[ticker] is not None:
            div_series = state.dividend_data[ticker]
            if not div_series.empty:
                div_dates = pd.to_datetime(div_series.index).date
                for div_date in div_dates:
                    if state.common_dates[0] <= div_date <= state.common_dates[-1]:
                        day_index = state.common_dates.index(div_date)
                        div_per_share = div_series.loc[pd.Timestamp(div_date)]
                        dividend_events.append((day_index, ticker, div_date, div_per_share))

    # Sort events by day
    dividend_events.sort(key=lambda x: x[0])

    # Process events in order
    for day_index, ticker, div_date, div_per_share in dividend_events:
        # Wait until the dividend date
        if day_index > env.now:
            yield env.timeout(day_index - int(env.now))

        # Special handling for CASH (sweep account interest from BIL)
        if ticker == "CASH":
            # Calculate interest based on cash balance (not holdings)
            # Bank balance earns BIL yield as if invested in BIL shares
            if state.bil_price_data is not None:
                try:
                    # Get BIL price on dividend date
                    bil_price = state.bil_price_data.loc[pd.Timestamp(div_date), "Close"].item()

                    # Calculate equivalent BIL shares from current bank balance
                    # Use time-weighted average bank balance over accrual period
                    accrual_period_days = 30  # Monthly for BIL
                    period_start = div_date - timedelta(days=accrual_period_days)

                    # Calculate average bank balance over period
                    # (Simple approximation: just use current balance)
                    avg_cash_balance = state.shared_bank

                    # Equivalent BIL shares
                    equivalent_shares = avg_cash_balance / bil_price

                    # Interest payment
                    div_payment = div_per_share * equivalent_shares
                    state.shared_bank += div_payment
                    state.total_dividends_by_asset[ticker] += div_payment
                    state.dividend_payment_count_by_asset[ticker] += 1

                    state.all_transactions.append(
                        Transaction(
                            transaction_date=div_date,
                            action="INTEREST",
                            qty=0,  # CASH doesn't have shares
                            price=div_per_share,
                            ticker=ticker,
                            notes=f"${div_payment:.2f} (${avg_cash_balance:,.0f} @ {(div_per_share/bil_price)*12*100:.2f}% APY via BIL), bank = {state.shared_bank:.2f}",
                        )
                    )
                except (KeyError, IndexError):
                    # No BIL price data for this date, skip interest payment
                    pass
            continue

        # Standard dividend payment for regular tickers
        accrual_period_days = 90
        period_start = div_date - timedelta(days=accrual_period_days)
        avg_holdings = calculate_time_weighted_average_holdings(
            state.holdings_history[ticker], period_start, div_date
        )

        div_payment = div_per_share * avg_holdings
        state.shared_bank += div_payment
        state.total_dividends_by_asset[ticker] += div_payment
        state.dividend_payment_count_by_asset[ticker] += 1

        state.all_transactions.append(
            Transaction(
                transaction_date=div_date,
                action="DIVIDEND",
                qty=int(avg_holdings),
                price=div_per_share,
                ticker=ticker,
                notes=f"${div_payment:.2f} (avg {avg_holdings:.2f} shares over 90 days), bank = {state.shared_bank:.2f}",
            )
        )
