#!/usr/bin/env python3
"""Debug script to understand buyback stack behavior."""

import sys
from pathlib import Path
from datetime import date

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.algorithms.factory import build_algo_from_name
from src.models.backtest import run_algorithm_backtest
import pandas as pd

# Load NVDA 2023 data from testdata (cached in repo)
testdata_path = Path(__file__).parent.parent / "testdata" / "NVDA.csv"
prices = pd.read_csv(testdata_path, index_col=0, parse_dates=True)

print(f"NVDA 2023 Price Action:")
print(f"  Start: ${prices['Close'].iloc[0]:.2f}")
print(f"  End: ${prices['Close'].iloc[-1]:.2f}")
print(f"  ATH: ${prices['Close'].max():.2f}")
print(f"  Gain: {(prices['Close'].iloc[-1] / prices['Close'].iloc[0] - 1) * 100:.1f}%")
print(f"  Trading days: {len(prices)}")

# Test with different sdN values
for sdn in [8, 16, 32]:
    algo = build_algo_from_name(f'sd{sdn}')

    start_date = prices.index[0].date()
    end_date = prices.index[-1].date()

    transactions, summary = run_algorithm_backtest(
        df=prices,
        ticker='NVDA',
        initial_qty=10000,
        start_date=start_date,
        end_date=end_date,
        algo=algo,
    )

    print(f"\n{'='*70}")
    print(f"sd{sdn} Results")
    print(f"{'='*70}")
    print(f"Initial shares: 10,000")
    print(f"Buyback stack count: {algo.buyback_stack_count:,} shares")
    print(f"Summary: {summary}")
    print(f"")

    # Count transactions
    buys = [t for t in transactions if t.action == 'BUY']
    sells = [t for t in transactions if t.action == 'SELL']
    total_bought = sum(t.qty for t in buys)
    total_sold = sum(t.qty for t in sells)

    print(f"Transactions:")
    print(f"  BUY: {len(buys)} transactions, {total_bought:,.0f} shares")
    print(f"  SELL: {len(sells)} transactions, {total_sold:,.0f} shares")
    print(f"  Net: {total_bought - total_sold:,.0f} shares")
    print(f"")
    print(f"Volatility Alpha:")
    print(f"  Realized: {algo.realized_volatility_alpha:.2f}%")
    print(f"  Unrealized: {algo.unrealized_stack_alpha:.2f}%")
    print(f"  Total: {algo.total_volatility_alpha:.2f}%")

    # Show last few transactions (commented out for now - attribute issues)
    # print(f"\nLast 10 transactions:")
    # for t in transactions[-10:]:
    #     print(f"  {t.action:4s} {t.qty:8,.0f} shares @ ${t.price:7.2f}")
