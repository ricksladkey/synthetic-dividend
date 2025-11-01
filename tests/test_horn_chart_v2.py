"""Test script to generate proper horn charts with per-asset breakdown."""

from datetime import date
from src.models.backtest import run_portfolio_backtest
from src.algorithms.portfolio_factory import build_portfolio_algo_from_name
from src.charts import create_portfolio_horn_chart

# Run a backtest with the classic-plus-crypto portfolio with withdrawals
allocations = {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)

print("Running portfolio backtest with 60/30/10 allocation and 8% withdrawals...")
portfolio_algo = build_portfolio_algo_from_name("auto", allocations)

transactions, summary = run_portfolio_backtest(
    allocations=allocations,
    start_date=start_date,
    end_date=end_date,
    portfolio_algo=portfolio_algo,
    initial_investment=1_000_000,
    cash_interest_rate_pct=5.0,
    withdrawal_rate_pct=8.0,
    withdrawal_frequency_days=30,
    allow_margin=False,  # Enforce non-negative cash invariant
)

print(f"\nBacktest complete!")
print(f"Trading days: {summary['trading_days']}")
print(f"Total return: {summary['total_return']:.2f}%")
print(f"Cash interest earned: ${summary['cash_interest_earned']:,.2f}")
print(f"Total withdrawn: ${summary['total_withdrawn']:,.2f}")
print(f"Withdrawal count: {summary['withdrawal_count']}")

# Check what data is available
print(f"\nData available:")
print(f"  daily_asset_values keys: {list(summary.get('daily_asset_values', {}).keys())}")
print(f"  daily_withdrawals entries: {len(summary.get('daily_withdrawals', {}))}")

# Generate horn charts at different resolutions
print("\n" + "="*80)
print("Generating horn charts with per-asset breakdown...")
print("="*80)

# Daily resolution
print("\n1. Daily resolution...")
daily_chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_v2_daily.png",
    resample=None
)
print(f"   Saved to: {daily_chart}")

# Weekly resolution
print("\n2. Weekly resolution...")
weekly_chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_v2_weekly.png",
    resample='W'
)
print(f"   Saved to: {weekly_chart}")

# Monthly resolution
print("\n3. Monthly resolution...")
monthly_chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_v2_monthly.png",
    resample='M'
)
print(f"   Saved to: {monthly_chart}")

print("\n" + "="*80)
print("All charts generated successfully!")
print("="*80)
print("\nThese charts should now show:")
print("  - USD (Cash) - green band at bottom")
print("  - BIL (Bonds) - brown band")
print("  - VOO (Equities) - orange band")
print("  - BTC-USD (Crypto) - blue band at top")
print("  - Withdrawals (Spending Power) - red wedge below zero")
