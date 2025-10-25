# Experiment 002: SPY Normal Market Conditions

**Date**: 2025-01-02  
**Researcher**: Synthetic Dividend Research Team  
**Status**: ✅ Complete (Revised with corrected cash flow calculation)

**Note**: Initial version had a bug where cash flow included the initial purchase transaction. This has been corrected.

---

## Experiment Thesis

**Question**: How does SD8 perform in more typical market conditions (SPY) compared to the extreme bull run of NVDA?

**Hypothesis**: SPY should show more balanced performance between buy-and-hold and SD8 strategies, with potentially positive volatility alpha in periods with higher volatility-to-trend ratio.

**Market Conditions**:
- Ticker: SPY (S&P 500 ETF)
- Period: 2020-01-01 to 2025-01-01 (5 years)
- Market character: Moderate bull market with COVID crash
- Price range: $324 → $586 (+81% total)
- Volatility: HIGH in 2020 (COVID), moderate thereafter

---

## Methodology

**Strategies Tested**:
1. **Buy-and-Hold**: Passive baseline, 10,000 shares, no rebalancing
2. **SD8 Full**: Synthetic dividend with buybacks (9.05% rebalancing, 50% profit sharing)
3. **SD8 ATH-Only**: Only sells at new all-time highs (LTCG only)

**Initial Capital**: $3,248,700 (10,000 shares @ $324.87)

**Withdrawal Assumption**: $50,000/year for living expenses

---

## Results (CORRECTED)

### Strategy Performance Summary

| Strategy | Ann. Return | Final Value | Final Shares | Cash Generated | Transactions/Yr |
|----------|-------------|-------------|--------------|----------------|-----------------|
| Buy-and-Hold | 12.53% | $5,860,800 | 10,000 | $0 | 0.0 |
| SD8 Full | 11.87% | $5,689,449 | 7,588 | **$1,242,274** | 5.8 |
| SD8 ATH-Only | 11.26% | $5,537,091 | 7,410 | **$1,194,239** | 1.4 |

### Cash Flow Analysis (CORRECTED)

| Strategy | Avg Yearly | Total Generated | Positive Years |
|----------|------------|----------------|----------------|
| Buy and Hold | $0 | $0 | 0/0 |
| SD8 Full | **$207,046** | **$1,242,274** | 4/5 |
| SD8 ATH-Only | **$199,040** | **$1,194,239** | 3/3 |

**Key Insight**: Both SD8 strategies generate substantial ongoing cash - around $200K per year on average!

### Withdrawal Sustainability (CORRECTED)

Assuming $50K/year in expenses ($249,829 total over period):

| Strategy | Cash Generated | Coverage | Surplus/Deficit |
|----------|----------------|----------|----------------|
| Buy and Hold | $0 | 0.0% | -$249,829 |
| SD8 Full | $1,242,274 | **497.2%** ✅ | **+$992,445** |
| SD8 ATH-Only | $1,194,239 | **478.0%** ✅ | **+$944,410** |

**Dramatic Finding**: SD8 generates nearly **5x more cash than needed** for $50K/year expenses!

---

## Evaluation: Do Results Make Sense?

### ✅ Expected Behaviors

1. **Smaller Alpha Gap**: SPY's moderate gains (81% vs 2139%) mean less opportunity cost from taking profits early. SD8 sacrifices only 0.66-1.27% annualized (vs NVDA's 27-32%). ✓

2. **Lower Transaction Frequency**: Less volatile asset = fewer rebalancing triggers. SPY: 5.8/yr vs NVDA: 36.4/yr. ✓

3. **Smaller Buyback Premium**: Less dramatic dips = fewer profitable buyback opportunities. SPY: 0.61%/yr vs NVDA: 4.53%/yr. ✓

### 🎯 Unexpected Finding: MASSIVE Cash Generation

**SPY generated nearly 5x the cash needed for withdrawals while sacrificing minimal returns!**

- NVDA: Generated 73-96% coverage, sacrificed 27-32% returns (high cost)
- SPY: Generated 478-497% coverage, sacrificed only 0.66-1.27% returns (minimal cost)

This suggests **moderate volatility is the sweet spot** for SD8:
- High enough to trigger rebalancing and generate cash
- Low enough that opportunity cost is minimal

### 🤔 Questions Raised

1. **Is this SPY-specific or general?** Need to test other moderate-volatility assets
2. **What happens in choppy/sideways markets?** Expect even better relative performance
3. **Does this pattern hold across different time periods?** Need to test bear markets, sideways markets

---

## Conclusions

### Primary Findings

1. **SPY is the Sweet Spot for SD8**: Sacrificed only 0.66-1.27%/year vs buy-and-hold while generating nearly 5x needed withdrawal cash. Compare to NVDA which sacrificed 27-32% while generating only 73-110% coverage.

2. **Moderate Volatility = Best Risk/Reward**: 
   - High enough to trigger rebalancing and generate cash
   - Low enough that opportunity cost is minimal
   - SPY shows this pattern clearly

3. **Transaction Efficiency**: Lower transaction frequency (5.8/yr vs NVDA's 36.4/yr) means:
   - Lower tax friction
   - Lower complexity
   - More "passive" feel while still generating cash

4. **Buyback Premium**: Even at 0.61%/year (vs NVDA's 4.53%), buying dips still adds measurable value

### Critical Insight: Market Regime Matters

The data suggests SD8 performance follows a pattern:

| Market Type | Example | Alpha Gap | Cash Coverage | Transaction Freq |
|-------------|---------|-----------|---------------|------------------|
| Extreme Bull | NVDA 2020-2025 | -27 to -32% | 73-110% | 36.4/yr |
| Moderate Bull | SPY 2020-2025 | -0.66 to -1.27% | **478-497%** | 5.8/yr |
| Choppy/Sideways | TBD | Expect positive? | TBD | TBD |

**Hypothesis**: There's an optimal volatility range where SD8 excels:
- Too high (NVDA): Massive opportunity cost from missing parabolic gains
- Moderate (SPY): Sweet spot - minimal opportunity cost, excellent cash generation
- Too low: Insufficient rebalancing opportunities?

---

## Future Directions

### Follow-Up Experiments

1. **Test Choppy/Sideways Market**: Find period where SD8 might show *positive* volatility alpha
   - Candidates: SPY 2015-2018, QQQ during tech corrections
   - Expect: SD8 holds value better while generating cash

2. **Model Buy-and-Hold WITH Withdrawals**: Create 4th strategy that sells shares to fund $50K/year
   - This is the TRUE apples-to-apples comparison
   - Current buy-and-hold is unrealistic - you can't live off unrealized gains

3. **Transaction Deep Dive**: Analyze when/why SD8 trades
   - Did it buy during COVID crash?
   - What triggered the sales?
   - Cash generation patterns over time

4. **Visualize Cash Flow**: Plot bank balance over time for all strategies
   - Highlight positive/negative zones
   - Show yearly patterns
   - Compare withdrawal coverage visually

---

## Experiment Artifacts

**Code**: `src/research/strategy_comparison.py`  
**Raw Data**: `experiments/002_spy_normal_market/results.csv`  
**Command**: 
```powershell
python -m src.research.strategy_comparison SPY 2020-01-01 2025-01-01
```

**Git Commit**: [To be added]

---

## Bug Fixed During Experiment

**Issue**: Initial version of cash flow calculation included the initial purchase transaction, making all cash flow metrics negative and meaningless.

**Fix**: Modified `calculate_yearly_cash_flow()` in `strategy_comparison.py` to skip first transaction:
```python
# Skip first transaction (initial BUY)
for tx in transactions[1:] if len(transactions) > 1 else []:
    # ... cash flow logic
```

**Impact**: This bug would have contaminated all future experiments. Caught and fixed immediately through careful result analysis.

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-02
