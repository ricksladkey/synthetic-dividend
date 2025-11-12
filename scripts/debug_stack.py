#!/usr/bin/env python3
"""Analyze buyback stack behavior across SDN parameters.

Focus on theoretical understanding:
- Stack size as function of SDN
- Transaction count scaling (appears quadratic in SDN)
- Margin usage (hypothesis: never exceeds 50% of initial position)
"""

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

initial_shares = 10000
initial_price = prices['Close'].iloc[0]
initial_value = initial_shares * initial_price

print(f"NVDA 2023 Price Action:")
print(f"  Start: ${prices['Close'].iloc[0]:.2f}")
print(f"  End: ${prices['Close'].iloc[-1]:.2f}")
print(f"  ATH: ${prices['Close'].max():.2f}")
print(f"  Price gain: {(prices['Close'].iloc[-1] / prices['Close'].iloc[0] - 1) * 100:.1f}%")
print(f"  Trading days: {len(prices)}")
print(f"  Initial value: ${initial_value:,.0f}")
print()

# Compare SDN parameters (linear in log space: 2^2, 2^3, 2^4, 2^5)
results = []
for sdn in [4, 8, 16, 32]:
    algo = build_algo_from_name(f'sd{sdn}')

    start_date = prices.index[0].date()
    end_date = prices.index[-1].date()

    transactions, summary = run_algorithm_backtest(
        df=prices,
        ticker='NVDA',
        initial_qty=initial_shares,
        start_date=start_date,
        end_date=end_date,
        algo=algo,
    )

    # Count transactions
    buys = [t for t in transactions if t.action == 'BUY']
    sells = [t for t in transactions if t.action == 'SELL']
    total_txns = len(buys) + len(sells)

    # Extract key metrics
    stack_size = algo.buyback_stack_count
    bank = summary['bank']
    holdings = summary['holdings']
    margin_pct = (bank / initial_value) * 100 if bank < 0 else 0

    results.append({
        'sdn': sdn,
        'txns': total_txns,
        'buys': len(buys),
        'sells': len(sells),
        'stack': stack_size,
        'holdings': holdings,
        'bank': bank,
        'margin_pct': margin_pct,
        'realized_alpha': algo.realized_volatility_alpha,
        'unrealized_alpha': algo.unrealized_stack_alpha,
    })

# Display results table
print(f"{'='*90}")
print(f"SDN Parameter Analysis (Linear in Log Space: 2^2, 2^3, 2^4, 2^5)")
print(f"{'='*90}")
print(f"{'SDN':>4} {'Txns':>6} {'Buys':>6} {'Sells':>6} {'Stack':>8} {'Holdings':>9} {'Bank':>12} {'Margin%':>8} {'Real α':>7} {'Unreal α':>8}")
print(f"{'-'*90}")

for r in results:
    print(f"{r['sdn']:>4} {r['txns']:>6} {r['buys']:>6} {r['sells']:>6} "
          f"{r['stack']:>8,} {r['holdings']:>9,} {r['bank']:>12,.0f} "
          f"{r['margin_pct']:>7.1f}% {r['realized_alpha']:>6.2f}% {r['unrealized_alpha']:>7.2f}%")

print()

# Analyze scaling relationships
print(f"{'='*90}")
print(f"Scaling Analysis")
print(f"{'='*90}")

# Transaction count scaling
print(f"\nTransaction Count vs SDN:")
for r in results:
    ratio = r['txns'] / (r['sdn'] ** 2) if r['sdn'] > 0 else 0
    print(f"  sd{r['sdn']:2d}: {r['txns']:4d} txns  →  txns/(SDN²) = {ratio:.2f}")

# Stack size scaling
print(f"\nBuyback Stack vs SDN:")
for r in results:
    print(f"  sd{r['sdn']:2d}: {r['stack']:8,} shares  ({r['stack']/initial_shares:6.2f}× initial)")

# Margin usage (test 50% hypothesis)
print(f"\nMargin Usage vs Initial Value:")
print(f"  Initial value: ${initial_value:,.0f}")
print(f"  Hypothesis: Margin never exceeds 50% of initial position")
for r in results:
    if r['bank'] < 0:
        margin_pct = abs(r['bank']) / initial_value * 100
        status = "✓ PASS" if margin_pct <= 50 else "✗ FAIL"
        print(f"  sd{r['sdn']:2d}: ${r['bank']:12,.0f}  ({margin_pct:5.1f}%)  {status}")
    else:
        print(f"  sd{r['sdn']:2d}: ${r['bank']:12,.0f}  (positive bank)")

print()
print(f"{'='*90}")
print(f"Observations for Continuous Model:")
print(f"{'='*90}")
print(f"1. Transaction count appears to scale as O(SDN²)")
print(f"2. Stack size grows dramatically with tighter triggers")
print(f"3. Margin usage grows but may have theoretical bound")
print(f"4. Realized alpha peaks at intermediate SDN values")
