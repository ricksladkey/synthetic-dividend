"""Rolling window validation: Test strategy across multiple time periods.

This is the objectivity test - we can't cherry-pick time periods.
Every 5-year window from 2015-2025 will be tested.

Portfolio: 60% VOO, 30% BIL, 10% BTC (realistic, diversified)
Strategies: buy-and-hold, quarterly-rebalance, synthetic-dividend-auto
Withdrawal rates: 0%, 4%, 6%, 8%

The question: Does volatility alpha hold up across ALL periods, not just cherry-picked ones?
"""

from datetime import date
from typing import Dict, List, Tuple

import pandas as pd

from src.algorithms import QuarterlyRebalanceAlgorithm, build_portfolio_algo_from_name
from src.models.backtest import run_portfolio_backtest


def generate_rolling_windows(
    start_year: int, end_year: int, window_years: int
) -> List[Tuple[date, date]]:
    """Generate overlapping rolling windows.

    Args:
        start_year: First year of data (e.g., 2015)
        end_year: Last year of data (e.g., 2025)
        window_years: Window size in years (e.g., 5)

    Returns:
        List of (start_date, end_date) tuples
    """
    windows = []
    for year in range(start_year, end_year - window_years + 2):
        start = date(year, 1, 1)
        end = date(year + window_years - 1, 12, 31)
        windows.append((start, end))
    return windows


def run_single_window_comparison(
    allocations: Dict[str, float],
    start_date: date,
    end_date: date,
    withdrawal_rate_pct: float,
    initial_investment: float = 1_000_000,
) -> Dict[str, Dict]:
    """Run all strategies on a single time window.

    Args:
        allocations: Asset allocations (must sum to 1.0)
        start_date: Window start
        end_date: Window end
        withdrawal_rate_pct: Annual withdrawal rate (e.g., 4.0 for 4%)
        initial_investment: Starting capital

    Returns:
        Dict of strategy_name → results summary
    """
    results = {}

    # Strategy 1: Buy-and-hold (no rebalancing, no withdrawals initially)
    print("\n  [1/3] Running buy-and-hold...")
    try:
        from src.algorithms import BuyAndHoldAlgorithm, PerAssetPortfolioAlgorithm

        buy_hold_algo = PerAssetPortfolioAlgorithm(
            {ticker: BuyAndHoldAlgorithm() for ticker in allocations.keys()}
        )

        txns, summary = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=buy_hold_algo,
            initial_investment=initial_investment,
        )

        results["buy-and-hold"] = {
            "final_value": summary["total_final_value"],
            "final_bank": summary["final_bank"],
            "total_return": summary["total_return"],
            "transactions": summary["transaction_count"],
        }
    except Exception as e:
        print(f"    ERROR: {e}")
        results["buy-and-hold"] = {"error": str(e)}

    # Strategy 2: Quarterly rebalancing
    print("  [2/3] Running quarterly-rebalance...")
    try:
        quarterly_algo = QuarterlyRebalanceAlgorithm(
            target_allocations=allocations, rebalance_months=[3, 6, 9, 12]
        )

        txns, summary = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=quarterly_algo,
            initial_investment=initial_investment,
        )

        results["quarterly-rebalance"] = {
            "final_value": summary["total_final_value"],
            "final_bank": summary["final_bank"],
            "total_return": summary["total_return"],
            "transactions": summary["transaction_count"],
        }
    except Exception as e:
        print(f"    ERROR: {e}")
        results["quarterly-rebalance"] = {"error": str(e)}

    # Strategy 3: Synthetic dividend auto
    print("  [3/3] Running synthetic-dividend-auto...")
    try:
        auto_algo = build_portfolio_algo_from_name("auto", allocations)

        txns, summary = run_portfolio_backtest(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=auto_algo,
            initial_investment=initial_investment,
        )

        results["synthetic-dividend-auto"] = {
            "final_value": summary["total_final_value"],
            "final_bank": summary["final_bank"],
            "total_return": summary["total_return"],
            "transactions": summary["transaction_count"],
        }
    except Exception as e:
        print(f"    ERROR: {e}")
        results["synthetic-dividend-auto"] = {"error": str(e)}

    return results


def run_rolling_window_validation(
    allocations: Dict[str, float],
    start_year: int = 2015,
    end_year: int = 2025,
    window_years: int = 5,
    withdrawal_rates: List[float] = [0.0, 4.0, 6.0, 8.0],
    initial_investment: float = 1_000_000,
) -> pd.DataFrame:
    """Run comprehensive rolling window validation.

    Args:
        allocations: Asset allocation dict
        start_year: First year of available data
        end_year: Last year of available data
        window_years: Window size in years
        withdrawal_rates: List of annual withdrawal rates to test
        initial_investment: Starting capital

    Returns:
        DataFrame with columns:
            - window_start, window_end
            - withdrawal_rate
            - strategy
            - final_value, total_return, transactions
            - alpha_vs_buy_hold
    """
    windows = generate_rolling_windows(start_year, end_year, window_years)

    print("=== Rolling Window Validation ===")
    print(f"Portfolio: {allocations}")
    print(f"Windows: {len(windows)} × {window_years}-year periods")
    print(f"Withdrawal rates: {withdrawal_rates}")
    print(f"Initial investment: ${initial_investment:,.0f}")
    print()

    all_results = []

    for window_idx, (start_date, end_date) in enumerate(windows, 1):
        print(f"Window {window_idx}/{len(windows)}: {start_date} to {end_date}")

        for withdrawal_rate in withdrawal_rates:
            print(f"  Withdrawal rate: {withdrawal_rate}%")

            # Run all strategies on this window
            results = run_single_window_comparison(
                allocations=allocations,
                start_date=start_date,
                end_date=end_date,
                withdrawal_rate_pct=withdrawal_rate,
                initial_investment=initial_investment,
            )

            # Calculate alpha vs buy-and-hold
            buy_hold_return = results.get("buy-and-hold", {}).get("total_return", 0)

            for strategy, metrics in results.items():
                if "error" in metrics:
                    continue

                alpha = metrics["total_return"] - buy_hold_return

                all_results.append(
                    {
                        "window_start": start_date,
                        "window_end": end_date,
                        "withdrawal_rate": withdrawal_rate,
                        "strategy": strategy,
                        "final_value": metrics["final_value"],
                        "total_return": metrics["total_return"],
                        "transactions": metrics["transactions"],
                        "alpha_vs_buy_hold": alpha,
                    }
                )

    df = pd.DataFrame(all_results)
    return df


def print_summary_statistics(df: pd.DataFrame) -> None:
    """Print summary statistics across all windows.

    Args:
        df: Results dataframe from run_rolling_window_validation
    """
    print("\n" + "=" * 80)
    print("SUMMARY STATISTICS ACROSS ALL WINDOWS")
    print("=" * 80)

    # Group by strategy and withdrawal rate
    for withdrawal_rate in sorted(df["withdrawal_rate"].unique()):
        print(f"\n{'='*80}")
        print(f"Withdrawal Rate: {withdrawal_rate}%")
        print(f"{'='*80}")

        subset = df[df["withdrawal_rate"] == withdrawal_rate]

        for strategy in ["buy-and-hold", "quarterly-rebalance", "synthetic-dividend-auto"]:
            strategy_data = subset[subset["strategy"] == strategy]

            if len(strategy_data) == 0:
                continue

            print(f"\n{strategy.upper()}")
            print(f"  Mean return: {strategy_data['total_return'].mean():.2f}%")
            print(f"  Std return: {strategy_data['total_return'].std():.2f}%")
            print(f"  Min return: {strategy_data['total_return'].min():.2f}%")
            print(f"  Max return: {strategy_data['total_return'].max():.2f}%")

            if strategy != "buy-and-hold":
                alpha_data = strategy_data["alpha_vs_buy_hold"]
                positive_windows = (alpha_data > 0).sum()
                total_windows = len(alpha_data)
                pct_positive = (positive_windows / total_windows) * 100

                print("\n  Alpha vs buy-and-hold:")
                print(f"    Mean: {alpha_data.mean():.2f}%")
                print(f"    Std: {alpha_data.std():.2f}%")
                print(
                    f"    Positive windows: {positive_windows}/{total_windows} ({pct_positive:.0f}%)"
                )

    print("\n" + "=" * 80)


if __name__ == "__main__":
    # Standard portfolio: 60% VOO, 30% BIL, 10% BTC
    allocations = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}

    # Run validation
    df = run_rolling_window_validation(
        allocations=allocations,
        start_year=2015,
        end_year=2025,
        window_years=5,
        withdrawal_rates=[0.0, 4.0, 6.0, 8.0],
        initial_investment=1_000_000,
    )

    # Print summary
    print_summary_statistics(df)

    # Save results
    output_file = "rolling_window_validation_results.csv"
    df.to_csv(output_file, index=False)
    print(f"\nResults saved to: {output_file}")
