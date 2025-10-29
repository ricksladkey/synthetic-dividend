#!/usr/bin/env python3
"""
Demo: Synthetic Portfolio - The Killer App

This script demonstrates the new SyntheticPortfolio class that enables
multi-asset retirement portfolios with 8-10% sustainable withdrawal rates.
"""

from src.models.synthetic_portfolio import SyntheticPortfolio


def demo_portfolio_creation():
    """Demo basic portfolio creation and management."""
    print("=== Synthetic Portfolio Demo ===\n")

    # Create a retirement portfolio
    portfolio = SyntheticPortfolio(
        cash=500_000,
        name="Retirement Portfolio",
        withdrawal_rate=0.08  # 8% annual withdrawal
    )

    print(f"Created: {portfolio}")
    print(f"Initial cash: ${portfolio.bank:,.0f}")
    print(f"Withdrawal rate: {portfolio.withdrawal_rate:.1%}")
    print()

    # Add diversified assets
    print("Adding assets...")
    portfolio.add_asset('NVDA', shares=200, price=450.0, strategy='sd8')
    portfolio.add_asset('SPY', shares=150, price=400.0, strategy='sd10')
    portfolio.add_asset('BTC-USD', shares=300, price=35_000.0, strategy='sd6')
    portfolio.add_asset('GLD', shares=400, price=180.0, strategy='sd12')

    print(f"Assets added: {len(portfolio.assets)}")
    print(f"Holdings: {portfolio.get_holdings()}")
    print(f"Remaining cash: ${portfolio.bank:,.0f}")
    print()

    # Show NAV calculations
    print("NAV Analysis:")
    for ticker, asset in portfolio.assets.items():
        print(f"  {ticker}: NAV=${asset.nav:.2f}, Holdings={asset.holdings}")

    print()

    # Show portfolio summary
    summary = portfolio.summary()
    print("Portfolio Summary:")
    print(f"  Total Value: ${summary['total_value']:,.0f}")
    print(f"  Bank Balance: ${summary['bank_balance']:,.0f}")
    print(f"  Assets: {summary['assets']}")
    print(f"  Rebalancing Mode: {summary['rebalancing_mode']}")
    print(f"  Withdrawal Rate: {summary['withdrawal_rate']:.1%}")
    print()

    # Simulate some NAV updates
    print("Simulating price movements and NAV updates...")

    # NVDA hits new high
    portfolio.assets['NVDA'].update_nav(475.0)
    print(f"NVDA NAV updated to ${portfolio.assets['NVDA'].nav:.2f}")

    # SPY drops (buy opportunity)
    current_spy = 380.0
    premium = portfolio.assets['SPY'].nav_premium(current_spy)
    print(f"SPY at ${current_spy:.2f} ({premium:.1%} premium)")

    # BTC volatile movement
    portfolio.assets['BTC-USD'].update_nav(38_000.0)
    print(f"BTC NAV updated to ${portfolio.assets['BTC-USD'].nav:.2f}")

    print()
    print("=== Demo Complete ===")
    print("\nThis portfolio framework enables:")
    print("• Multi-asset synthetic dividend management")
    print("• NAV-based cross-asset arbitrage")
    print("• Retirement planning with 8-10% withdrawal rates")
    print("• Unified cash management across assets")
    print("• Automatic rebalancing strategies")


if __name__ == "__main__":
    demo_portfolio_creation()
