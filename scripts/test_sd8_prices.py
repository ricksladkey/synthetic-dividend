"""Test script to verify SD-8 transaction prices."""

from datetime import date

from src.algorithms.factory import build_algo_from_name
from src.data.fetcher import HistoryFetcher
from src.models.backtest import run_portfolio_backtest

fetcher = HistoryFetcher()
df = fetcher.get_history("NVDA", date(2024, 1, 1), date(2024, 2, 29))

algo = build_algo_from_name("sd8")
print(
    f"Algorithm settings: rebalance={algo.rebalance_size:.6f}, profit={algo.profit_sharing:.6f}\n"
)

# Convert to portfolio format
start_price = df.iloc[0]["Close"]
initial_investment = 1000 * start_price
allocations = {"NVDA": 1.0}
portfolio_algo = "per-asset:sd8"

transactions, summary = run_portfolio_backtest(
    allocations=allocations,
    start_date=date(2024, 1, 1),
    end_date=date(2024, 2, 29),
    portfolio_algo=portfolio_algo,
    initial_investment=initial_investment,
)

print("All transactions:")
for i, tx in enumerate(transactions):
    print(f"{i+1:2d}. {tx.transaction_date} {tx.action:4s} {tx.qty:5d} shares @ ${tx.price:8.2f}")

# Check sell price ratios
sells = [tx for tx in transactions if tx.action == "SELL"]
if len(sells) >= 2:
    print(f"\nSELL price progression (should increase by ~9.05% each time):")
    for i in range(len(sells)):
        if i == 0:
            print(f"  {i+1}. ${sells[i].price:.2f}")
        else:
            ratio = sells[i].price / sells[i - 1].price
            pct = (ratio - 1) * 100
            print(f"  {i+1}. ${sells[i].price:.2f} (ratio: {ratio:.6f}, +{pct:.2f}%)")
