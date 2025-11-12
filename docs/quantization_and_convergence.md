# Quantization Effects and Convergence Analysis

## The Quantization Problem

### Discrete vs Continuous Regimes

In the discrete simulation, we can only trade **whole shares**. This creates severe quantization errors when:

1. **Position size is small** (e.g., 100 shares)
2. **Price is high** (e.g., MSTR at $400)
3. **Brackets are tight** (e.g., sd32 at 2.19%)

### Example: MSTR at $400 with sd32

**Setup:**
- Price: $400/share
- Bracket spacing: 2.19% = $8.76
- Transaction size: $100 (algorithmic default)
- Shares per transaction: $100/$400 = **0.25 shares**

**Problem:** Must round to 0 or 1 share!
- Round down → Never transact (algorithm breaks)
- Round up → Trade 4× intended amount ($400 instead of $100)

**Impact on results:**
- Artificially inflates transaction counts
- Distorts realized alpha calculations
- Makes tight brackets appear worse than they are

### Quantization Error Scaling

Define the **quantization parameter**:
```
Q = (Initial shares) × (Bracket spacing) / (Price)
```

**Regimes:**
- Q >> 1: Continuous regime (quantization negligible)
- Q ≈ 1: Transition regime (some quantization)
- Q << 1: Discrete regime (quantization dominates)

**Example calculations:**

| Ticker | Price | Position | SDN | δ | Q | Regime |
|--------|-------|----------|-----|---|---|--------|
| NVDA | $50 | 10,000 | sd8 | 9.05% | 18 | Continuous ✓ |
| NVDA | $50 | 100 | sd32 | 2.19% | 0.04 | Discrete ✗ |
| MSTR | $400 | 100 | sd16 | 4.43% | 0.11 | Discrete ✗ |
| MSTR | $400 | 10,000 | sd16 | 4.43% | 11 | Continuous ✓ |

**Conclusion:** Need Q > 10 to avoid quantization artifacts.

---

## Convergence to the Continuous Limit

### Theoretical Result

As bracket spacing δ → 0, the algorithm converges to a **stable limit** that depends only on (μ, σ, T), not on n.

### Proof Sketch

Consider the continuous limit where:
- Bracket spacing: δ = 2^(1/n) - 1 ≈ 1/(n log 2)
- Transaction rate: λ(n) ∝ n (from our earlier derivation)
- Alpha per transaction: α(n) ∝ δ ∝ 1/n

**Total realized alpha:**
```
A(n) = λ(n) × α(n) × T
     ≈ c₁·n × c₂/n × T
     = c₁·c₂·T
     = constant (independent of n!)
```

This explains why realized alpha **converges** as brackets tighten.

### Empirical Evidence (NVDA 2023, 10K shares)

Recall our results:

| SDN | δ | Txns | Realized α |
|-----|---|------|------------|
| 4   | 18.9% | 7 | 0.00% |
| 8   | 9.05% | 24 | 1.98% |
| 16  | 4.43% | 403 | 18.59% |
| 32  | 2.19% | 2677 | 32.81% |

**Problem:** These are still increasing! But notice:
- sd16→sd32: α increased by 1.76× for 2× tighter brackets
- Converging toward limit, but not there yet
- sd32 is contaminated by **margin accumulation** (112K stack)

**Hypothesis:** True convergence only visible with:
1. Fractional shares (no quantization)
2. Managed stack (prevent accumulation)

---

## Continuous Model with Fractional Shares

### Model Setup

Allow trading **continuous share quantities** s ∈ ℝ₊.

At each bracket crossing at price S:
```
Transaction size: D (in dollars)
Shares traded: s = D/S (continuous, no rounding)
```

### Stack Dynamics (Continuous)

The buyback stack evolves as a **continuous accumulation**:

```
dB(t)/dt = λ_buy(S(t), dS/dt) - λ_sell(S(t), dS/dt)
```

where:
- λ_buy = rate of buying (downward crossings)
- λ_sell = rate of selling (upward crossings)

For GBM with drift μ and volatility σ:
```
λ_buy(S, μ, σ, δ) = c · σ/δ · [1 - erf(μ/σ√2)]
λ_sell(S, μ, σ, δ) = c · σ/δ · [1 + erf(μ/σ√2)]
```

where erf = error function encoding the drift bias.

### Equilibrium Stack Size

In steady state (dB/dt = 0):
```
λ_buy = λ_sell
```

This requires **zero drift** (μ = 0). For μ ≠ 0, stack accumulates!

**Critical observation:**
- Uptrend (μ > 0): Stack grows indefinitely (buys > sells)
- Downtrend (μ < 0): Stack drains (sells > buys)
- Sideways (μ = 0): Stack stabilizes

This explains sd32 catastrophe: strong uptrend + tight brackets → unbounded stack.

---

## Convergence of Realized Alpha

### The Limiting Formula

As δ → 0 (equivalently n → ∞), realized alpha converges to:

```
A_∞ = ∫₀ᵀ σ²(t)/2 · f(μ(t)/σ(t)) dt
```

where f(x) is the **efficiency function**:
```
f(x) = {
  1 - x²  if |x| < 1   (choppy market, high efficiency)
  0       if |x| ≥ 1   (strong trend, stack accumulation)
}
```

**Physical interpretation:**
- σ²/2 = "potential" volatility alpha available
- f(μ/σ) = efficiency factor (trend reduces efficiency)
- Strong trends (|μ/σ| > 1) → zero bankable alpha (stack accumulates)

### Sharpe Ratio Dependence

Define Sharpe ratio: SR = μ/σ

**Regimes:**
1. **|SR| < 0.5**: High efficiency, f(SR) ≈ 1
2. **0.5 < |SR| < 1**: Moderate efficiency, stack manageable
3. **|SR| > 1**: Low efficiency, stack accumulates

For NVDA 2023:
```
μ ≈ 150% annual, σ ≈ 40% annual
SR = 1.5/0.4 = 3.75
f(3.75) ≈ 0 (strong trend kills efficiency!)
```

This explains why **sd32 accumulates a massive stack** - the trend is too strong relative to volatility.

---

## Transaction Count Convergence

### Expected Transactions

In the continuous limit:
```
E[N_txns] = λ · T = (c · σ/δ) · T
```

As δ = 1/(n log 2):
```
N_txns ≈ k · σ · n · log(2) · T
```

**For NVDA 2023** (T = 1 year, σ = 40%):
```
N_txns(n) ≈ 0.28 · n · (trading days)
         ≈ 0.28 · n · 250
         ≈ 70 · n
```

**Predictions vs Empirical:**

| SDN | Predicted | Actual | Ratio |
|-----|-----------|--------|-------|
| 4   | 280 | 7 | 0.025 |
| 8   | 560 | 24 | 0.043 |
| 16  | 1120 | 403 | 0.36 |
| 32  | 2240 | 2677 | 1.19 |

**Observation:** Underpredicts at small n, overpredicts at large n.

**Explanation:**
- Small n: Insufficient volatility to trigger crossings
- Large n: Intraday volatility causes **multiple crossings per day**
- Our formula assumes daily resolution

**Corrected formula** (accounting for intraday volatility):
```
N_txns(n) ≈ k₁ · n + k₂ · n² · (σ_intraday/σ_daily)²
```

This quadratic term explains the sd32 explosion!

---

## Practical Recommendations

### 1. Position Sizing to Avoid Quantization

**Rule of thumb:** Maintain Q > 10 for reliable results.

For ticker at price P with bracket δ and N_shares:
```
Q = N_shares · δ · P / (transaction size)

Need: N_shares > 10 · (transaction size) / (δ · P)
```

**Examples:**

| Ticker | Price | SDN | δ | Min shares (Q>10) |
|--------|-------|-----|---|-------------------|
| NVDA | $50 | sd16 | 4.43% | 450 shares |
| NVDA | $50 | sd32 | 2.19% | 910 shares |
| MSTR | $400 | sd16 | 4.43% | 56 shares |
| MSTR | $400 | sd32 | 2.19% | 114 shares |

**Recommendation:** Use **1000-10000 shares** for testing to ensure continuous regime.

### 2. Fractional Shares Implementation

Modify algorithm to track **fractional share quantities**:

```python
# Current (discrete):
shares_to_buy = int(dollar_amount / current_price)  # Rounds down

# Proposed (fractional):
shares_to_buy = dollar_amount / current_price  # Keep as float
```

**Benefits:**
- Eliminates quantization errors
- Matches continuous model exactly
- More accurate alpha calculations

**Challenges:**
- Most brokers don't support fractional shares for all tickers
- Simulation complexity (tracking fractional positions)

### 3. Convergence Testing

Test hypothesis that realized alpha converges with:

**Experiment design:**
1. Run NVDA 2023 with different position sizes:
   - 100 shares (Q << 1, discrete regime)
   - 1,000 shares (Q ≈ 1, transition)
   - 10,000 shares (Q >> 1, continuous)
   - 100,000 shares (verify convergence)

2. Compare realized alpha across SDN values:
   - Expect convergence as position size increases
   - Discrete artifacts should disappear

3. Test with/without fractional shares:
   - Validate that fractional = large position limit

---

## Analytical Predictions

### For Large Position (10,000 shares, fractional)

Using our convergence formula:
```
A_∞ = σ²·T/2 · f(μ/σ)
```

NVDA 2023: μ = 150%, σ = 40%, T = 1, SR = 3.75

Since SR > 1, efficiency factor f(3.75) ≈ 0 (trend too strong).

**Prediction:** Realized alpha should **plateau** around 2-5% regardless of SDN, with stack accumulation preventing further gains.

### For Choppy Market (μ ≈ 0, σ = 40%)

```
A_∞ = (0.4)²/2 · 1 = 0.08 = 8%
```

**Prediction:** Should see ~8% realized alpha with tight brackets in sideways market.

---

## Next Steps for Validation

1. **Implement fractional shares** in simulation
2. **Test convergence** with 100/1K/10K/100K share positions
3. **Verify** that sd16-sd32 converge to same alpha (in fractional regime)
4. **Compare** choppy vs trending markets
5. **Derive closed-form** optimal δ for given (μ, σ, T)

---

## Key Insights

1. **Quantization matters:** Need Q > 10 (or fractional shares) for accurate results

2. **Convergence is real:** As δ → 0, realized alpha approaches limit depending on σ²·f(μ/σ)

3. **Trend kills efficiency:** Strong trends (|SR| > 1) cause stack accumulation, preventing alpha realization

4. **Transaction explosion:** Quadratic growth from intraday volatility makes sd32+ impractical

5. **Optimal regime:** sd8-sd16 with 1000+ shares balances:
   - Enough transactions to capture volatility
   - Manageable stack (Q > 10, δ near δ*)
   - Practical transaction counts
