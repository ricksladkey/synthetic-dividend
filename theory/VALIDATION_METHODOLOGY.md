# Validation Methodology - Statistical Rigor and Objectivity

**Purpose**: Remove hindsight bias and establish mathematical proof that synthetic dividends work across market conditions.

**Problem**: Cherry-picking favorable periods (NVDA 2023 bull run) undermines credibility. We need objective, reproducible validation that holds across:
- Multiple time periods (bull, bear, sideways markets)
- Multiple asset classes (stocks, bonds, crypto, commodities)
- Multiple starting dates (no calendar anchoring)

**Author**: Synthetic Dividend Research Team
**Created**: 2025-10-29
**Status**: Proposed methodology

---

## The Objectivity Problem

### What We're Fighting Against

**Hindsight bias**:
- Picking NVDA for 2023-2024 because we know it went 3x
- Choosing start dates that align with market bottoms
- Selecting assets that happened to be volatile during our test period

**Survivorship bias**:
- Only testing assets that still exist
- Ignoring delisted/bankrupt companies
- Portfolio composition based on current winners

**Period selection bias**:
- Testing on unusually bullish periods (2010-2020)
- Avoiding 2008 financial crisis or 2000 dot-com bubble
- Implicit assumption that past decade represents "normal" markets

### Why This Matters

**For credibility**:
- Academic/financial community dismisses strategies without proper validation
- Investors need confidence the strategy works in *their* future, not our past

**For understanding limits**:
- When does the strategy fail? (sideways markets? hyperinflation?)
- What are realistic expectations? (1-10% alpha, not 100%)
- How much diversification is required?

---

## Validation Approach 1: Rolling Window Analysis

### Core Methodology

**Test a realistic, diversified portfolio across overlapping time windows.**

**Standard portfolio** (can't be cherry-picked):
- 60% VOO (total US stock market)
- 30% BIL (1-3 month T-bills, cash-like)
- 10% BTC-USD (high-volatility alternative)

**Why this portfolio**:
- VOO: Represents "buy the market" baseline
- BIL: Cash buffer (essential for strategy), earns T-bill rate
- BTC: High-volatility asset to test alpha generation
- **No stock-picking**: Can't accuse us of picking winners

### Rolling Window Design

**10 years of data → Multiple overlapping 5-year windows**:

```
2015-2020 (window 1)
2016-2021 (window 2)
2017-2022 (window 3) ← includes 2022 bear market
2018-2023 (window 4)
2019-2024 (window 5)
2020-2025 (window 6)
```

**Key properties**:
- Overlapping windows reduce independence, but increase sample size
- Each window experiences different market regimes
- 2022 bear market appears in windows 3-6
- COVID crash (2020) appears in windows 2-6
- No cherry-picking possible - we test *everything*

### Metrics to Track

**Primary metric**: Volatility alpha (excess return vs buy-and-hold)

**Required for robustness**:
- Alpha mean across all windows
- Alpha standard deviation (consistency)
- Percentage of windows with positive alpha
- Worst-case alpha (risk assessment)
- Best-case alpha (upside potential)

**Secondary metrics**:
- Sharpe ratio improvement
- Maximum drawdown reduction
- Cash flow generation (dividends vs forced sales)
- Transaction count (cost assessment)

### Success Criteria

**Strong evidence** (high confidence):
- ≥80% of windows show positive alpha
- Mean alpha >5% over 5 years
- Standard deviation <5% (consistent across periods)

**Moderate evidence** (promising):
- ≥60% of windows show positive alpha
- Mean alpha >2% over 5 years
- No catastrophic failures (alpha <-10%)

**Weak/inconclusive**:
- <60% positive windows
- High variance (some windows +20%, others -10%)
- Alpha driven entirely by one period (e.g., BTC bull run)

---

## Validation Approach 2: Monte Carlo Bootstrapping

### Core Methodology

**Generate thousands of synthetic market paths that preserve statistical properties of real data.**

**Bootstrap procedure**:
1. Take historical daily returns for VOO, BIL, BTC
2. Estimate correlation matrix and volatility structure
3. Sample with replacement to create new return sequences
4. Run strategy on each synthetic path
5. Aggregate results across 1,000+ simulations

**Why this is more rigorous**:
- Tests strategy on markets we've never seen
- Removes calendar effects and event-driven anomalies
- Provides distribution of outcomes, not just point estimates
- Standard technique in quantitative finance

### Implementation Sketch

**Step 1**: Historical statistics
```python
# Calculate from 10 years of data
daily_returns = {
 'VOO': μ=0.05%, σ=1.2%,
 'BIL': μ=0.01%, σ=0.05%,
 'BTC': μ=0.15%, σ=4.5%
}
correlation_matrix = [[1.0, 0.1, 0.3],
 [0.1, 1.0, 0.0],
 [0.3, 0.0, 1.0]]
```

**Step 2**: Generate synthetic paths
```python
for i in range(1000):
 # Sample returns with replacement
 synthetic_returns = bootstrap_sample(historical_returns)

 # Apply correlations
 correlated_returns = cholesky_decomp(correlation_matrix) @ synthetic_returns

 # Run strategy
 alpha[i] = run_synthetic_dividend(synthetic_portfolio)
```

**Step 3**: Statistical analysis
```python
mean_alpha = np.mean(alpha)
ci_95 = np.percentile(alpha, [2.5, 97.5])
prob_positive = sum(alpha > 0) / 1000

print(f"Expected alpha: {mean_alpha:.2%} [{ci_95[0]:.2%}, {ci_95[1]:.2%}]")
print(f"P(alpha > 0): {prob_positive:.1%}")
```

### Success Criteria

**Strong evidence**:
- P(alpha > 0) ≥ 95%
- 95% confidence interval entirely above 0%
- Mean alpha ≥ 5% over 5 years

**Moderate evidence**:
- P(alpha > 0) ≥ 75%
- Lower bound of 95% CI ≥ 0%
- Mean alpha ≥ 2%

**Weak/inconclusive**:
- P(alpha > 0) < 75%
- Confidence interval includes negative values
- High variance suggests strategy is unstable

---

## Validation Approach 3: Out-of-Sample Testing

### Time-Series Split

**Training period**: 2015-2020 (5 years)
- Use to select optimal rebalancing trigger (sd6? sd8? sd10?)
- Calibrate profit-sharing ratio for target withdrawal rate
- Measure volatility of each asset

**Test period**: 2021-2025 (5 years, completely held out)
- Run strategy with parameters selected from training period
- No peeking, no adjustments
- This is the true test of generalization

**Why this matters**:
- Most strategies fail on out-of-sample data
- If alpha persists on held-out period → not overfit
- Standard practice in machine learning / quant finance

### Walk-Forward Optimization

**Even more rigorous**:
```
Train on 2015-2017 → Test on 2018
Train on 2016-2018 → Test on 2019
Train on 2017-2019 → Test on 2020
...
```

Each test year uses only past data for calibration.

---

## Implementation Roadmap

### Phase 1: Rolling Window Analysis (Immediate)

**Easiest to implement, provides quick validation**:

1. Define standard portfolio (60% VOO, 30% BIL, 10% BTC)
2. Fetch 10 years of daily data (2015-2025)
3. Run 6 overlapping 5-year backtests
4. Calculate alpha statistics across windows
5. Document results in `07-research-validation.md`

**Time estimate**: 1-2 hours of coding, 30 minutes of analysis

**Deliverable**: Table showing alpha across all windows, with mean/std/min/max

### Phase 2: Monte Carlo Bootstrapping (Advanced)

**More complex, but mathematically rigorous**:

1. Implement bootstrap sampling with correlation preservation
2. Generate 1,000 synthetic market paths
3. Run strategy on each path
4. Build distribution of alpha outcomes
5. Calculate confidence intervals and probabilities

**Time estimate**: 4-6 hours of coding, 1-2 hours of analysis

**Deliverable**: Probability distribution chart, confidence intervals, statistical tests

### Phase 3: Mathematical Proof (Theoretical)

**Hardest, but most convincing**:

1. Formalize alpha generation mechanism mathematically
2. Prove under what conditions alpha must be positive
3. Derive bounds on alpha as function of volatility
4. Show convergence properties (longer horizon → more alpha)

**Time estimate**: Weeks (requires deep math)

**Deliverable**: Formal proof that strategy has positive expected value under reasonable assumptions

---

## Avoiding Common Pitfalls

### Pitfall 1: Transaction Costs

**Problem**: Ignoring bid-ask spread and commissions

**Solution**:
- Assume 0.05% per transaction (conservative for modern brokers)
- Penalize high-frequency strategies appropriately
- Report net alpha after costs

### Pitfall 2: Liquidity Constraints

**Problem**: Assuming you can always buy/sell at close price

**Solution**:
- Use realistic execution model (limit orders at OHLC extremes)
- Account for slippage on large positions
- Acknowledge BTC may have higher slippage than VOO

### Pitfall 3: Survivorship Bias

**Problem**: Only testing assets that exist today

**Solution**:
- Use index funds (VOO) which rebalance automatically
- If testing individual stocks, use universe from start date
- Acknowledge limitation in results section

### Pitfall 4: Look-Ahead Bias

**Problem**: Using future data to make past decisions

**Solution**:
- Strict chronological ordering in backtests
- No rebalancing based on future price knowledge
- Walk-forward validation for parameter selection

---

## Statistical Framework

### Hypothesis Testing

**Null hypothesis (H₀)**: Synthetic dividend strategy has zero alpha
**Alternative hypothesis (H₁)**: Synthetic dividend strategy has positive alpha

**Test statistic**: t = (mean_alpha - 0) / (std_alpha / √n)

**Significance level**: α = 0.05 (95% confidence)

**Rejection criterion**: If p < 0.05, reject H₀ and conclude strategy has statistically significant positive alpha

### Effect Size

**Not just statistical significance, but practical significance**:

- 1-2% alpha: Modest but worthwhile
- 5-10% alpha: Substantial advantage
- >10% alpha: Extraordinary (requires skepticism)

**Context matters**:
- 10% alpha on NVDA alone → might be cherry-picking
- 10% alpha on diversified portfolio over 10 years → compelling
- 10% alpha across 100 simulated markets → very strong evidence

---

## Reporting Standards

### Required Disclosure

**All validation results must include**:
1. Exact time period tested
2. Assets and allocations
3. Algorithm parameters (trigger, profit sharing)
4. Transaction costs assumed
5. Comparison baseline (buy-and-hold, 60/40, etc.)
6. Risk metrics (Sharpe, max drawdown, volatility)
7. Sample size (number of windows, simulations, assets)

### Transparency

**Make data and code available**:
- Raw backtest results in CSV format
- Python code for reproduction
- Clear documentation of any data cleaning or adjustments

**Acknowledge limitations**:
- Past performance ≠ future results
- Strategy may fail in unprecedented market conditions
- Requires discipline and automation to execute

---

## Next Steps

1. **Implement rolling window validation** on 60/30/10 VOO/BIL/BTC portfolio
2. **Document results** with full statistical analysis
3. **Compare to traditional 60/40** rebalancing (quarterly)
4. **Test robustness** by varying:
 - Portfolio allocations (50/40/10, 70/20/10)
 - Rebalancing triggers (sd6, sd8, sd10)
 - Profit sharing ratios (25%, 50%, 75%)
5. **If rolling windows succeed**, implement Monte Carlo bootstrapping
6. **If bootstrapping succeeds**, attempt mathematical proof

---

## Success Definition

**Strategy is validated if**:
- ≥75% of rolling windows show positive alpha
- Mean alpha ≥3% over 5-year periods
- Works across multiple market regimes (bull, bear, sideways)
- Alpha increases with holding period (compound effect)
- Results are statistically significant (p < 0.05)

**Strategy is promising but needs more research if**:
- 50-75% of windows show positive alpha
- Mean alpha 1-3% (modest but positive)
- High variance across periods (works sometimes)

**Strategy is questionable if**:
- <50% of windows show positive alpha
- High sensitivity to parameters (overfit)
- Alpha driven by single asset or period (not robust)

---

## Mathematical Conjecture to Prove

**Central claim**: For any asset with mean-reverting volatility around positive drift, the synthetic dividend strategy generates positive expected alpha that compounds over time.

**Formal statement**:
```
Let:
- μ = expected daily return (drift)
- σ = daily volatility (standard deviation)
- r = rebalancing trigger (e.g., 9.05%)
- N = number of rebalancing events

Then:
Expected_Alpha ≈ (r²/2) × N × f(σ,μ)

Where f(σ,μ) > 0 when σ > threshold(μ)
```

**Intuition**:
- Strategy profits from round trips (buy low, sell high)
- Each round trip captures ~r²/2 of move
- Higher volatility → more round trips
- Positive drift → each round trip has positive expected value
- Longer holding period → more round trips → more alpha

**To prove**: Derive f(σ,μ) explicitly and show conditions for f > 0.

---

## Conclusion

Moving from cherry-picked demonstrations to rigorous validation requires:
1. **Objectivity**: No hindsight bias in asset/period selection
2. **Robustness**: Strategy works across market conditions
3. **Statistical rigor**: Proper hypothesis testing and confidence intervals
4. **Transparency**: Full disclosure of methods and limitations

**The goal**: Prove that synthetic dividends aren't just a lucky backtest, but a mathematically sound strategy with predictable, repeatable alpha generation.
