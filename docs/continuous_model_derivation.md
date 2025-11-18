# Continuous Model Derivation for Synthetic Dividend Algorithm

## Limitations of Discrete Simulation

### 1. Quantization Errors (High-Priced Stocks)

For stocks like MSTR trading at $300-$500:
- Dollar amounts per transaction: ~$100
- Share quantities: **single digits** (e.g., 3-5 shares per transaction)
- Bracket spacing at sd16 (4.43%): $13-$22
- **Discretization artifacts dominate the dynamics**

Example: MSTR at $400 with sd16 (4.43% = $17.72 brackets)
- Buy trigger at $382.28: Can only buy whole shares
- $100 / $382.28 = **0.26 shares** → Round to **0 or 1 share**
- Rounding errors accumulate over thousands of transactions

### 2. OHLC Path Ambiguity

Daily OHLC data shows: Open, High, Low, Close
- **Problem**: We don't know the actual price path during the day
- If High - Low spans multiple brackets, **we can't determine transaction sequence**

Example: Price range $100-$110 on single day with sd32 (2.19% = $2.19 brackets)
- Spans ~4-5 brackets
- Possible paths:
 - Monotonic: $100 → $110 (4 sells)
 - V-shaped: $100 → $95 → $110 (buys then sells)
 - Choppy: Multiple up/down oscillations (many transactions)
- **OHLC doesn't distinguish these!**

### 3. Need for Higher Frequency Data

To resolve multiple bracket crossings within a day:
- **Per-hour data**: Required for sd32 with volatile stocks
- **Per-minute data**: Needed for sd64 or higher
- **Tick data**: Ultimate resolution, but computationally expensive

### Why Continuous Model Solves These Issues

The continuous model works in the **thermodynamic limit**:
- Share quantities → infinitesimal (no quantization)
- Time resolution → continuous (no path ambiguity)
- Amenable to **calculus** and **stochastic differential equations**

---

## Mathematical Setup

### Price Process

Stock price follows geometric Brownian motion (GBM):

```
dS(t) = μ S(t) dt + σ S(t) dW(t)
```

where:
- `S(t)` = stock price at time t
- `μ` = drift rate (annualized expected return)
- `σ` = volatility (annualized standard deviation)
- `W(t)` = standard Wiener process (Brownian motion)

**Solution** (Itô's lemma):
```
S(t) = S(0) · exp((μ - σ²/2)t + σ W(t))
```

### Bracket System

Exponentially-spaced brackets with parameter n:

```
δ = 2^(1/n) - 1 (bracket spacing as fraction)
```

Bracket levels in log-space:
```
y_k = y_0 + k · Δ where Δ = log(1 + δ) ≈ δ (for small δ)
```

Price levels:
```
S_k = S_0 · exp(k · δ)
```

### Position Tracking (Continuous Quantities)

Define state variables:
- `H(t)` = total shares held (continuous quantity)
- `B(t)` = buyback stack size (continuous)
- `C(t)` = cash balance (bank account)

Initial conditions:
```
H(0) = H_0 (initial shares)
B(0) = 0 (no stack initially)
C(0) = 0 (no initial cash)
```

---

## Derivation 1: Transaction Rate

### Bracket Crossing Rate

Consider price in log-space: `Y(t) = log(S(t))`

From GBM:
```
dY = (μ - σ²/2) dt + σ dW(t)
```

This is **arithmetic Brownian motion** with:
- Drift: `μ̃ = μ - σ²/2`
- Diffusion: `σ`

**Question**: What is the rate of crossing equally-spaced levels separated by Δ?

### Renewal Theory Approach

For Brownian motion with drift, the mean time between crossings is:

```
E[τ] = Δ / |μ̃| if |μ̃| > 0 (trending market)
E[τ] = ∞ if μ̃ = 0 (pure diffusion)
```

But this is only for **one-directional** crossings. For **both directions** (buys and sells):

The local time density gives crossing rate:
```
Rate of crossings ≈ σ / (π Δ) (from local time theory)
```

**For small Δ** (tight brackets):
```
λ(Δ) = c · σ / Δ where c is a constant
```

Since `Δ = δ ≈ 1/(n · log(2))` for SDN parameter n:

```
λ(n) ∝ σ · n · log(2)
```

**Total transactions over time T**:
```
N_txns(n, T) = λ(n) · T = c · σ · n · log(2) · T
```

This suggests **linear scaling** in n!

### Why Do We Observe Quadratic Scaling?

**Hypothesis**: In trending markets (μ ≠ 0), tighter brackets create **more complex dynamics**:

1. **Primary trend**: Drift μ causes directional movement
2. **Volatility**: Creates oscillations around trend
3. **Mean reversion**: When brackets are tight, intraday volatility triggers many transactions

For a trending market, the effective transaction rate includes:
- **Drift-driven crossings**: ∝ μT/Δ ∝ μ n T
- **Volatility-driven crossings**: ∝ σ²T/Δ² ∝ σ² n² T

**Combined**:
```
N_txns(n, T) ≈ α μ n T + β σ² n² T
```

For strong trends (large μ), linear term dominates.
For choppy markets (large σ/μ), **quadratic term dominates**.

**NVDA 2023**: Strong uptrend with intraday volatility → transition from linear to quadratic as n increases!

---

## Derivation 2: Margin Bound for Downtrends

### Scenario: Price Falls from S₀ to 0

Assume pure downtrend: `S(t) = S_0 · e^(-αt)` for α > 0

As price falls, we cross bracket levels and buy:
```
Bracket k crossed when: S(t) = S_0 · (1+δ)^k = S_0 · e^(-αt)
```

Solving for k:
```
k = -α t / log(1+δ) ≈ -α t / δ
```

### Total Shares Accumulated

Buy fixed dollar amount D at each bracket:
```
Shares bought at level k: Q_k = D / S_k = D / (S_0 (1+δ)^k)
```

Total shares after crossing K brackets (price falls to S_K):
```
H_total = Σ_{k=-K}^{0} Q_k = (D/S_0) · Σ_{k=-K}^{0} (1+δ)^{-k}
```

This is a geometric series:
```
H_total = (D/S_0) · [(1+δ)^{K+1} - 1] / δ
```

### Cash Spent (Margin Usage)

Total cash spent:
```
C_spent = D · (K + 1)
```

### Value at Bottom

When price reaches S_K = S_0 · (1+δ)^{-K}:
```
Value_holdings = H_total · S_K
```

After some algebra:
```
Value_holdings = D · [(1+δ)^{K+1} - 1] / δ · S_0 · (1+δ)^{-K}
 = D · [(1+δ) - (1+δ)^{-K}] / δ
```

For large K (price → 0):
```
Value_holdings ≈ D · (1+δ) / δ ≈ D / δ (for small δ)
```

### Net Position

```
Net = Value_holdings - C_spent
 ≈ D/δ - D(K+1)
```

Wait, this grows without bound as K increases! Let me reconsider...

### Corrected Analysis: Dollar-Cost Averaging

Actually, we buy a **fixed dollar amount** D at each level, but we started with H_0 shares worth V_0 = H_0 · S_0.

The algorithm splits proceeds: when selling at level k, we get D dollars. When buying at level k, we spend D dollars.

**Key insight**: The algorithm's cash balance tracks cumulative buy/sell imbalance.

In pure downtrend from S_0 to S_final:
- Number of sells: 0 (never crosses upward)
- Number of buys: K = log(S_0/S_final) / log(1+δ)
- Cash spent: D · K

**But**: We're selling shares from initial holdings to fund purchases!

Actually, the algorithm uses **margin** when cash runs out. The margin usage is bounded by the fact that:

```
Value of holdings ≥ (Initial value) / 2
```

This requires more careful analysis with the actual algorithm mechanics...

### Margin Bound Proof (Sketch)

**Claim**: For pure downtrend, margin never exceeds 50% of initial value.

**Proof idea**:
1. Start with V_0 = H_0 · S_0 worth of stock
2. As price falls by fraction f, portfolio value becomes V_0 · (1-f)
3. Dollar-cost averaging: we buy more shares at lower prices
4. Average cost basis < initial price
5. By buying on dips, we "share the losses" with the market

**Formal statement**: Need to compute cash balance as function of price decline and show |C_min| ≤ V_0 / 2.

*[TODO: Complete rigorous proof using algorithm's rebalancing mechanics]*

---

## Derivation 3: Stack Accumulation in Uptrends

### The Accumulation Problem

In a strong uptrend, the algorithm:
1. Buys on every small pullback
2. Sells on recovery
3. **But**: Pullbacks become less frequent as price rises
4. **Result**: Stack accumulates

### Continuous Model for Stack

Define:
- `B(t)` = buyback stack size (shares)
- `S(t)` = current price
- `Y(t) = log(S(t))` = log-price

Stack accumulation rate:
```
dB/dt = (Buy rate) - (Sell rate)
```

**Buy rate** when price drops through bracket:
```
λ_buy(Y) = Rate of downward crossings × (shares per crossing)
```

**Sell rate** when price rises:
```
λ_sell(Y) = Rate of upward crossings × (unwinding rate)
```

For GBM with positive drift (uptrend):
```
λ_buy > λ_sell ⟹ dB/dt > 0 ⟹ Stack grows!
```

### Equilibrium Stack Size

In equilibrium (if it exists):
```
λ_buy = λ_sell
```

This requires:
```
Drift × (Downward crossing rate) = Volatility × (Upward crossing rate)
```

For strong uptrends, **no equilibrium exists** → Stack grows without bound!

### Critical Bracket Spacing

There exists a critical bracket spacing δ* such that:
- If δ > δ*: Stack remains manageable (sells dominate over long term)
- If δ < δ*: Stack accumulates (buys exceed sells)

**Hypothesis**:
```
δ* ≈ σ² / (2μ) (ratio of variance to drift)
```

For NVDA 2023: μ ≈ 150%, σ ≈ 40% (annualized)
```
δ* ≈ (0.4)² / (2 × 1.5) ≈ 0.16 / 3 ≈ 5.3%
```

Comparing to bracket spacings:
- sd4: δ = 18.9% > δ* [OK] (manageable)
- sd8: δ = 9.05% > δ* [OK] (manageable)
- sd16: δ = 4.43% < δ* [FAIL] (marginal)
- sd32: δ = 2.19% << δ* [FAIL] (catastrophic)

This predicts the transition around **sd16** where stack begins to grow!

---

## Derivation 4: Realized Alpha

### Alpha Per Transaction

When buying at S₁ and selling at S₂ = S₁(1+δ):
```
Alpha = (S₂ - S₁) / S₁ = δ
```

For one complete cycle (buy → sell):
```
Profit = D · δ (where D is transaction size)
```

### Total Realized Alpha

Number of **complete cycles** over time T:
```
N_cycles(n, T) = min(N_buys, N_sells)
```

In balanced market (equal buys/sells):
```
N_cycles ≈ N_txns / 2
```

Total realized profit:
```
Profit_realized = N_cycles · D · δ
```

As fraction of initial value V_0:
```
Alpha_realized = (N_cycles · D · δ) / V_0
```

Substituting N_cycles ≈ c σ² n² T / 2:
```
Alpha_realized ≈ (c σ² n² T · D · δ) / (2 V_0)
 ≈ (c σ² n² T · D) / (2 n log(2) V_0)
 ≈ k σ² n T where k is a constant
```

**Prediction**: Realized alpha should scale **linearly** with n!

But **empirically** (NVDA 2023):
- sd4: 0.00%
- sd8: 1.98%
- sd16: 18.59% (9.4× increase for 2× in n)
- sd32: 32.81% (1.8× increase for 2× in n)

**Explanation**: The formula holds only while stack can be unwound. For sd32, most "realized" alpha is actually trapped in unmovable stack!

### True Bankable Alpha

Define **bankable alpha** as profit that can be withdrawn:
```
Alpha_bankable = Alpha_realized - Alpha_trapped_in_stack
```

where:
```
Alpha_trapped = (Unrealized gains in stack) × (1 - Liquidity_factor)
```

For sd32 with 112K share stack at end of year:
- Unrealized stack alpha: 2.07%
- But to liquidate 112K shares would require crossing 112 brackets upward
- In a strong uptrend, this may **never happen**
- Therefore: **Effective bankable alpha << reported realized alpha**

---

## Summary of Continuous Model Results

### Transaction Rate
```
N_txns(n, T) ≈ α μ n T + β σ² n² T
```
- Linear term dominates in strong trends
- Quadratic term dominates in choppy markets

### Critical Bracket Spacing
```
δ* ≈ σ² / (2μ)
```
- If δ > δ*: Manageable stack
- If δ < δ*: Stack accumulates unboundedly

### Realized Alpha (Bankable)
```
Alpha_bankable ≈ k σ² n T · [1 - Stack_penalty(n)]
```
where Stack_penalty(n) → 1 as n → ∞

### Optimal SDN
```
n* ≈ argmax_n { Alpha_bankable(n) }
 ≈ 1 / (δ* log(2))
 ≈ 2μ / (σ² log(2))
```

For NVDA 2023 (μ ≈ 1.5, σ ≈ 0.4):
```
n* ≈ 2(1.5) / (0.16 × 0.693) ≈ 3 / 0.111 ≈ 27
```

Suggests **sd16-sd32 range**, but sd32 requires infeasible margin!

**Practical optimum**: **sd8-sd16** balancing alpha capture with stack manageability.

---

## Next Steps

1. **Rigorous proof** of 50% margin bound for downtrends
2. **Numerical verification** of critical δ* formula
3. **Stochastic simulation** of continuous model (Euler-Maruyama)
4. **Optimal control formulation**: Dynamic bracket adjustment
5. **Extension to regime-switching**: Different dynamics for bull/bear markets

## Key Takeaway

**The continuous model reveals**:
- Tight brackets (sd32) are only "optimal" in the unrealistic infinite-liquidity limit
- Real-world constraints (margin, stack accumulation) favor **sd8-sd16**
- The algorithm transitions from volatility harvesting to leveraged accumulation at δ ≈ δ*
