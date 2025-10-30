"""Quick validation: Single window, multiple withdrawal rates.

Test: 2019-2024 (5 years, includes COVID crash and 2022 bear market)
Portfolio: 60% VOO, 30% BIL, 10% BTC
Withdrawal rates: 4%, 6%, 8%
"""

from datetime import date

from src.algorithms import (
    BuyAndHoldAlgorithm,
    PerAssetPortfolioAlgorithm,
    QuarterlyRebalanceAlgorithm,
    build_portfolio_algo_from_name,
)
from src.models.backtest import run_portfolio_backtest_v2


def main():
    """Run quick validation experiment."""
    # Portfolio
    allocations = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}

    # Time window: 2019-2024 (includes COVID and 2022 bear market)
    start_date = date(2019, 1, 1)
    end_date = date(2024, 12, 31)

    # Starting capital
    initial_investment = 1_000_000

    print("=" * 80)
    print("QUICK VALIDATION EXPERIMENT")
    print("=" * 80)
    print(f"Portfolio: {allocations}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Initial: ${initial_investment:,.0f}")
    print()

    # Withdrawal rates to test
    withdrawal_rates = [0.0, 4.0, 6.0, 8.0]

    results = {}

    for withdrawal_rate in withdrawal_rates:
        print(f"\n{'='*80}")
        print(f"WITHDRAWAL RATE: {withdrawal_rate}%")
        print(f"{'='*80}\n")

        results[withdrawal_rate] = {}

        # Strategy 1: Buy-and-hold
        print("[1/3] Buy-and-hold...")
        buy_hold_algo = PerAssetPortfolioAlgorithm(
            {ticker: BuyAndHoldAlgorithm() for ticker in allocations.keys()}
        )

        txns, summary = run_portfolio_backtest_v2(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=buy_hold_algo,
            initial_investment=initial_investment,
            withdrawal_rate_pct=withdrawal_rate,
        )

        results[withdrawal_rate]["buy-and-hold"] = {
            "final_value": summary["total_final_value"],
            "final_bank": summary["final_bank"],
            "return_pct": summary["total_return"],
            "transactions": summary["transaction_count"],
            "total_withdrawn": summary.get("total_withdrawn", 0),
            "withdrawal_count": summary.get("withdrawal_count", 0),
        }

        print(
            f"  Final: ${summary['total_final_value']:,.0f} "
            f"({summary['total_return']:.2f}% return)\n"
        )

        # Strategy 2: Quarterly rebalance
        print("[2/3] Quarterly rebalance...")
        quarterly_algo = QuarterlyRebalanceAlgorithm(
            target_allocations=allocations, rebalance_months=[3, 6, 9, 12]
        )

        txns, summary = run_portfolio_backtest_v2(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=quarterly_algo,
            initial_investment=initial_investment,
            withdrawal_rate_pct=withdrawal_rate,
        )

        results[withdrawal_rate]["quarterly-rebalance"] = {
            "final_value": summary["total_final_value"],
            "final_bank": summary["final_bank"],
            "return_pct": summary["total_return"],
            "transactions": summary["transaction_count"],
            "total_withdrawn": summary.get("total_withdrawn", 0),
            "withdrawal_count": summary.get("withdrawal_count", 0),
        }

        print(
            f"  Final: ${summary['total_final_value']:,.0f} "
            f"({summary['total_return']:.2f}% return)\n"
        )

        # Strategy 3: Synthetic dividend auto
        print("[3/3] Synthetic dividend auto...")
        auto_algo = build_portfolio_algo_from_name("auto", allocations)

        txns, summary = run_portfolio_backtest_v2(
            allocations=allocations,
            start_date=start_date,
            end_date=end_date,
            portfolio_algo=auto_algo,
            initial_investment=initial_investment,
            withdrawal_rate_pct=withdrawal_rate,
        )

        results[withdrawal_rate]["synthetic-dividend-auto"] = {
            "final_value": summary["total_final_value"],
            "final_bank": summary["final_bank"],
            "return_pct": summary["total_return"],
            "transactions": summary["transaction_count"],
            "total_withdrawn": summary.get("total_withdrawn", 0),
            "withdrawal_count": summary.get("withdrawal_count", 0),
        }

        print(
            f"  Final: ${summary['total_final_value']:,.0f} "
            f"({summary['total_return']:.2f}% return)\n"
        )

    # Print summary table
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    for withdrawal_rate in withdrawal_rates:
        print(f"\n{'─'*80}")
        print(f"Withdrawal Rate: {withdrawal_rate}%")
        print(f"{'─'*80}")

        buy_hold = results[withdrawal_rate]["buy-and-hold"]
        quarterly = results[withdrawal_rate]["quarterly-rebalance"]
        synth_div = results[withdrawal_rate]["synthetic-dividend-auto"]

        print(f"\n{'Strategy':<30} {'Final Value':>15} {'Return':>10} {'Withdrawn':>12} {'Txns':>8}")
        print("-" * 90)

        print(
            f"{'Buy-and-hold':<30} "
            f"${buy_hold['final_value']:>14,.0f} "
            f"{buy_hold['return_pct']:>9.2f}% "
            f"${buy_hold['total_withdrawn']:>11,.0f} "
            f"{buy_hold['transactions']:>8}"
        )

        quarterly_alpha = quarterly["return_pct"] - buy_hold["return_pct"]
        print(
            f"{'Quarterly rebalance':<30} "
            f"${quarterly['final_value']:>14,.0f} "
            f"{quarterly['return_pct']:>9.2f}% "
            f"${quarterly['total_withdrawn']:>11,.0f} "
            f"{quarterly['transactions']:>8} "
            f"(α: {quarterly_alpha:+.2f}%)"
        )

        synth_alpha = synth_div["return_pct"] - buy_hold["return_pct"]
        print(
            f"{'Synthetic dividend auto':<30} "
            f"${synth_div['final_value']:>14,.0f} "
            f"{synth_div['return_pct']:>9.2f}% "
            f"${synth_div['total_withdrawn']:>11,.0f} "
            f"{synth_div['transactions']:>8} "
            f"(α: {synth_alpha:+.2f}%)"
        )

        # Highlight the winner
        winner = max(
            [
                ("Buy-and-hold", buy_hold["return_pct"]),
                ("Quarterly rebalance", quarterly["return_pct"]),
                ("Synthetic dividend", synth_div["return_pct"]),
            ],
            key=lambda x: x[1],
        )

        print(f"\n  Winner: {winner[0]} with {winner[1]:.2f}% return")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
