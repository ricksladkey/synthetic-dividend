"""Demo: Income Classification Framework

Demonstrates the three-tier income breakdown:
  - Universal: Real dividends (what the asset gives you)
  - Primary: ATH profit-taking (what the trend gives you)
  - Secondary: Volatility alpha (what volatility gives you)
"""

from datetime import date
import pandas as pd

from src.models.backtest import run_algorithm_backtest, print_income_classification
from src.algorithms import SyntheticDividendAlgorithm, BuyAndHoldAlgorithm


def demo_income_classification():
    """Show income breakdown for synthetic dividend strategy."""
    
    # Create volatile price data with upward trend
    dates = pd.date_range(start="2024-01-01", end="2024-12-31", freq="D")
    n = len(dates)
    
    # Price pattern: oscillating upward trend
    # Starts at $100, ends at $150, with 10% volatility along the way
    import numpy as np
    np.random.seed(42)
    trend = np.linspace(100, 150, n)
    volatility = 10 * np.sin(np.linspace(0, 8*np.pi, n))  # Oscillations
    prices = trend + volatility
    
    df = pd.DataFrame({
        "Open": prices,
        "High": prices * 1.01,
        "Low": prices * 0.99,
        "Close": prices,
    }, index=dates)
    
    # Add quarterly dividends
    div_dates = ["2024-02-15", "2024-05-15", "2024-08-15", "2024-11-15"]
    div_series = pd.Series([0.50] * 4, index=pd.to_datetime(div_dates))
    
    print("=" * 70)
    print("INCOME CLASSIFICATION DEMO")
    print("=" * 70)
    print()
    print("Asset: Volatile stock with upward trend")
    print("Strategy: Synthetic Dividend (9.15% rebalance, 50% profit sharing)")
    print("Period: 2024 (1 year)")
    print("Dividends: $0.50/share quarterly")
    print()
    
    # Run full synthetic dividend algorithm
    algo = SyntheticDividendAlgorithm(
        rebalance_size=9.15,
        profit_sharing=50.0,
        buyback_enabled=True
    )
    
    transactions, summary = run_algorithm_backtest(
        df=df,
        ticker="DEMO",
        initial_qty=100,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo=algo,
        dividend_series=div_series,
        simple_mode=True
    )
    
    print()
    print(f"Final Results:")
    print(f"  Holdings: {summary['holdings']} shares")
    print(f"  Bank: ${summary['bank']:.2f}")
    print(f"  End Value: ${summary['end_value']:.2f}")
    print(f"  Total: ${summary['total']:.2f}")
    print()
    
    # Print detailed income classification
    print_income_classification(summary, verbose=True)
    
    print()
    print("=" * 70)
    print("COMPARISON: Buy-and-Hold vs Synthetic Dividend")
    print("=" * 70)
    print()
    
    # Run buy-and-hold for comparison
    algo_bh = BuyAndHoldAlgorithm()
    _, summary_bh = run_algorithm_backtest(
        df=df,
        ticker="DEMO",
        initial_qty=100,
        start_date=date(2024, 1, 1),
        end_date=date(2024, 12, 31),
        algo=algo_bh,
        dividend_series=div_series,
        simple_mode=True
    )
    
    print(f"Buy-and-Hold:")
    print(f"  Total Return: {summary_bh['total_return']*100:.2f}%")
    print(f"  Dividends: ${summary_bh.get('total_dividends', 0):.2f}")
    print()
    print(f"Synthetic Dividend:")
    print(f"  Total Return: {summary['total_return']*100:.2f}%")
    ic = summary['income_classification']
    print(f"  Universal (dividends): ${ic['universal_dollars']:.2f}")
    print(f"  Primary (ATH selling): ${ic['primary_dollars']:.2f}")
    print(f"  Secondary (vol alpha): ${ic['secondary_dollars']:.2f}")
    print()
    print(f"Outperformance: {(summary['total_return'] - summary_bh['total_return'])*100:+.2f}%")
    print()


if __name__ == "__main__":
    demo_income_classification()
