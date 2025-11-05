"""Demo: Real dividend income with AAPL backtest.

Shows how dividend payments from dividend-paying stocks are automatically
credited to the bank, improving coverage ratio and reducing forced sales.
"""

from datetime import date

from src.data.fetcher import HistoryFetcher
from src.models.backtest import SyntheticDividendAlgorithm, run_portfolio_backtest


def main():
    print("=" * 80)
    print("DIVIDEND INTEGRATION DEMO: AAPL with Real Dividends")
    print("=" * 80)
    print()

    # Fetch historical data
    fetcher = HistoryFetcher()

    print("Fetching AAPL price history (2024)...")
    price_df = fetcher.get_history("AAPL", date(2024, 1, 1), date(2024, 12, 31))

    print("Fetching AAPL dividend history (2024)...")
    div_series = fetcher.get_dividends("AAPL", date(2024, 1, 1), date(2024, 12, 31))

    print()
    print("AAPL dividend payments in 2024:")
    print(f"  Count: {len(div_series)}")
    print(f"  Total per share: ${div_series.sum():.4f}")
    print("  Payments:")
    for dt, amt in div_series.items():
        print(f"    {dt.strftime('%Y-%m-%d')}: ${amt:.4f}")
    print()

    # Common parameters
    allocations = {"AAPL": 1.0}
    start_price = price_df.iloc[0]["Close"]
    initial_investment = 100 * start_price
    portfolio_algo = "per-asset:sd-9.15,50"

    # Run backtest WITHOUT dividends
    print("-" * 80)
    print("Backtest 1: WITHOUT dividend tracking")
    print("-" * 80)
    transactions1, summary1 = run_portfolio_backtest(
        allocations=allocations,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        portfolio_algo=portfolio_algo,
        initial_investment=initial_investment,
        dividend_data=None,  # Ignore dividends
        cash_interest_rate_pct=0.0,  # simple_mode equivalent
    )

    # Map to single-ticker format
    from src.models.backtest import _map_portfolio_to_single_ticker_summary

    summary1_mapped = _map_portfolio_to_single_ticker_summary(
        portfolio_summary=summary1,
        ticker="AAPL",
        df_indexed=price_df,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo_obj=None,
        transactions=transactions1,
    )

    print(f"Total return: {summary1_mapped['total_return'] * 100:.2f}%")
    print(f"Bank balance: ${summary1_mapped['bank']:.2f}")
    print(f"Total value: ${summary1_mapped['total']:.2f}")
    print(f"Dividends tracked: ${summary1_mapped['total_dividends']:.2f}")
    print()

    # Run backtest WITH dividends
    print("-" * 80)
    print("Backtest 2: WITH dividend tracking")
    print("-" * 80)
    transactions2, summary2 = run_portfolio_backtest(
        allocations=allocations,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        portfolio_algo=portfolio_algo,
        initial_investment=initial_investment,
        dividend_data={"AAPL": div_series},  # Include real dividends
        cash_interest_rate_pct=0.0,  # simple_mode equivalent
    )

    summary2_mapped = _map_portfolio_to_single_ticker_summary(
        portfolio_summary=summary2,
        ticker="AAPL",
        df_indexed=price_df,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo_obj=None,
        transactions=transactions2,
    )

    print(f"Total return: {summary2_mapped['total_return'] * 100:.2f}%")
    print(f"Bank balance: ${summary2_mapped['bank']:.2f}")
    print(f"Total value: ${summary2_mapped['total']:.2f}")
    print(f"Dividends received: ${summary2_mapped['total_dividends']:.2f}")
    print(f"Dividend payments: {summary2_mapped['dividend_payment_count']}")
    print()

    # Compare results
    print("=" * 80)
    print("COMPARISON")
    print("=" * 80)
    bank_diff = summary2_mapped["bank"] - summary1_mapped["bank"]
    total_diff = summary2_mapped["total"] - summary1_mapped["total"]

    print(f"Bank balance increase: ${bank_diff:.2f}")
    print(f"Total value increase: ${total_diff:.2f}")
    print(f"Total dividends captured: ${summary2_mapped['total_dividends']:.2f}")
    print()

    # Show dividend transactions
    print("Dividend transaction log (subset):")
    div_txns = [t for t in transactions2 if "DIVIDEND" in t]
    for txn in div_txns[:3]:  # Show first 3
        print(f"  {txn}")
    if len(div_txns) > 3:
        print(f"  ... and {len(div_txns) - 3} more")
    print()

    print("=" * 80)
    print("KEY INSIGHT:")
    print("=" * 80)
    print("Real dividends are 'free money' that boosts the bank balance,")
    print("improving coverage ratio and reducing the need for forced sales.")
    print()
    print("AAPL 2024: $0.99/share dividend income on top of price appreciation!")
    print("=" * 80)


if __name__ == "__main__":
    main()
