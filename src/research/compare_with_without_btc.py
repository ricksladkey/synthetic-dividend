"""Compare 60/40 VOO/BIL vs 60/30/10 VOO/BIL/BTC to isolate BTC contribution.

This answers: Is the volatility alpha from BTC's bull run, or from the strategy itself?
"""

from datetime import date

from src.algorithms import (
    BuyAndHoldAlgorithm,
    PerAssetPortfolioAlgorithm,
    QuarterlyRebalanceAlgorithm,
    build_portfolio_algo_from_name,
)
from src.models.backtest import run_portfolio_backtest


def test_portfolio(name, allocations, withdrawal_rate, initial=1_000_000):
    """Test one portfolio configuration."""
    start_date = date(2019, 1, 1)
    end_date = date(2024, 12, 31)

    results = {}

    print(f"\n{name}")
    print("=" * 80)

    # Buy-and-hold
    print("[1/3] Buy-and-hold...")
    buy_hold = PerAssetPortfolioAlgorithm(
        {ticker: BuyAndHoldAlgorithm() for ticker in allocations.keys()}
    )

    txns, summary = run_portfolio_backtest(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=buy_hold,
        initial_investment=initial,
        withdrawal_rate_pct=withdrawal_rate,
    )

    results["buy-and-hold"] = {
        "final": summary["total_final_value"],
        "return": summary["total_return"],
        "withdrawn": summary.get("total_withdrawn", 0),
    }

    # Quarterly rebalance
    print("[2/3] Quarterly rebalance...")
    quarterly = QuarterlyRebalanceAlgorithm(
        target_allocations=allocations, rebalance_months=[3, 6, 9, 12]
    )

    txns, summary = run_portfolio_backtest(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=quarterly,
        initial_investment=initial,
        withdrawal_rate_pct=withdrawal_rate,
    )

    results["quarterly-rebalance"] = {
        "final": summary["total_final_value"],
        "return": summary["total_return"],
        "withdrawn": summary.get("total_withdrawn", 0),
    }

    # Synthetic dividend auto
    print("[3/3] Synthetic dividend auto...")
    auto_algo = build_portfolio_algo_from_name("auto", allocations)

    txns, summary = run_portfolio_backtest(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=auto_algo,
        initial_investment=initial,
        withdrawal_rate_pct=withdrawal_rate,
    )

    results["synthetic-dividend"] = {
        "final": summary["total_final_value"],
        "return": summary["total_return"],
        "withdrawn": summary.get("total_withdrawn", 0),
    }

    return results


def main():
    """Compare portfolios with and without BTC."""
    print("=" * 80)
    print("COMPARISON: WITH vs WITHOUT BTC")
    print("=" * 80)
    print("Period: 2019-2024 (6 years)")
    print("Withdrawal rates: 0%, 4%, 6%, 8%")
    print()

    withdrawal_rates = [0.0, 4.0, 6.0, 8.0]

    # Test both portfolios
    portfolio_60_40 = {"VOO": 0.6, "BIL": 0.4}
    portfolio_60_30_10 = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}

    all_results = {}

    for wd_rate in withdrawal_rates:
        print(f"\n\n{'#'*80}")
        print(f"WITHDRAWAL RATE: {wd_rate}%")
        print(f"{'#'*80}")

        results_60_40 = test_portfolio(
            "60/40 VOO/BIL (Traditional, no BTC)", portfolio_60_40, wd_rate
        )

        results_60_30_10 = test_portfolio("60/30/10 VOO/BIL/BTC", portfolio_60_30_10, wd_rate)

        all_results[wd_rate] = {
            "60/40": results_60_40,
            "60/30/10": results_60_30_10,
        }

    # Print comparison summary
    print("\n\n" + "=" * 90)
    print("SUMMARY COMPARISON")
    print("=" * 90)

    for wd_rate in withdrawal_rates:
        print(f"\n{'-'*90}")
        print(f"Withdrawal Rate: {wd_rate}%")
        print(f"{'-'*90}")

        r_60_40 = all_results[wd_rate]["60/40"]
        r_60_30_10 = all_results[wd_rate]["60/30/10"]

        print(f"\n{'Portfolio':<25} {'Strategy':<25} {'Final Value':>15} {'Return':>10}")
        print("-" * 90)

        # 60/40 results
        print(
            f"{'60/40 VOO/BIL':<25} {'Buy-and-hold':<25} ${r_60_40['buy-and-hold']['final']:>14,.0f} {r_60_40['buy-and-hold']['return']:>9.2f}%"
        )
        print(
            f"{'(no BTC)':<25} {'Quarterly rebalance':<25} ${r_60_40['quarterly-rebalance']['final']:>14,.0f} {r_60_40['quarterly-rebalance']['return']:>9.2f}%"
        )
        print(
            f"{'':<25} {'Synthetic dividend':<25} ${r_60_40['synthetic-dividend']['final']:>14,.0f} {r_60_40['synthetic-dividend']['return']:>9.2f}%"
        )

        print()

        # 60/30/10 results
        print(
            f"{'60/30/10 VOO/BIL/BTC':<25} {'Buy-and-hold':<25} ${r_60_30_10['buy-and-hold']['final']:>14,.0f} {r_60_30_10['buy-and-hold']['return']:>9.2f}%"
        )
        print(
            f"{'(with 10% BTC)':<25} {'Quarterly rebalance':<25} ${r_60_30_10['quarterly-rebalance']['final']:>14,.0f} {r_60_30_10['quarterly-rebalance']['return']:>9.2f}%"
        )
        print(
            f"{'':<25} {'Synthetic dividend':<25} ${r_60_30_10['synthetic-dividend']['final']:>14,.0f} {r_60_30_10['synthetic-dividend']['return']:>9.2f}%"
        )

        print()

        # Calculate deltas
        print("BTC Contribution (60/30/10 - 60/40):")
        for strategy in ["buy-and-hold", "quarterly-rebalance", "synthetic-dividend"]:
            delta = r_60_30_10[strategy]["final"] - r_60_40[strategy]["final"]
            delta_pct = r_60_30_10[strategy]["return"] - r_60_40[strategy]["return"]
            print(f"  {strategy:<25} ${delta:>14,.0f} ({delta_pct:+.2f}%)")

        print()

        # Calculate alpha (vs buy-and-hold)
        print("Volatility Alpha (vs buy-and-hold within same portfolio):")

        alpha_60_40_quarterly = (
            r_60_40["quarterly-rebalance"]["return"] - r_60_40["buy-and-hold"]["return"]
        )
        alpha_60_40_synth = (
            r_60_40["synthetic-dividend"]["return"] - r_60_40["buy-and-hold"]["return"]
        )

        alpha_60_30_10_quarterly = (
            r_60_30_10["quarterly-rebalance"]["return"] - r_60_30_10["buy-and-hold"]["return"]
        )
        alpha_60_30_10_synth = (
            r_60_30_10["synthetic-dividend"]["return"] - r_60_30_10["buy-and-hold"]["return"]
        )

        print(f"  60/40 Quarterly rebalance: {alpha_60_40_quarterly:+.2f}%")
        print(f"  60/40 Synthetic dividend:  {alpha_60_40_synth:+.2f}%")
        print(f"  60/30/10 Quarterly rebalance: {alpha_60_30_10_quarterly:+.2f}%")
        print(f"  60/30/10 Synthetic dividend:  {alpha_60_30_10_synth:+.2f}%")

    print("\n" + "=" * 90)
    print("KEY INSIGHTS:")
    print("=" * 90)
    print("1. BTC contribution: How much extra return comes from 10% BTC allocation")
    print("2. Volatility alpha: Strategy outperformance WITHIN same portfolio")
    print("3. If alpha is similar with/without BTC, strategy works independently of BTC")
    print("=" * 90)


if __name__ == "__main__":
    main()
