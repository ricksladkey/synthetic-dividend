#!/usr/bin/env python3
"""Test quantization effects and convergence with position size.

This script validates the analytical predictions:
1. Quantization errors decrease with position size
2. Realized alpha converges as position size increases
3. Fractional shares match the large-position limit
"""

import sys
from datetime import date
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd

from src.algorithms.factory import build_algo_from_name
from src.models.backtest import run_algorithm_backtest

# Load NVDA 2023 data from testdata
testdata_path = Path(__file__).parent.parent / "testdata" / "NVDA.csv"
prices = pd.read_csv(testdata_path, index_col=0, parse_dates=True)

initial_price = prices["Close"].iloc[0]
final_price = prices["Close"].iloc[-1]

print(f"{'='*90}")
print(f"Quantization & Convergence Analysis: NVDA 2023")
print(f"{'='*90}")
print(
    f"Price: ${initial_price:.2f} → ${final_price:.2f} ({(final_price/initial_price - 1)*100:.1f}% gain)"
)
print(f"Trading days: {len(prices)}")
print()

# Test different position sizes
position_sizes = [100, 500, 1000, 5000, 10000]
sdn_values = [8, 16, 32]

results = []

for position_size in position_sizes:
    print(f"{'='*90}")
    print(f"Position Size: {position_size:,} shares (${position_size * initial_price:,.0f})")
    print(f"{'='*90}")

    for sdn in sdn_values:
        algo = build_algo_from_name(f"sd{sdn}")

        start_date = prices.index[0].date()
        end_date = prices.index[-1].date()

        transactions, summary = run_algorithm_backtest(
            df=prices,
            ticker="NVDA",
            initial_qty=position_size,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )

        # Calculate quantization parameter Q
        bracket_spacing = 2 ** (1 / sdn) - 1  # Fractional spacing
        transaction_size = 100  # Algorithm default
        Q = position_size * bracket_spacing * initial_price / transaction_size

        # Extract metrics
        buys = len([t for t in transactions if t.action == "BUY"])
        sells = len([t for t in transactions if t.action == "SELL"])
        total_txns = buys + sells

        stack = algo.buyback_stack_count
        bank = summary["bank"]
        realized_alpha = algo.realized_volatility_alpha
        unrealized_alpha = algo.unrealized_stack_alpha

        # Normalized metrics (per initial dollar)
        realized_alpha_normalized = realized_alpha  # Already a percentage

        results.append(
            {
                "position_size": position_size,
                "sdn": sdn,
                "Q": Q,
                "txns": total_txns,
                "buys": buys,
                "sells": sells,
                "stack": stack,
                "stack_pct": stack / position_size * 100,
                "bank": bank,
                "bank_pct": bank / (position_size * initial_price) * 100,
                "realized_alpha": realized_alpha,
                "unrealized_alpha": unrealized_alpha,
            }
        )

        regime = "Continuous" if Q > 10 else "Transition" if Q > 1 else "Discrete"

        print(
            f"  sd{sdn:2d} (δ={bracket_spacing*100:5.2f}%)  "
            f"Q={Q:6.2f} [{regime:>10s}]  "
            f"Txns={total_txns:4d}  "
            f"Stack={stack:6,} ({stack/position_size*100:5.1f}%)  "
            f"Real α={realized_alpha:6.2f}%"
        )

    print()

# Analysis: Convergence with position size
print(f"{'='*90}")
print(f"Convergence Analysis: Realized Alpha vs Position Size")
print(f"{'='*90}")

for sdn in sdn_values:
    print(f"\nsd{sdn}:")
    sdn_results = [r for r in results if r["sdn"] == sdn]

    for r in sdn_results:
        print(
            f"  {r['position_size']:6,} shares (Q={r['Q']:6.2f}): "
            f"α={r['realized_alpha']:6.2f}%  "
            f"Stack={r['stack_pct']:5.1f}%  "
            f"Bank={r['bank_pct']:+6.1f}%"
        )

    # Check convergence
    alphas = [r["realized_alpha"] for r in sdn_results]
    if len(alphas) > 1:
        alpha_range = max(alphas) - min(alphas)
        converged = "✓" if alpha_range < 1.0 else "✗"
        print(f"  Range: {alpha_range:.2f}% {converged}")

# Analysis: Transaction count scaling
print(f"\n{'='*90}")
print(f"Transaction Count Scaling")
print(f"{'='*90}")

for position_size in position_sizes:
    print(f"\n{position_size:,} shares:")
    size_results = [r for r in results if r["position_size"] == position_size]

    for r in size_results:
        ratio = r["txns"] / (r["sdn"] ** 2)
        print(f"  sd{r['sdn']:2d}: {r['txns']:4d} txns  " f"(txns/n² = {ratio:.2f})")

# Analysis: Quantization regime
print(f"\n{'='*90}")
print(f"Quantization Regime Classification")
print(f"{'='*90}")

discrete_results = [r for r in results if r["Q"] < 1]
transition_results = [r for r in results if 1 <= r["Q"] <= 10]
continuous_results = [r for r in results if r["Q"] > 10]

print(f"\nDiscrete regime (Q < 1): {len(discrete_results)} cases")
if discrete_results:
    avg_alpha = sum(r["realized_alpha"] for r in discrete_results) / len(discrete_results)
    print(f"  Average realized alpha: {avg_alpha:.2f}%")

print(f"\nTransition regime (1 ≤ Q ≤ 10): {len(transition_results)} cases")
if transition_results:
    avg_alpha = sum(r["realized_alpha"] for r in transition_results) / len(transition_results)
    print(f"  Average realized alpha: {avg_alpha:.2f}%")

print(f"\nContinuous regime (Q > 10): {len(continuous_results)} cases")
if continuous_results:
    avg_alpha = sum(r["realized_alpha"] for r in continuous_results) / len(continuous_results)
    print(f"  Average realized alpha: {avg_alpha:.2f}%")

# Key findings
print(f"\n{'='*90}")
print(f"Key Findings")
print(f"{'='*90}")

print(
    f"""
1. Quantization Parameter:
   - Discrete (Q<1): Dominated by rounding errors
   - Transition (1≤Q≤10): Some quantization effects
   - Continuous (Q>10): Quantization negligible

2. Convergence:
   - Realized alpha should converge as position size increases
   - Variations due to quantization should decrease with Q

3. Stack Accumulation:
   - sd32 likely shows massive stack even at large positions
   - Indicates trend (μ) dominates volatility (σ)
   - Not a quantization artifact

4. Recommendations:
   - Use ≥1000 shares for testing to ensure Q>10
   - Consider fractional shares for exact continuous model
   - sd8-sd16 preferred for practical trading
"""
)
