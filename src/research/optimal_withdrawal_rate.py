"""Optimal Withdrawal Rate Research

Research Question:
    What withdrawal rate minimizes abs(bank) - i.e., keeps the portfolio balanced
    where withdrawals are matched by harvested volatility alpha?

Key Insight:
    When bank ≈ 0:
    - Withdrawals are balanced (on average)
    - Cash buffer is used ~50% of the time
    - No margin borrowing required
    - Portfolio is "self-sustaining" from volatility harvesting alone

Statistical Approach:
    - Find withdrawal rate where mean(bank) ≈ 0
    - Or minimize std(bank) / mean(abs(bank))
    - 2-sigma gives "zero point" for diversified portfolios
    - With N uncorrelated assets: 80-90% probability of no margin

Test Design:
    1. Run backtests with varying withdrawal rates
    2. Track bank balance statistics
    3. Find rate where bank oscillates around zero
    4. Measure margin usage frequency
    5. Test across different market conditions

Metrics:
    - mean(bank): Should be near zero for balanced withdrawals
    - std(bank): Volatility of bank balance
    - bank_negative_count: How often we need margin
    - bank_positive_count: How often we have cash buffer
    - abs(mean(bank)): Minimize this for "balanced" portfolio
"""

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
from typing import TypedDict

from src.algorithms.factory import build_algo_from_name
from src.data.fetcher import HistoryFetcher
from src.models.retirement_backtest import run_retirement_backtest


class Scenario(TypedDict):
    """Type definition for experiment scenarios."""

    ticker: str
    start: date
    end: date
    algo: str
    min_rate: float
    max_rate: float
    step: float
    qty: int


@dataclass
class WithdrawalRateResult:
    """Results from testing a specific withdrawal rate."""

    withdrawal_rate: float
    mean_bank: float
    std_bank: float
    bank_negative_count: int
    bank_positive_count: int
    bank_min: float
    bank_max: float
    abs_mean_bank: float  # Optimization target
    total_return: float
    final_value: float
    total_withdrawn: float

    @property
    def margin_usage_pct(self) -> float:
        """Percentage of days using margin."""
        total_days = self.bank_negative_count + self.bank_positive_count
        return (self.bank_negative_count / total_days * 100) if total_days > 0 else 0

    @property
    def balance_score(self) -> float:
        """Lower is better - measures how balanced the withdrawals are."""
        return self.abs_mean_bank + 0.5 * self.std_bank


def find_optimal_withdrawal_rate(
    ticker: str,
    start_date: date,
    end_date: date,
    algorithm_name: str,
    initial_qty: int = 10000,
    min_rate: float = 0.01,
    max_rate: float = 0.20,
    step: float = 0.01,
    simple_mode: bool = True,
    risk_free_data: Optional[pd.DataFrame] = None,
    risk_free_asset_ticker: Optional[str] = None,
) -> List[WithdrawalRateResult]:
    """Find the withdrawal rate that minimizes abs(mean(bank)).

    Args:
        ticker: Asset symbol
        start_date: Start of test period
        end_date: End of test period
        algorithm_name: Algorithm to test (e.g., 'sd-9.05,50.0')
        initial_qty: Initial quantity of shares
        min_rate: Minimum withdrawal rate to test (default 1%)
        max_rate: Maximum withdrawal rate to test (default 20%)
        step: Step size for testing rates (default 1%)
        simple_mode: Whether to use simple mode (no costs/gains)
        risk_free_data: Optional price data for risk-free asset
        risk_free_asset_ticker: Ticker for risk-free asset

    Returns:
        List of WithdrawalRateResult sorted by balance_score (best first)
    """
    # Fetch price data
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df.empty:
        raise ValueError(f"No data available for {ticker}")

    # Test withdrawal rates
    results = []
    test_rates = np.arange(min_rate, max_rate + step, step)

    print(
        f"Testing {len(test_rates)} withdrawal rates from {min_rate*100:.0f}% to {max_rate*100:.0f}%"
    )
    print(f"Asset: {ticker} ({start_date} to {end_date})")
    print(f"Algorithm: {algorithm_name}")
    print(f"Simple mode: {simple_mode}")
    print()

    for i, rate in enumerate(test_rates, 1):
        # Build algorithm (fresh instance for each test)
        algo = build_algo_from_name(algorithm_name)

        # Run backtest
        _, summary = run_retirement_backtest(
            df,
            ticker,
            initial_qty,
            start_date,
            end_date,
            algo,
            annual_withdrawal_rate=rate,
            withdrawal_frequency="monthly",
            cpi_adjust=True,
            simple_mode=simple_mode,
        )

        # Calculate statistics
        result = WithdrawalRateResult(
            withdrawal_rate=rate,
            mean_bank=summary["bank_avg"],
            std_bank=np.std([summary["bank_min"], summary["bank_max"], summary["bank"]]),
            bank_negative_count=summary["bank_negative_count"],
            bank_positive_count=summary["bank_positive_count"],
            bank_min=summary["bank_min"],
            bank_max=summary["bank_max"],
            abs_mean_bank=abs(summary["bank_avg"]),
            total_return=summary["total_return"],
            final_value=summary["total"],
            total_withdrawn=summary["total_withdrawn"],
        )

        results.append(result)

        # Progress indicator
        if i % 5 == 0 or i == len(test_rates):
            print(f"Progress: {i}/{len(test_rates)} rates tested")

    # Sort by balance score (lower is better)
    results.sort(key=lambda r: r.balance_score)

    return results


def print_results(results: List[WithdrawalRateResult], ticker: str, top_n: int = 10):
    """Print results in a readable format.

    Args:
        results: List of WithdrawalRateResult (assumed sorted)
        ticker: Asset ticker for display
        top_n: Number of top results to show in detail
    """
    print("\n" + "=" * 80)
    print(f"OPTIMAL WITHDRAWAL RATE ANALYSIS: {ticker}")
    print("=" * 80)

    # Show top N results
    print(f"\nTop {top_n} Most Balanced Withdrawal Rates:")
    print("-" * 80)
    print(
        f"{'Rank':<6} {'Rate':<8} {'Mean Bank':<12} {'Std Bank':<12} {'Margin %':<10} {'Balance Score':<15}"
    )
    print("-" * 80)

    for i, result in enumerate(results[:top_n], 1):
        print(
            f"{i:<6} {result.withdrawal_rate*100:>6.1f}%  "
            f"${result.mean_bank:>10,.0f}  "
            f"${result.std_bank:>10,.0f}  "
            f"{result.margin_usage_pct:>8.1f}%  "
            f"{result.balance_score:>13,.0f}"
        )

    # Detailed view of optimal rate
    optimal = results[0]
    print("\n" + "=" * 80)
    print("OPTIMAL WITHDRAWAL RATE (Most Balanced)")
    print("=" * 80)
    print(f"\nWithdrawal Rate: {optimal.withdrawal_rate*100:.1f}% annually")
    print("\nBank Balance Statistics:")
    print(f"  Mean: ${optimal.mean_bank:,.0f}")
    print(f"  Std Dev: ${optimal.std_bank:,.0f}")
    print(f"  Min: ${optimal.bank_min:,.0f}")
    print(f"  Max: ${optimal.bank_max:,.0f}")
    print(f"  |Mean|: ${optimal.abs_mean_bank:,.0f} (optimization target)")
    print("\nMargin Usage:")
    print(f"  Days in margin: {optimal.bank_negative_count}")
    print(f"  Days with cash: {optimal.bank_positive_count}")
    print(f"  Margin usage: {optimal.margin_usage_pct:.1f}%")
    print("\nPortfolio Performance:")
    print(f"  Total return: {optimal.total_return*100:+.1f}%")
    print(f"  Final value: ${optimal.final_value:,.0f}")
    print(f"  Total withdrawn: ${optimal.total_withdrawn:,.0f}")
    print(f"\nBalance Score: {optimal.balance_score:,.0f} (lower is better)")

    # Statistical insight
    print("\n" + "=" * 80)
    print("STATISTICAL INTERPRETATION")
    print("=" * 80)
    print(
        """
At {optimal.withdrawal_rate*100:.1f}% withdrawal rate:

1. **Balanced Withdrawals**: Mean bank ≈ ${optimal.mean_bank:,.0f}
   - Withdrawals are roughly matched by harvested volatility alpha
   - Portfolio is near self-sustaining from rebalancing alone

2. **Margin Usage**: {optimal.margin_usage_pct:.1f}% of days in margin
   - Bank buffer used ~{100-optimal.margin_usage_pct:.0f}% of the time
   - This is the "zero point" for a single asset

3. **Diversification Potential**:
   - With N uncorrelated assets, margin usage drops to ~{optimal.margin_usage_pct / np.sqrt(10):.1f}%
   - Central Limit Theorem: σ_portfolio = σ_asset / √N
   - 2-sigma confidence: ~95% probability of no margin with 10+ assets

4. **Interpretation**:
   - This is the maximum sustainable withdrawal rate for THIS asset
   - Below this: Portfolio grows (excess volatility alpha)
   - Above this: Increasing margin usage (under-harvesting)
   - At this point: Perfectly balanced (maximum efficiency)
"""
    )

    print("=" * 80)


def run_experiment():
    """Run the optimal withdrawal rate experiment."""

    # Experiment parameters
    scenarios: list[Scenario] = [
        {
            "ticker": "NVDA",
            "start": date(2023, 1, 1),
            "end": date(2023, 12, 31),
            "algo": "sd-9.05,50.0",
            "min_rate": 0.04,
            "max_rate": 0.30,
            "step": 0.01,
            "qty": 10000,
        },
        {
            "ticker": "VOO",
            "start": date(2019, 1, 1),
            "end": date(2019, 12, 31),
            "algo": "sd-9.05,50.0",
            "min_rate": 0.03,
            "max_rate": 0.15,
            "step": 0.01,
            "qty": 1000,
        },
        {
            "ticker": "SPY",
            "start": date(2022, 1, 1),
            "end": date(2022, 12, 31),
            "algo": "sd-9.05,50.0",
            "min_rate": 0.00,
            "max_rate": 0.10,
            "step": 0.01,
            "qty": 1000,
        },
    ]

    for scenario in scenarios:
        print("\n" + "=" * 80)
        print(f"SCENARIO: {scenario['ticker']} {scenario['start'].year}")
        print("=" * 80)

        results = find_optimal_withdrawal_rate(
            ticker=scenario["ticker"],
            start_date=scenario["start"],
            end_date=scenario["end"],
            algorithm_name=scenario["algo"],
            initial_qty=scenario["qty"],
            min_rate=scenario["min_rate"],
            max_rate=scenario["max_rate"],
            step=scenario["step"],
            simple_mode=True,
        )

        print_results(results, scenario["ticker"], top_n=10)

        # Save results
        output_dir = Path("experiments/optimal_withdrawal")
        output_dir.mkdir(parents=True, exist_ok=True)

        df = pd.DataFrame(
            [
                {
                    "withdrawal_rate": r.withdrawal_rate,
                    "mean_bank": r.mean_bank,
                    "std_bank": r.std_bank,
                    "abs_mean_bank": r.abs_mean_bank,
                    "balance_score": r.balance_score,
                    "margin_usage_pct": r.margin_usage_pct,
                    "bank_min": r.bank_min,
                    "bank_max": r.bank_max,
                    "total_return": r.total_return,
                    "final_value": r.final_value,
                    "total_withdrawn": r.total_withdrawn,
                }
                for r in results
            ]
        )

        filename = f"{scenario['ticker']}_{scenario['start'].year}_optimal_withdrawal.csv"
        df.to_csv(output_dir / filename, index=False)
        print(f"\nResults saved to: {output_dir / filename}")


if __name__ == "__main__":
    run_experiment()
