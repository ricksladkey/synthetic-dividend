"""Test script to generate horn charts at different resolutions."""

from datetime import date
from src.models.backtest import run_portfolio_backtest_v2
from src.algorithms.portfolio_factory import build_portfolio_algo_from_name
from src.charts import create_portfolio_horn_chart

# Run a backtest with the classic portfolio
allocations = {"VOO": 0.6, "BIL": 0.4}
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)

print("Running portfolio backtest...")
portfolio_algo = build_portfolio_algo_from_name("auto", allocations)

transactions, summary = run_portfolio_backtest_v2(
    allocations=allocations,
    start_date=start_date,
    end_date=end_date,
    portfolio_algo=portfolio_algo,
    initial_investment=1_000_000,
    cash_interest_rate_pct=5.0,
)

print(f"\nBacktest complete!")
print(f"Trading days: {summary['trading_days']}")
print(f"Total return: {summary['total_return']:.2f}%")
print(f"Cash interest earned: ${summary['cash_interest_earned']:,.2f}")

# Generate horn charts at different resolutions
print("\n" + "="*80)
print("Generating horn charts at different resolutions...")
print("="*80)

# Daily resolution (all data points)
print("\n1. Daily resolution (252 data points)...")
daily_chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_daily.png",
    resample=None  # or 'D'
)
print(f"   Saved to: {daily_chart}")

# Weekly resolution
print("\n2. Weekly resolution (~52 data points)...")
weekly_chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_weekly.png",
    resample='W'
)
print(f"   Saved to: {weekly_chart}")

# Monthly resolution
print("\n3. Monthly resolution (12 data points)...")
monthly_chart = create_portfolio_horn_chart(
    summary,
    output="horn_chart_monthly.png",
    resample='M'
)
print(f"   Saved to: {monthly_chart}")

print("\n" + "="*80)
print("All charts generated successfully!")
print("="*80)
print("\nYou can view them at:")
print(f"  - Daily:   {daily_chart}")
print(f"  - Weekly:  {weekly_chart}")
print(f"  - Monthly: {monthly_chart}")
