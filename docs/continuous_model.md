# Continuous Model for Synthetic Dividend Algorithm

## Motivation

Rather than simulating discrete transactions penny-by-penny, we seek a continuous model amenable to calculus and analysis. This allows us to derive theoretical properties and scaling relationships.

## Model Setup

### Price Process

Assume the stock price follows a geometric Brownian motion:

```
dS(t) = μ S(t) dt + σ S(t) dW(t)
```

where:
- `S(t)` = stock price at time t
- `μ` = drift (expected return)
- `σ` = volatility (annualized)
- `W(t)` = Wiener process (Brownian motion)

### Bracket System

The algorithm creates symmetric buy/sell triggers spaced at:

```
Bracket spacing: δ = 2^(1/n) - 1
```

For SDN parameter `n`:
- sd4: δ = 18.92%
- sd8: δ = 9.05%
- sd16: δ = 4.43%
- sd32: δ = 2.19%

Triggers at price levels:
```
S_k = S_0 · exp(k · log(1 + δ))  for k ∈ ℤ
```

### Transaction Rate

The rate of crossing bracket boundaries depends on:
1. **Volatility**: Higher σ → more crossings
2. **Bracket spacing**: Smaller δ → more crossings
3. **Drift**: Drift μ creates directional bias (more buys if μ > 0)

For small time intervals, the expected number of crossings scales as:

```
E[crossings] ∝ σ / δ
```

This suggests transaction count should scale as:

```
Transactions ∝ (σ/δ) · T ∝ (σ · n · log(2)) · T
```

where T is the time period.

## Key Questions for the Continuous Model

### 1. Transaction Count Scaling

**Empirical observation**: Transactions appear to scale as O(n²) for SDN parameter n.

**Hypothesis**: For a trending market with volatility σ, the transaction count is:

```
N_txns(n) ≈ α · n² · σ² · T
```

where α is a constant depending on the drift-to-volatility ratio μ/σ.

### 2. Margin Bound

**Claim**: "Even if price goes straight to zero, we only share half the losses with the position."

**Analysis needed**:
- In a pure downtrend (price → 0), we buy on every dip
- Dollar-cost averaging effect: average purchase price < initial price
- Need to derive maximum possible margin usage

For a downtrend from S₀ to S_final = ε ≈ 0:
- Number of brackets crossed: `k ≈ log(S₀/ε) / log(1+δ) ≈ log(S₀/ε) / δ`
- Shares accumulated: Sum of geometric series
- Cash used: Integral of purchase prices

**Conjecture**: Maximum margin usage = 50% of initial position value for pure downtrend.

### 3. Stack Dynamics

Define:
- `H(t)` = total holdings at time t
- `B(t)` = buyback stack size at time t
- `C(t)` = cash/bank balance at time t

The stack accumulation rate depends on:
```
dB/dt = rate_buy(S, dS/dt) - rate_sell(S, dS/dt)
```

For an uptrend (dS/dt > 0):
- Buys triggered on small pullbacks
- Sells triggered when price recovers
- Net effect: B(t) accumulates if drift >> volatility

### 4. Realized Alpha Optimization

**Goal**: Find optimal n that maximizes realized (bankable) alpha.

**Trade-off**:
- Small n (wide brackets): Few transactions, less alpha capture
- Large n (tight brackets): Many transactions, but stack accumulates
- Optimal n*: Balances alpha capture with stack manageability

**Continuous formulation**:
```
Realized_Alpha(n) = ∫₀ᵀ α(t, n) · unwinding_rate(t, n) dt
```

where:
- `α(t, n)` = instantaneous alpha per transaction
- `unwinding_rate(t, n)` = rate at which stack is liquidated

## Empirical Observations (NVDA 2023)

From `scripts/debug_stack.py`:

| SDN | Txns | Txns/n² | Stack | Bank | Realized α |
|-----|------|---------|-------|------|------------|
| 4   | 7    | 0.44    | 0     | +$109K | 0.00% |
| 8   | 24   | 0.38    | 44    | +$119K | 1.98% |
| 16  | 403  | 1.57    | 116   | +$94K  | 18.59% |
| 32  | 2677 | 2.61    | 112K  | -$4.1M | 32.81% |

**Key insights**:
1. Txns/n² increases with n (not constant!)
2. Stack explodes at sd32 (leveraged accumulation)
3. Margin bound fails catastrophically for sd32 in uptrend
4. Realized alpha peaks at sd16-32, but sd32 requires unsustainable margin

## Next Steps for Continuous Model

1. **Derive transaction rate** as function of (μ, σ, δ, T)
2. **Prove margin bound** for pure downtrend scenario
3. **Model stack accumulation** in trending markets
4. **Find optimal δ*** that maximizes realized alpha subject to margin constraint
5. **Compare continuous predictions** to discrete simulation results

## Mathematical Tools Needed

- **Stochastic calculus**: For modeling price crossings of fixed barriers
- **First passage time theory**: Expected time to cross bracket boundaries
- **Renewal theory**: For counting bracket crossings
- **Optimal stopping**: For determining when to tighten/widen brackets

## Open Questions

1. Why does Txns/n² increase with n? (Suggests non-linear interaction with volatility)
2. Can we derive a closed-form expression for margin usage in uptrends?
3. What is the theoretical maximum realized alpha for given (μ, σ, T)?
4. How does the optimal n* depend on the Sharpe ratio μ/σ?
