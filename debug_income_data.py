"""
Debug: Show Income Band Chart Data in Tabular Form

Prints the income data used for the band chart to verify correctness.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path for imports
import sys

sys.path.insert(0, str(Path(__file__).parent / "src"))

from models.synthetic_portfolio import SyntheticPortfolio  # noqa: E402


def create_simple_portfolio() -> SyntheticPortfolio:
    """Create a simple portfolio for debugging."""
    portfolio = SyntheticPortfolio(cash=500_000, name="Debug Portfolio", withdrawal_rate=0.08)

    # Mock assets
    class MockAlgorithm:
        def __init__(self, name):
            self.name = name

    from models.synthetic_portfolio import SyntheticAsset

    assets = [
        ("NVDA", 200, 450.0, "sd8"),
        ("SPY", 150, 400.0, "sd10"),
        ("BTC-USD", 300, 35_000.0, "sd6"),
    ]

    for ticker, shares, price, strategy in assets:
        asset = SyntheticAsset(
            ticker=ticker, holdings=shares, nav=price, algorithm=MockAlgorithm(strategy)
        )
        portfolio.assets[ticker] = asset

        cost = shares * price
        portfolio.bank -= cost
        asset.total_invested = cost

    return portfolio


def generate_debug_income_data(portfolio: SyntheticPortfolio) -> pd.DataFrame:
    """Generate income data for debugging."""
    # Create date range (12 months for easier viewing)
    dates = pd.date_range("2024-01-01", "2024-12-01", freq="M")

    np.random.seed(42)  # For reproducible results

    income_data = []

    for i, current_date in enumerate(dates):
        # Simulate some portfolio activity
        # In a real scenario, this would come from actual algorithm processing

        # Generate realistic income (some months have income, some don't)
        income_row = {
            "date": current_date,
            "NVDA": np.random.normal(500, 100) if np.random.random() > 0.6 else 0,
            "SPY": np.random.normal(300, 50) if np.random.random() > 0.7 else 0,
            "BTC-USD": np.random.normal(800, 200) if np.random.random() > 0.5 else 0,
            "expenses": 3333,  # $500K * 8% / 12 = ~$3,333/month
            "cash": max(0, portfolio.bank - (i * 500)),  # Simulate gradual cash depletion
        }
        income_data.append(income_row)

    df = pd.DataFrame(income_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    return df


def print_income_table(df: pd.DataFrame):
    """Print the income data in a readable table format."""
    print("=== INCOME BAND CHART DATA ===\n")

    # Format for display
    display_df = df.copy()
    display_df = display_df.round(0)  # Round to whole dollars

    print(display_df.to_string())

    print("\n=== SUMMARY STATISTICS ===")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print(f"Total months: {len(df)}")
    print(
        f"Assets with income: {len([col for col in df.columns if col not in ['expenses', 'cash']])}"
    )

    # Monthly totals
    asset_cols = [col for col in df.columns if col not in ["expenses", "cash"]]
    df["total_income"] = df[asset_cols].sum(axis=1)

    print("\nMonthly totals:")
    monthly_summary = df[["total_income", "expenses", "cash"]].round(0)
    print(monthly_summary.to_string())

    print("\nAnnual averages:")
    annual_avg = df[["total_income", "expenses"]].mean() * 12
    print(f"Total Income: ${annual_avg['total_income']:,.0f}")
    print(f"Total Expenses: ${annual_avg['expenses']:,.0f}")
    print(f"Annual Surplus/Deficit: ${(annual_avg['total_income'] - annual_avg['expenses']):,.0f}")

    # Check for issues
    print("\n=== DATA VALIDATION ===")
    if (df[asset_cols] < 0).any().any():
        print("❌ WARNING: Negative income values found!")
    else:
        print("✅ All income values are non-negative")

    if (df["expenses"] < 0).any():
        print("❌ WARNING: Negative expense values found!")
    else:
        print("✅ All expense values are non-negative")

    if (df["cash"] < 0).any():
        print("❌ WARNING: Negative cash values found!")
        print(f"   Cash range: ${df['cash'].min():,.0f} to ${df['cash'].max():,.0f}")
    else:
        print("✅ All cash values are non-negative")


def main():
    """Run the debug script."""
    print("=== DEBUGGING INCOME BAND CHART DATA ===\n")

    # Create portfolio
    portfolio = create_simple_portfolio()
    print(f"Created portfolio with ${portfolio.bank:,.0f} cash")

    # Generate income data
    income_df = generate_debug_income_data(portfolio)

    # Print table
    print_income_table(income_df)


if __name__ == "__main__":
    main()
