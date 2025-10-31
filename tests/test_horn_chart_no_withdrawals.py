"""Test horn chart with NO withdrawals - cash should accumulate from synthetic dividends."""

from datetime import date
from src.models.backtest import run_portfolio_backtest_v2
from src.algorithms.portfolio_factory import build_portfolio_algo_from_name
from src.charts import create_portfolio_horn_chart

# Run backtest with classic-plus-crypto portfolio, NO withdrawals
allocations = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)

print("Running portfolio backtest with 60/30/10 allocation, NO withdrawals...")
print("Expectation: Cash should GROW as synthetic dividends sell at ATH")
portfolio_algo = build_portfolio_algo_from_name("auto", allocations)

transactions, summary = run_portfolio_backtest_v2(
    allocations=allocations,
    start_date=start_date,
    end_date=end_date,
    portfolio_algo=portfolio_algo,
    initial_investment=1_000_000,
    cash_interest_rate_pct=5.0,
    withdrawal_rate_pct=0.0,  # NO WITHDRAWALS
    withdrawal_frequency_days=30,
)

print(f"\nBacktest complete!")
print(f"Trading days: {summary['trading_days']}")
print(f"Total return: {summary['total_return']:.2f}%")
print(f"Cash interest earned: ${summary['cash_interest_earned']:,.2f}")
print(f"Final bank: ${summary['final_bank']:,.2f}")
print(f"Total withdrawn: ${summary['total_withdrawn']:,.2f}")

# Get initial and final cash from daily tracking
daily_bank = summary['daily_bank_values']
dates = sorted(daily_bank.keys())
initial_bank = daily_bank[dates[0]]
final_bank = summary['final_bank']
cash_change = final_bank - initial_bank

print(f"\nCash analysis:")
print(f"  Starting cash: ${initial_bank:,.2f}")
print(f"  Ending cash:   ${final_bank:,.2f}")
print(f"  Change:        ${cash_change:,.2f} ({(cash_change/initial_bank*100):.1f}%)")

if cash_change > 0:
    print("  [OK] Cash GREW - synthetic dividends are accumulating!")
else:
    print("  [ERROR] Cash SHRUNK - something is consuming cash (buybacks?)")

# Generate horn chart
print("\n" + "="*80)
print("Generating horn chart (no withdrawals)...")
print("="*80)

chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_no_withdrawals.png",
    resample='W'  # Weekly for clarity
)
print(f"\nChart saved to: {chart}")
print("\nExpected: Green cash band should GROW over time (synthetic dividends)")
