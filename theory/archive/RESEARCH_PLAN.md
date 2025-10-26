# Scientific Research Plan: Volatility Alpha in Growth Assets

## Executive Summary

This research investigates the systematic extraction of "volatility alpha" from rapidly appreciating assets through rules-based rebalancing strategies. We examine whether optimal rebalancing frequencies exist for different asset volatility profiles and whether these relationships generalize across asset classes.

---

## Research Questions

### Primary Questions

1. **Does optimal rebalancing frequency correlate with asset volatility?**
   - High volatility assets (crypto) → lower N (more frequent rebalancing)?
   - Low volatility assets (indices) → higher N (less frequent rebalancing)?

2. **Does a universal "Goldilocks zone" exist for rebalancing?**
   - Is sd8 (9.05% trigger) universally optimal across asset classes?
   - Or does each volatility tier require different optimal parameters?

3. **Is volatility alpha extraction independent of profit-sharing ratio?**
   - Does optimal sdN remain constant whether profit-sharing is 25%, 50%, or 75%?
   - Or do distribution requirements affect optimal rebalancing strategy?

4. **What is the relationship between transaction frequency and total return?**
   - Is there a point of diminishing returns where more trades = lower alpha?
   - Does this inflection point vary by asset class?

### Secondary Questions

5. **How does volatility alpha compare across time horizons?**
   - 1-year vs. 3-year vs. 5-year backtests
   - Do optimal strategies persist across different market regimes?

6. **What role do drawdowns play in strategy effectiveness?**
   - Does aggressive rebalancing (low N) reduce maximum drawdown?
   - Is there a trade-off between return and drawdown protection?

7. **Can we quantify the "cost of missing volatility"?**
   - Conservative strategies (high N) vs. aggressive (low N)
   - Transaction costs vs. harvesting opportunity

---

## Hypotheses (Testable Predictions)

### H1: Volatility-Optimal Mapping
**Hypothesis**: Optimal rebalancing frequency (sdN) inversely correlates with asset volatility.

**Prediction**:
- Crypto (highest volatility): sd4-sd6 optimal (18.92%-12.25% triggers)
- Growth stocks (high volatility): sd6-sd10 optimal (12.25%-7.18% triggers)
- Indices (moderate volatility): sd12-sd20 optimal (5.95%-3.53% triggers)
- Commodities (low-moderate volatility): sd10-sd16 optimal (7.18%-4.43% triggers)

**Null Hypothesis**: No correlation exists; optimal sdN is random across asset classes.

**Test**: Rank assets by historical volatility (standard deviation of returns), rank by optimal sdN, compute Spearman correlation.

### H2: Universal Goldilocks Zone
**Hypothesis**: sd8 (9.05% trigger, legacy default) represents a universally near-optimal balance.

**Prediction**:
- sd8 will rank in top 3 performers for ≥80% of assets tested
- Performance gap between sd8 and optimal sdN will be <5% for most assets
- sd8 provides robust "one-size-fits-most" solution

**Null Hypothesis**: sd8 is arbitrary; other values perform systematically better.

**Test**: For each asset, calculate rank of sd8 among all tested sdN values. Compute median rank and percentage of assets where sd8 is top-3.

### H3: Profit-Sharing Independence
**Hypothesis**: Optimal rebalancing frequency (sdN) is independent of profit-sharing ratio.

**Prediction**:
- Asset tested with profit-sharing of 25%, 50%, 75% shows same optimal sdN
- Example: If NVDA optimal is sd8 at 50% profit-sharing, it's also sd8 at 25% and 75%
- Transaction count remains primary driver of alpha, not distribution amount

**Null Hypothesis**: Optimal sdN varies with profit-sharing ratio.

**Test**: For subset of assets, run grid search over sdN × profit-sharing. For each profit-sharing level, identify optimal sdN. Check if optimal sdN is constant.

### H4: Diminishing Returns Threshold
**Hypothesis**: Volatility alpha exhibits diminishing returns beyond optimal transaction frequency.

**Prediction**:
- Return curve is concave: increases from sd20→sd8, plateaus, then declines sd6→sd4
- Inflection point (maximum return/transaction ratio) varies by asset
- Over-trading (too low N) reduces alpha due to whipsaw risk

**Null Hypothesis**: More transactions always yield higher returns (monotonic relationship).

**Test**: Plot total return vs. transaction count for each asset. Identify inflection points. Check for inverted-U shape.

---

## Experimental Design

### Asset Selection (Representative Sample)

**Tier 1: Extreme Volatility (Crypto)**
- BTC-USD: Bitcoin (established, highest market cap)
- ETH-USD: Ethereum (second largest, different use case)

**Tier 2: High Volatility (Growth Stocks)**
- NVDA: Nvidia (AI/semiconductor mega-cap)
- MSTR: MicroStrategy (leveraged BTC proxy)
- PLTR: Palantir (emerging tech)
- SHOP: Shopify (e-commerce platform)
- GOOG: Google (tech mega-cap, more stable than others)

**Tier 3: Moderate Volatility (Commodities)**
- GLD: Gold ETF (defensive commodity)
- SLV: Silver ETF (industrial commodity)

**Tier 4: Low-Moderate Volatility (Index ETFs)**
- SPY: S&P 500 (broad market)
- QQQ: Nasdaq 100 (tech-heavy)
- DIA: Dow 30 (blue-chip)

**Total**: 12 assets across 4 volatility tiers

### Parameter Space

**Rebalancing Frequencies (sdN)**:
- sd4 (18.92%): Aggressive
- sd6 (12.25%): Moderately aggressive
- sd8 (9.05%): Balanced (legacy default)
- sd10 (7.18%): Moderately conservative
- sd12 (5.95%): Conservative
- sd16 (4.43%): Very conservative
- sd20 (3.53%): Extremely conservative

**Profit-Sharing Ratios** (for H3 testing):
- Primary: 50% (standard balanced approach)
- Secondary: 25%, 75% (for independence testing on subset)

**Time Horizons**:
- 1-year: 10/22/2024 - 10/22/2025 (recent performance)
- 3-year: 10/22/2022 - 10/22/2025 (includes 2022 bear market)
- 5-year: 10/22/2020 - 10/22/2025 (includes COVID crash and recovery)

### Experimental Matrix

**Phase 1: Core Dataset (1-year horizon)**
- 12 assets × 7 sdN values × 1 profit-sharing (50%) = **84 backtests**
- Runtime: ~20-30 minutes (with caching)
- Output: `research_1year_core.csv`

**Phase 2: Profit-Sharing Independence Test**
- 4 representative assets (NVDA, BTC-USD, GLD, SPY) × 7 sdN × 3 profit-sharing = **84 backtests**
- Runtime: ~20-30 minutes
- Output: `research_profit_sharing_test.csv`

**Phase 3: Extended Time Horizons** (if Phase 1-2 show promising results)
- 12 assets × 7 sdN × 2 additional horizons = **168 backtests**
- Runtime: ~40-60 minutes
- Output: `research_3year.csv`, `research_5year.csv`

**Total**: ~336 backtests across all phases

### Metrics Collected

For each backtest, we collect:

**Performance Metrics**:
- Total return (%)
- Annualized return (%)
- Maximum drawdown (%)
- Sharpe ratio
- Sortino ratio

**Transaction Metrics**:
- Transaction count
- Buy count
- Sell count
- Return per transaction (alpha/trade)

**Position Metrics**:
- Final holdings (shares)
- Starting holdings (shares)
- Position growth rate

**Cash Metrics**:
- Bank min, max, avg
- Days negative/positive
- Opportunity cost
- Risk-free gains

---

## Analysis Plan

### Quantitative Analysis

1. **Correlation Analysis**
   - Asset volatility (std dev of daily returns) vs. optimal sdN
   - Transaction count vs. total return (by asset class)
   - Drawdown vs. rebalancing frequency

2. **Ranking Analysis**
   - For each asset: rank all strategies by total return
   - Identify optimal sdN per asset
   - Check sd8 performance percentile across all assets

3. **Statistical Testing**
   - Spearman correlation: volatility rank vs. optimal sdN rank (H1)
   - Chi-square test: Is sd8 in top-3 more often than random? (H2)
   - ANOVA: Does optimal sdN vary by profit-sharing level? (H3)

4. **Regression Modeling**
   - Predict optimal sdN from: asset volatility, market cap, asset class
   - Identify which variables explain most variance

### Qualitative Analysis

1. **Pattern Recognition**
   - Visual inspection of return curves (sdN vs. return)
   - Identify common shapes: linear, concave, convex, U-shaped
   - Look for regime changes (different patterns in bull vs. bear markets)

2. **Anomaly Detection**
   - Assets that don't fit expected patterns
   - Extreme outliers in transaction count or return
   - Explanation hypotheses for anomalies

3. **Generalization Assessment**
   - Can we create simple heuristic rules?
   - Example: "Use sd(N) where N = asset_volatility / 2"
   - Test heuristic on out-of-sample assets

---

## Expected Outcomes

### If H1 Confirmed (Volatility-Optimal Mapping)
**Implication**: We can provide asset-specific recommendations:
- "For high-volatility tech stocks, use sd6-sd8"
- "For stable index funds, use sd12-sd16"
- Create lookup table or formula for users

### If H2 Confirmed (Universal Goldilocks)
**Implication**: Marketing simplification:
- "Just use sd8 for everything" (80% solution)
- Lower cognitive load for users
- sd8 becomes the branded default

### If H3 Confirmed (Profit-Sharing Independence)
**Implication**: Two-step decision process:
1. Choose sdN based on volatility (harvesting efficiency)
2. Choose profit-sharing based on distribution needs (independent decision)
- Simplifies parameter selection

### If H4 Confirmed (Diminishing Returns)
**Implication**: Warn against over-trading:
- "Don't use sd4 unless extreme volatility"
- Identify transaction cost break-even points
- Guidance on when more rebalancing hurts

### If Hypotheses Rejected
**Value**: Still valuable to know!
- "Optimal rebalancing is asset-specific and unpredictable"
- "Use sd8 as reasonable default, but backtest your specific asset"
- Honesty about limits of generalization

---

## Deliverables

### 1. Data Outputs
- CSV files with full backtest results
- Summary statistics by asset class
- Correlation matrices
- Ranking tables

### 2. Visualizations
- Heatmap: Asset × sdN showing total return
- Scatter plot: Volatility vs. Optimal sdN (test H1)
- Box plots: Return distribution by asset class and sdN
- Line charts: Return curves for each asset (sdN on x-axis)

### 3. Written Analysis
- Research report (markdown format)
- Key findings summary
- Recommendations for users
- Limitations and caveats

### 4. Updated Documentation
- Add empirical findings to RESEARCH.md
- Update README with data-driven recommendations
- Create "Choosing Your Strategy" guide

---

## Timeline

**Week 1**: Data Collection
- Run Phase 1 backtests (1-year core dataset)
- Run Phase 2 backtests (profit-sharing independence)
- Validate data quality

**Week 2**: Analysis
- Statistical testing of H1-H4
- Visualization creation
- Pattern identification

**Week 3**: Documentation
- Write research report
- Update project documentation
- Create user-facing guidance

**Week 4**: Validation & Extension
- Run Phase 3 (extended time horizons) if warranted
- Out-of-sample testing
- Peer review of findings

---

## Funding Justification

This research addresses a fundamental question in systematic investing: **Can we predict optimal rebalancing strategies from asset characteristics?**

**Scientific Contributions**:
1. Novel dataset spanning multiple asset classes and volatility regimes
2. Rigorous hypothesis testing with reproducible methodology
3. Open-source implementation enabling peer verification
4. Practical guidance for retail and institutional investors

**Practical Applications**:
1. Evidence-based strategy selection (not guesswork)
2. Risk-adjusted return optimization
3. Transaction cost minimization
4. Drawdown protection insights

**Broader Impact**:
- Democratizes sophisticated portfolio management
- Reduces reliance on expensive financial advisors
- Provides transparent, rules-based alternative to discretionary trading
- Open-source implementation benefits entire investing community

---

## Risk Factors & Limitations

1. **Survivorship Bias**: Assets selected are currently successful (we don't test delisted stocks)
2. **Backtest Overfitting**: Optimal parameters historically may not persist
3. **Transaction Costs**: Not modeled (assumes zero friction)
4. **Market Regime Dependency**: Bull market results may not generalize to bears
5. **Data Quality**: Relies on Yahoo Finance historical accuracy

**Mitigation**:
- Acknowledge limitations in documentation
- Test across multiple time horizons including bear markets
- Use out-of-sample validation
- Recommend conservative strategy selection (avoid overfitting)

---

**Principal Investigator**: Rick Sladkey  
**Institution**: Open-Source Investing Research  
**Project Duration**: 4 weeks  
**Estimated Compute Time**: ~2-3 hours total runtime  
**Budget**: $0 (uses free data sources and open-source tools)

---

**Status**: Ready to execute  
**Next Action**: Run Phase 1 experiments (84 backtests)

