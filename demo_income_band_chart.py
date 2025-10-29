"""
Demo: Synthetic Portfolio Income Band Chart

Creates a diversified retirement portfolio and visualizes income streams
using the new band chart visualization.

This demonstrates the "killer app" - multi-asset portfolios that can sustain
8-10% withdrawal rates through uncorrelated volatility harvesting.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Add src to path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from models.synthetic_portfolio import SyntheticPortfolio  # noqa: E402
from visualization.income_band_chart import plot_income_bands  # noqa: E402


def create_retirement_portfolio() -> SyntheticPortfolio:
    """Create a diversified retirement portfolio."""
    print("Creating retirement portfolio...")

    # Start with $500K retirement nest egg
    portfolio = SyntheticPortfolio(
        cash=500_000,
        name="Diversified Retirement Portfolio",
        rebalancing_mode="nav_opportunistic",
        withdrawal_rate=0.08  # 8% annual withdrawal
    )

    # Add diversified assets with different strategies
    # For demo purposes, use mock algorithm objects
    class MockAlgorithm:
        def __init__(self, name):
            self.name = name

    assets = [
        ('NVDA', 50, 450.0, 'sd8'),       # Tech growth - $22,500
        ('SPY', 100, 400.0, 'sd10'),      # Broad market - $40,000
        ('BTC-USD', 5, 35_000.0, 'sd6'),  # Crypto - $175,000 (smaller position)
        ('GLD', 200, 180.0, 'sd12'),      # Gold - $36,000
        ('TLT', 300, 95.0, 'ath_only'),   # Bonds - $28,500
    ]

    for ticker, shares, price, strategy in assets:
        # Manually create asset without using factory (for demo)
        from models.synthetic_portfolio import SyntheticAsset
        asset = SyntheticAsset(
            ticker=ticker,
            holdings=shares,
            nav=price,
            algorithm=MockAlgorithm(strategy)
        )
        portfolio.assets[ticker] = asset

        # Record initial purchase
        cost = shares * price
        portfolio.bank -= cost
        asset.total_invested = cost

        print(f"  Added {ticker}: {shares} shares @ ${price:.2f} ({strategy})")

    print(f"\nPortfolio created: ${portfolio.total_value:,.0f}")
    return portfolio


def simulate_backtest_data(portfolio: SyntheticPortfolio) -> pd.DataFrame:
    """
    Simulate backtest data for demonstration.

    In a real implementation, this would use actual market data.
    For now, create synthetic data that shows realistic portfolio values.

    Returns DataFrame with:
    - Asset columns: Current market value of each asset's holdings
    - 'cumulative_withdrawals': Total withdrawn to date
    - 'cash': Cash reserves
    """
    print("Simulating backtest data...")

    # Create date range (5 years monthly)
    dates = pd.date_range('2019-01-01', '2024-01-01', freq='ME')

    # Simulate realistic market data with volatility
    np.random.seed(42)  # For reproducible results

    portfolio_data = []
    cumulative_withdrawals = 0

    # Base prices and volatility assumptions
    base_prices = {
        'NVDA': 150, 'SPY': 250, 'BTC-USD': 8000, 'GLD': 120, 'TLT': 120
    }
    volatilities = {
        'NVDA': 0.4, 'SPY': 0.2, 'BTC-USD': 0.8, 'GLD': 0.15, 'TLT': 0.1
    }

    # Track holdings for each asset
    holdings = {
        'NVDA': 50,
        'SPY': 100,
        'BTC-USD': 5,
        'GLD': 200,
        'TLT': 300
    }

    for i, current_date in enumerate(dates):
        # Update prices with random walk
        for ticker in holdings.keys():
            base = base_prices[ticker]
            vol = volatilities[ticker]
            change = np.random.normal(0.01, vol)  # 1% drift, asset-specific vol
            base_prices[ticker] = base * (1 + change)

        # Calculate current asset values
        asset_values = {
            ticker: holdings[ticker] * base_prices[ticker]
            for ticker in holdings.keys()
        }

        # Monthly withdrawal
        monthly_withdrawal = 3333  # $500K * 8% / 12
        cumulative_withdrawals += monthly_withdrawal

        # Calculate cash (starts at $500K total - asset costs, decreases by withdrawals)
        initial_cash = 500_000 - sum(holdings[t] * p for t, p in
                                     [('NVDA', 450), ('SPY', 400), ('BTC-USD', 35000),
                                      ('GLD', 180), ('TLT', 95)])
        current_cash = max(0, initial_cash - (i * monthly_withdrawal))

        # Build row
        row = {
            'date': current_date,
            **asset_values,  # Add all asset values
            'cash': current_cash,
            'cumulative_withdrawals': cumulative_withdrawals
        }
        portfolio_data.append(row)

    # Create DataFrame
    df = pd.DataFrame(portfolio_data)
    df['date'] = pd.to_datetime(df['date'])
    df = df.set_index('date')

    print(f"Simulated {len(dates)} months of data")
    print(f"Final cumulative withdrawals: ${cumulative_withdrawals:,.0f}")
    final_value = df[['NVDA', 'SPY', 'BTC-USD', 'GLD', 'TLT', 'cash']].iloc[-1].sum()
    print(f"Final portfolio value: ${final_value:,.0f}")

    return df


def main():
    """Run the complete demo."""
    print("=== Synthetic Portfolio Income Band Chart Demo ===\n")

    # Create portfolio
    portfolio = create_retirement_portfolio()

    # Simulate backtest data
    income_data = simulate_backtest_data(portfolio)

    # Generate income band chart
    print("\nGenerating income band chart...")
    output_file = "retirement_portfolio_income_bands.png"

    plot_income_bands(
        income_data=income_data,
        title="Retirement Portfolio Income Streams (8% Withdrawal Rate)",
        output_file=output_file,
        figsize=(16, 10)
    )

    # Show portfolio summary
    summary = portfolio.summary()
    print("\nPortfolio Summary:")
    print(f"  Final Value: ${summary['total_value']:,.0f}")
    print(f"  Total Return: {summary['total_return']:.1%}")
    print(f"  Max Drawdown: {summary['max_drawdown']:.1%}")
    print(f"  Total Dividends: ${summary['total_dividends']:,.0f}")
    print(f"  Total Withdrawals: ${summary['total_withdrawals']:,.0f}")
    print(f"  Assets: {summary['assets']}")
    print(f"  Transactions: {summary['transactions']}")

    print(f"\n✓ Income band chart saved to: {output_file}")
    print("\nThe chart shows:")
    print("- Each asset's current value in different colored bands")
    print("- Red band at top: Cumulative withdrawals over time")
    print("- Green band at bottom: USD cash reserves")
    print("- Total height = Portfolio value + All withdrawals")
    print("- Demonstrates wealth preservation through volatility harvesting")


if __name__ == "__main__":
    # Ensure we have required dependencies
    try:
        import matplotlib.pyplot  # noqa: F401
    except ImportError as e:
        print(f"Missing required dependencies: {e}")
        print("Install with: pip install numpy matplotlib pandas")
        sys.exit(1)

    main()
