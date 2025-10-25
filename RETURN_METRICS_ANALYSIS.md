# Return Metrics Analysis: Variable Basis Strategies

## The Challenge

When a strategy has **variable capital deployment** (sometimes holding cash, sometimes fully invested), traditional return metrics can be misleading or incomplete.

### Current Implementation
```python
# Simple total return (what we currently calculate)
total_return = (final_value - initial_value) / initial_value

# Time-weighted: annualized geometric return
annualized = (final_value / initial_value) ^ (1 / years) - 1
```

**Problem**: These metrics don't account for how efficiently capital was deployed over time.

## The Scenarios

### Scenario A: Full Investment Strategy
- Day 1-365: 100% invested ($100k in stocks)
- Gains 20% → End value: $120k
- **Total return: 20%**
- **Capital always at risk: $100k**

### Scenario B: Variable Deployment Strategy
- Day 1-182: 50% invested ($50k stocks, $50k cash)
- Day 183-365: 100% invested ($100k stocks)
- Same 20% gain on stock portion → End value: $110k
- **Total return: 10%**
- **Average capital at risk: $75k**

**Question**: Is Scenario B "worse" because it returned 10% instead of 20%? Or is it better because it achieved half the gain with 25% less average risk exposure?

## Proposed Metrics

### 1. Total Return (Current - Keep as Primary)
```python
total_return = (final_value - initial_value) / initial_value
```
**Meaning**: "How much did my portfolio grow?"
**Use**: Primary metric for comparing absolute performance
**Limitation**: Ignores capital efficiency and time-in-market

### 2. Annualized Return (Current - Keep as Primary)
```python
annualized = (final_value / initial_value) ^ (1 / years) - 1
```
**Meaning**: "What was my compound annual growth rate?"
**Use**: Comparing strategies over different time periods
**Limitation**: Still doesn't account for capital utilization

### 3. Time-Weighted Average Return on Deployed Capital (NEW - Supplementary)
```python
# For each day, calculate return on deployed capital only
deployed_capital = holdings * price  # Excludes cash
if deployed_capital > 0:
    daily_deployed_return = (deployed_capital[t] - deployed_capital[t-1]) / deployed_capital[t-1]
    
# Average across all days when capital was deployed
time_weighted_avg_deployed_return = mean(daily_deployed_return for days with deployed_capital > 0)

# Or: weighted by amount of capital deployed
total_capital_days = sum(deployed_capital[t] for each day t)
weighted_avg_return = sum(deployed_capital[t] * daily_return[t]) / total_capital_days
```

**Meaning**: "How efficiently did I use the capital that was actually at risk?"
**Use**: Comparing strategies with different deployment patterns
**Benefit**: Separates timing decisions (when to be in market) from execution quality (returns when in market)

### 4. Capital Utilization Rate (NEW - Supplementary)
```python
avg_deployed_capital = mean(holdings * price for each day)
utilization_rate = avg_deployed_capital / initial_value

# Or: time-weighted version
total_possible_capital_days = initial_value * num_days
actual_capital_days = sum(holdings * price for each day)
utilization_rate = actual_capital_days / total_possible_capital_days
```

**Meaning**: "What percentage of my capital was working for me on average?"
**Use**: Understanding how aggressively the strategy deploys capital
**Interpretation**: 
- 100% = always fully invested
- 50% = half the capital deployed on average
- >100% = using leverage

### 5. Return per Unit of Capital-Time (NEW - Supplementary)
```python
# Capital-time units: dollar-years of exposure
capital_time_units = sum(deployed_capital[day] * (1/365.25) for each day)

# Return efficiency
return_per_capital_time = total_profit / capital_time_units
```

**Meaning**: "How much profit per dollar-year of capital exposure?"
**Use**: Risk-adjusted performance considering variable deployment
**Example**: 
- $10k profit with $100k deployed for 1 year = $0.10 per dollar-year
- $10k profit with $50k deployed for 1 year = $0.20 per dollar-year (2x more efficient)

## Recommendation: Metrics Suite

### Primary Metrics (Keep Current)
1. **Total Return**: Absolute performance vs buy-and-hold
2. **Annualized Return**: Time-normalized growth rate
3. **Volatility Alpha**: Algorithm return - baseline return

### Supplementary Metrics (Add New)
4. **Capital Utilization Rate**: % of capital deployed on average
5. **Return on Deployed Capital**: Performance when actually in the market
6. **Capital Efficiency Ratio**: Total return / utilization rate

### Example Output
```
Strategy: Synthetic Dividend ATH-Only
================================================
Primary Metrics:
  Total Return:        45.2%
  Annualized Return:   12.3%
  Volatility Alpha:    3.7%
  
Deployment Metrics:
  Avg Capital Utilization:  78.5%
  Return on Deployed Cap:   57.6%  (45.2% / 78.5%)
  Capital Efficiency:       1.28x  (outperformed utilization-adjusted baseline)
  
Capital History:
  Min Deployment:      65.2%  (during drawdown)
  Max Deployment:      95.8%  (during rally)
  Days Fully Invested: 156/365 (42.7%)
```

## When Does This Matter?

### Matters A LOT:
1. **Comparing ATH-only vs Enhanced**: Enhanced has lower deployment (holds more cash from sales)
2. **Comparing different profit-sharing ratios**: Higher ratio → more cash → lower deployment
3. **Evaluating drawdown strategies**: Does buying the dip improve return-per-deployed-capital?

### Matters LESS:
1. **Comparing to buy-and-hold baseline**: Already 100% deployed, so total return is fair comparison
2. **Evaluating pure uptrends**: Both strategies nearly 100% deployed, metrics converge

## Implementation Approach

### Phase 1: Calculate Daily Deployment
```python
# In run_algorithm_backtest, track daily deployment
deployment_history = []  # [(date, deployed_capital), ...]

for date, row in df.iterrows():
    price = row['Close']
    deployed_capital = holdings * price
    deployment_history.append((date, deployed_capital))
```

### Phase 2: Compute Supplementary Metrics
```python
# After main backtest loop
avg_deployed = mean(dep for _, dep in deployment_history)
utilization_rate = avg_deployed / start_val

# Return on deployed capital
return_on_deployed = total_return / utilization_rate if utilization_rate > 0 else 0

summary["capital_utilization"] = utilization_rate
summary["return_on_deployed_capital"] = return_on_deployed
summary["deployment_history"] = deployment_history  # For detailed analysis
```

### Phase 3: Add to Comparison Tools
```python
# In batch_comparison.py results table
columns = [
    "Total Return",
    "Annualized",
    "Volatility Alpha",
    "Capital Utilization",  # NEW
    "Return on Deployed",   # NEW
]
```

## Discussion Questions

1. **Primary vs Supplementary**: Should time-weighted return on deployed capital be **primary** (main metric) or **supplementary** (additional context)?

2. **Weighting Scheme**: Should we weight by time (each day equal) or by capital amount (more weight to days with more capital at risk)?

3. **Cash Treatment**: Should we consider cash as "deployed" (earning risk-free rate) or "undeployed" (idle capital)?

4. **Baseline Adjustment**: Should we compare against a "variable deployment buy-and-hold" baseline that mimics the strategy's deployment pattern but without active trading?

5. **Reporting Complexity**: Are we adding too many metrics, or is this additional insight valuable for understanding strategy behavior?

## My Initial Recommendation

**Supplementary, not primary.** Here's why:

1. **Total return is what matters to investors**: "I started with $100k, ended with $145k, that's a 45% return"

2. **Return on deployed capital is a diagnostic tool**: It helps explain WHY a strategy performed the way it did

3. **Deployment is a strategic choice**: Holding cash is part of the strategy (risk management), not a bug to be adjusted away

4. **Keep it simple**: Primary metrics should be intuitive. Supplementary metrics can be more sophisticated.

**Proposed Solution**: 
- Keep current total_return and annualized as primary metrics
- Add capital_utilization and return_on_deployed_capital as supplementary metrics in summary dict
- Include in detailed output but not in main comparison tables (unless specifically requested)
- Document in a new metrics explanation file

## Next Steps

1. Implement daily deployment tracking in backtest loop
2. Calculate supplementary metrics in summary
3. Add to verbose output / detailed reports
4. Create visualization showing deployment over time
5. Update documentation explaining all metrics

---

**Question for Discussion**: Does this analysis align with your thinking? Would you prefer deployment-adjusted returns as primary or supplementary metrics?
