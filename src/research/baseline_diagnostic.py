"""Diagnostic: Check if synthetic dividend is actually trading.

This will show us exactly what transactions happen with each strategy.
"""

from datetime import date

from src.algorithms import (
    BuyAndHoldAlgorithm,
    PerAssetPortfolioAlgorithm,
    build_portfolio_algo_from_name,
)
from src.models.backtest import run_portfolio_backtest_v2


def main():
    """Run diagnostic on 2019-2024 period."""
    allocations = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}
    start_date = date(2019, 1, 1)
    end_date = date(2024, 12, 31)
    initial = 1_000_000

    print("=" * 80)
    print("BASELINE DIAGNOSTIC")
    print("=" * 80)
    print(f"Portfolio: {allocations}")
    print(f"Period: {start_date} to {end_date}")
    print()

    # Test 1: Buy-and-hold
    print("Test 1: Buy-and-hold")
    print("-" * 80)
    buy_hold = PerAssetPortfolioAlgorithm(
        {ticker: BuyAndHoldAlgorithm() for ticker in allocations.keys()}
    )

    txns_bh, summary_bh = run_portfolio_backtest_v2(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=buy_hold,
        initial_investment=initial,
    )

    print(f"\nResults:")
    print(f"  Transactions: {len(txns_bh)}")
    print(f"  Final value: ${summary_bh['total_final_value']:,.0f}")
    print(f"  Final bank: ${summary_bh['final_bank']:,.2f}")
    print(f"  Return: {summary_bh['total_return']:.2f}%")

    print(f"\nTransaction list:")
    for tx in txns_bh[:10]:  # First 10
        print(f"  {tx.transaction_date} {tx.action:4s} {tx.qty:4d} {tx.ticker:8s} @ ${tx.price:8.2f}")
    if len(txns_bh) > 10:
        print(f"  ... ({len(txns_bh) - 10} more transactions)")

    # Test 2: Synthetic dividend auto
    print("\n\nTest 2: Synthetic dividend auto")
    print("-" * 80)
    auto_algo = build_portfolio_algo_from_name("auto", allocations)

    txns_sd, summary_sd = run_portfolio_backtest_v2(
        allocations=allocations,
        start_date=start_date,
        end_date=end_date,
        portfolio_algo=auto_algo,
        initial_investment=initial,
    )

    print(f"\nResults:")
    print(f"  Transactions: {len(txns_sd)}")
    print(f"  Final value: ${summary_sd['total_final_value']:,.0f}")
    print(f"  Final bank: ${summary_sd['final_bank']:,.2f}")
    print(f"  Return: {summary_sd['total_return']:.2f}%")

    print(f"\nTransaction list:")
    for tx in txns_sd[:20]:  # First 20
        print(f"  {tx.transaction_date} {tx.action:4s} {tx.qty:4d} {tx.ticker:8s} @ ${tx.price:8.2f} - {tx.notes}")
    if len(txns_sd) > 20:
        print(f"  ... ({len(txns_sd) - 20} more transactions)")

    # Analysis
    print("\n\nAnalysis:")
    print("=" * 80)

    # Count non-initial transactions
    bh_trading = [tx for tx in txns_bh if "Initial" not in tx.notes]
    sd_trading = [tx for tx in txns_sd if "Initial" not in tx.notes]

    print(f"Buy-and-hold trading activity: {len(bh_trading)} transactions")
    print(f"Synthetic dividend trading activity: {len(sd_trading)} transactions")

    if len(sd_trading) == 0:
        print("\n⚠️  WARNING: Synthetic dividend did ZERO trades!")
        print("    This means the algorithm never triggered rebalancing.")
        print("    Possible reasons:")
        print("    - Price movements stayed within trigger thresholds")
        print("    - Algorithm not being called correctly")
        print("    - Bug in the trading logic")
    else:
        print(f"\n✓ Synthetic dividend executed {len(sd_trading)} trades")

        # Show breakdown by ticker
        print("\nTrades by asset:")
        for ticker in allocations.keys():
            ticker_trades = [tx for tx in sd_trading if tx.ticker == ticker]
            buys = [tx for tx in ticker_trades if tx.action == "BUY"]
            sells = [tx for tx in ticker_trades if tx.action == "SELL"]
            print(f"  {ticker:8s}: {len(buys)} buys, {len(sells)} sells")

    # Compare final values
    diff = summary_sd['total_final_value'] - summary_bh['total_final_value']
    diff_pct = (diff / summary_bh['total_final_value']) * 100

    print(f"\nValue difference:")
    print(f"  SD - BH = ${diff:,.0f} ({diff_pct:+.2f}%)")

    if abs(diff) < 100:
        print("  ⚠️  Difference is negligible - strategies are identical")
    elif diff > 0:
        print("  ✓ Synthetic dividend outperformed!")
    else:
        print("  ✗ Buy-and-hold outperformed")


if __name__ == "__main__":
    main()
