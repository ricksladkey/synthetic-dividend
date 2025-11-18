# Strategic Analysis: Experiments & Infrastructure

**Analysis Date**: 2025-10-26

This document analyzes the 120 brainstormed experiments to identify:
1. **Ideal challenges to attack first** (maximum insight, minimum effort)
2. **Infrastructure gaps** preventing efficient research

---

## Top 10 Experiments to Attack First

These experiments offer the best **insight-to-effort ratio** and build foundational knowledge:

### 🥇 #1: Experiment #1 - Gap Frequency Distribution
**Why it's ideal:**
- [OK] **Foundational**: Validates core gap bonus theory with hard data
- [OK] **Easy**: Just analyze existing transaction logs from research_phase1_1year_core.csv
- [OK] **High Impact**: Answers "How often do multi-bracket gaps actually occur?"
- [OK] **Enables Others**: Data feeds into Exp #2, #6, #8, #12

**What we'd learn:**
- Empirical gap distribution by asset (1%, 5%, 10%, 20% gaps)
- Which assets are "gap leaders" (MSTR 234x multiplier - why?)
- Whether gap frequency correlates with volatility (test the hypothesis)

**Estimated effort**: 2 hours (write analysis script, generate charts)

---

### 🥈 #2: Experiment #11 - SD Parameter Sweep
**Why it's ideal:**
- [OK] **Practical Value**: Answers "What's the optimal SD for each asset?"
- [OK] **Already 90% done**: We have research_phase1_1year_core.csv with sd4-sd12 data
- [OK] **Visual Impact**: Can generate heat maps showing optimal zones
- [OK] **Validates Gap Bonus Theory**: Does MSTR prefer sd10 or sd12? Why?

**What we'd learn:**
- Optimal SD by asset class (crypto vs tech vs indices)
- Whether gap-adjusted formula (Exp #12) is needed
- Transaction count saturation point (Exp #18)

**Estimated effort**: 3 hours (already have data, need visualization + analysis)

---

### 🥉 #3: Experiment #21 - Profit Sharing Sweep (0-100%)
**Why it's ideal:**
- [OK] **User-Facing**: Everyone asks "What profit sharing % should I use?"
- [OK] **Easy to Run**: Batch comparison with 5 values × 10 assets = 50 backtests
- [OK] **Frontier Analysis**: Plot cash flow vs total return - beautiful visualization
- [OK] **Surprising Results**: We already know 100% sometimes beats 0% (market timing!)

**What we'd learn:**
- Optimal profit sharing by investment goal (income vs growth)
- Whether high-vol assets benefit from low % (counterintuitive finding?)
- Cash generation vs growth tradeoff quantified

**Estimated effort**: 4 hours (run backtests, create frontier plot, summarize)

---

### #4: Experiment #36 - Safe Withdrawal Rate Discovery
**Why it's ideal:**
- [OK] **Retirement Planning**: The killer use case for synthetic dividends
- [OK] **Quantitative Answer**: Replace "about 4%" with exact numbers by asset
- [OK] **Builds on #21**: Profit sharing × withdrawal rate interaction
- [OK] **Real-World Value**: Helps users design portfolios

**What we'd learn:**
- Maximum sustainable withdrawal rate by asset (VOO: 4.5%? NVDA: 6%?)
- Coverage ratio boundaries (when does bank deplete?)
- Which assets are retirement-ready

**Estimated effort**: 5 hours (grid search, coverage analysis, write-up)

---

### #5: Experiment #51 - Asset Class Leaderboard
**Why it's ideal:**
- [OK] **Quick Win**: Rank 12 assets by volatility alpha - one table!
- [OK] **Data exists**: Use research_phase1_1year_core.csv
- [OK] **Marketing Gold**: "Crypto generates 15x more alpha than bonds"
- [OK] **Informs Portfolio Design**: Exp #61-65 need this data

**What we'd learn:**
- Asset class hierarchy (crypto > tech > indices > commodities > bonds?)
- Whether volatility predicts alpha ranking
- Outliers (assets that punch above/below weight)

**Estimated effort**: 1 hour (sort CSV, make table, done!)

---

### #6: Experiment #8 - Transaction Multiplier by Asset Class
**Why it's ideal:**
- [OK] **Gap Bonus Validation**: Directly tests "234x for MSTR" finding
- [OK] **One Metric**: Actual transactions ÷ Theoretical transactions
- [OK] **Asset Class Pattern**: Do all crypto show 100x+? All indices show 2x?
- [OK] **Feeds Theory**: Helps derive gap-adjusted SD formula (Exp #12)

**What we'd learn:**
- Whether multiplier is asset-specific or class-specific
- Predictability of transaction count from volatility alone
- Boundaries (minimum 1x, maximum 300x?)

**Estimated effort**: 2 hours (calculate multipliers, group by class, visualize)

---

### #7: Experiment #37 - Withdrawal Rate Grid (3-6%)
**Why it's ideal:**
- [OK] **Builds on #36**: Comprehensive coverage ratio analysis
- [OK] **Table-Friendly**: 4 rates × 10 assets = 40-cell table
- [OK] **Coverage Ratio Zones**: Define "excellent" (>150%), "good" (100-150%), etc.
- [OK] **Practical Guidance**: Helps users choose withdrawal rate

**What we'd learn:**
- Coverage ratio distribution by rate and asset
- Bank depletion thresholds
- Safe vs marginal vs unsustainable zones

**Estimated effort**: 4 hours (grid backtests, heatmap, analysis)

---

### #8: Experiment #54 - 2022 Bear Market Test
**Why it's ideal:**
- [OK] **Stress Test**: Does algorithm protect in -20% market?
- [OK] **Recession Resilience**: Which assets maintain alpha when S&P crashes?
- [OK] **Real Data**: Specific historical period (Jan-Dec 2022)
- [OK] **User Confidence**: "Backtested through bear market" = credibility

**What we'd learn:**
- Whether volatility alpha increases in crashes (hypothesis: yes)
- Which assets are defensive (GLD? BIL?)
- Bank balance behavior during prolonged downturns

**Estimated effort**: 3 hours (run 2022 backtests, compare to 2024 bull market)

---

### #9: Experiment #15 - ATH-Only Comprehensive Baseline
**Why it's ideal:**
- [OK] **Baseline for All**: Every volatility alpha calc needs this
- [OK] **Gap Bonus Isolation**: ATH-only = no buybacks = no gap bonus
- [OK] **Algorithm Variant**: Validates the buyback mechanism's value
- [OK] **Systematic**: 12 assets × 6 SD values = 72 baselines

**What we'd learn:**
- ATH-only returns across assets (the "simple" strategy)
- How much alpha buybacks actually add (9.59% for NVDA)
- Whether any assets don't benefit from buybacks (smooth trends?)

**Estimated effort**: 5 hours (batch run, compare to enhanced, document)

---

### #10: Experiment #52 - Correlation Matrix
**Why it's ideal:**
- [OK] **Portfolio Theory**: Foundation for multi-asset portfolios
- [OK] **Uncorrelated Income**: Find assets with opposite income timing
- [OK] **Visual Impact**: Beautiful correlation heatmap
- [OK] **Enables #61-65**: All portfolio experiments need this

**What we'd learn:**
- Which asset pairs have negative income correlation (NVDA/GLD?)
- Whether crypto and equities correlate (probably yes)
- Best diversification pairs for stable income

**Estimated effort**: 4 hours (extract income series, calculate correlations, visualize)

---

## Infrastructure Gaps Preventing Efficient Research

Looking at the 120 experiments, several **missing infrastructure pieces** make complex questions harder than they should be:

### Gap #1: Batch Experiment Runner
**What's missing:**
```python
# Should be this simple:
runner = ExperimentRunner()
runner.run_grid(
 tickers=['NVDA', 'VOO', 'GLD'],
 strategies=['sd6', 'sd8', 'sd10', 'sd12'],
 profit_sharing=[0, 25, 50, 75, 100],
 start_date='2023-01-01',
 end_date='2024-01-01'
)
# Get: 3 tickers × 4 SD × 5 profit = 60 backtests automatically
```

**Current state:** Have to run each backtest manually or write custom batch scripts

**Impact:** Experiments #11, #21, #31, #37, #66 all need this

**Implementation:**
- Create `src/experiments/batch_runner.py`
- Support parameter grids (Cartesian product)
- Parallel execution (utilize all CPU cores)
- Progress tracking and caching

---

### Gap #2: Transaction Log Analysis Tools
**What's missing:**
```python
# Should be able to do:
log = TransactionLog.from_backtest(backtest_result)

# Gap analysis
gaps = log.analyze_gaps()
print(gaps.frequency_by_magnitude()) # 1%, 5%, 10%, 20%
print(gaps.multi_bracket_gaps()) # Count 2+, 3+, 4+ bracket gaps
print(gaps.overnight_vs_intraday()) # Where do gaps come from?

# Income analysis
income = log.analyze_income()
print(income.monthly_distribution())
print(income.coefficient_of_variation())
```

**Current state:** Transaction data exists in backtest results but not easily queryable

**Impact:** Experiments #1, #3, #6, #14, #29, #42, #86, #87 all need this

**Implementation:**
- Create `src/analysis/transaction_log.py`
- Parse transaction lists into pandas DataFrame
- Add gap detection logic (compare consecutive prices)
- Add income smoothing metrics

---

### Gap #3: Result Aggregation & Comparison Framework
**What's missing:**
```python
# Should be able to do:
results = ExperimentResults.load_many([
 'exp11_nvda_sweep.csv',
 'exp11_voo_sweep.csv',
 'exp11_gld_sweep.csv'
])

# Compare across dimensions
results.compare_by('ticker', metric='volatility_alpha')
results.compare_by('sd_n', metric='total_return')
results.plot_heatmap(x='ticker', y='sd_n', value='alpha')
results.generate_markdown_report('exp11_summary.md')
```

**Current state:** Manual CSV munging for each comparison

**Impact:** Every experiment needs this for analysis

**Implementation:**
- Create `src/analysis/results.py`
- Unified CSV schema for all experiments
- Comparison utilities (group by, pivot, aggregate)
- Visualization templates (heatmaps, line plots, distributions)

---

### Gap #4: Metric Calculator Suite
**What's missing:**
```python
# Currently missing from backtest.py:
summary = backtest(...)

# Should include:
print(summary['max_drawdown']) # NOT IMPLEMENTED
print(summary['sharpe_ratio']) # NOT IMPLEMENTED
print(summary['sortino_ratio']) # NOT IMPLEMENTED
print(summary['calmar_ratio']) # NOT IMPLEMENTED
print(summary['alpha_per_transaction']) # NOT IMPLEMENTED
print(summary['income_coefficient_of_variation']) # NOT IMPLEMENTED
```

**Current state:** Only basic metrics (return, alpha, transaction count)

**Impact:** Experiments #28, #96, #97, #98, #99, #14, #29, #87 blocked

**Implementation:**
- Extend `run_portfolio_backtest()` return dict
- Add drawdown tracking to daily loop
- Calculate risk-adjusted metrics
- Add income stability metrics

---

### Gap #5: Portfolio-Level Backtesting
**What's missing:**
```python
# Multi-asset portfolios don't exist yet:
portfolio = Portfolio(
 allocations={
 'NVDA': 0.40,
 'VOO': 0.30,
 'GLD': 0.20,
 'BIL': 0.10
 },
 strategies={
 'NVDA': 'sd8',
 'VOO': 'sd10',
 'GLD': 'sd16',
 'BIL': 'sd20'
 },
 rebalancing='NAV_OPPORTUNISTIC' # From PORTFOLIO_ABSTRACTION.md
)

results = backtest_portfolio(portfolio, start, end)
```

**Current state:** Only single-asset backtests, manual portfolio construction

**Impact:** Experiments #48, #52, #61-65, #101-105 all blocked

**Implementation:**
- Implement PORTFOLIO_ABSTRACTION.md design
- Create `src/models/portfolio.py`
- Unified bank across assets
- Cross-asset NAV arbitrage
- Rebalancing strategies (Simple, NAV Opportunistic, Target Allocation)

---

### Gap #6: Experiment Template System
**What's missing:**
```bash
# Should be able to bootstrap experiment:
$ ./synthetic-dividend-tool.bat experiment create gap-frequency
# Creates:
# experiments/exp01_gap_frequency/
# ├── run.bat
# ├── analyze.py (template with TODOs)
# ├── SUMMARY.md (template)
# └── data/ (empty)

$ cd experiments/exp01_gap_frequency
$ ./run.bat # Executes experiment
# Outputs:
# data/gaps.csv
# results/gap_distribution.png
# SUMMARY.md (filled in)
```

**Current state:** Every experiment requires manual scaffolding

**Impact:** Slows down ALL experiments, reduces reproducibility

**Implementation:**
- Add `experiment create <name>` to CLI tool
- Template files with standard structure
- Makefile-style dependencies
- Auto-generate SUMMARY.md outline

---

### Gap #7: Time-Series Analysis Tools
**What's missing:**
```python
# For analyzing bank balance, holdings, income over time:
timeseries = TimeSeriesAnalyzer(backtest_result)

# Bank trajectory
timeseries.plot_bank_balance()
timeseries.bank_depletion_events() # When did bank go negative?
timeseries.bank_growth_rate() # Trend line

# Holdings trajectory
timeseries.plot_holdings_count()
timeseries.shares_sold_per_month()

# Income trajectory
timeseries.monthly_income()
timeseries.income_autocorrelation() # Is income predictable?
```

**Current state:** Summary stats only, no time-series visibility

**Impact:** Experiments #29, #40, #41, #42, #79, #86, #87, #89 need this

**Implementation:**
- Track daily state in backtest (not just summary)
- Create `src/analysis/timeseries.py`
- Plotting utilities for trajectories
- Statistical analysis (trend, autocorrelation, regime detection)

---

## Recommended Implementation Order

### Phase 1: Quick Wins (1 week)
**Goal:** Run top 10 experiments with minimal infrastructure

1. [OK] **Build Gap #2**: Transaction log analyzer (2 days)
 - Enables Exp #1, #6, #8
2. [OK] **Build Gap #3**: Results aggregation (1 day)
 - Enables Exp #11, #21, #51
3. [OK] **Run Experiments #51, #1, #8** (2 days)
 - Asset class leaderboard
 - Gap frequency distribution
 - Transaction multipliers
4. [OK] **Document Results** (1 day)
 - experiments/exp01_gap_frequency/SUMMARY.md
 - experiments/exp08_transaction_multiplier/SUMMARY.md
 - experiments/exp51_asset_leaderboard/SUMMARY.md

**Output:** 3 experiments completed, foundational analysis tools built

---

### Phase 2: Optimization Studies (2 weeks)
**Goal:** Answer "What's optimal?" questions

1. [OK] **Build Gap #1**: Batch experiment runner (3 days)
2. [OK] **Build Gap #4**: Metric calculator suite (2 days)
 - Add max_drawdown, sharpe_ratio, sortino_ratio
3. [OK] **Run Experiments #11, #21, #36, #37** (1 week)
 - SD parameter sweep
 - Profit sharing sweep
 - Safe withdrawal rate
 - Withdrawal rate grid
4. [OK] **Document Results** (2 days)

**Output:** 7 experiments completed (total: 10), optimization guidance for users

---

### Phase 3: Portfolio Infrastructure (3 weeks)
**Goal:** Enable multi-asset research

1. [OK] **Build Gap #5**: Portfolio-level backtesting (2 weeks)
 - Implement PORTFOLIO_ABSTRACTION.md
 - Unified bank, NAV opportunistic rebalancing
2. [OK] **Run Experiments #15, #52, #61** (1 week)
 - ATH-only comprehensive baseline
 - Correlation matrix
 - Equal weight vs cap weight portfolios

**Output:** 10 experiments completed (total: 20), portfolio framework operational

---

### Phase 4: Advanced Analysis (4 weeks)
**Goal:** Deep dives and theory validation

1. [OK] **Build Gap #7**: Time-series analysis (1 week)
2. [OK] **Build Gap #6**: Experiment templates (3 days)
3. [OK] **Run Experiments #2, #12, #14, #54** (2 weeks)
 - Gap magnitude vs volatility
 - Gap-adjusted SD formula
 - Alpha per transaction
 - 2022 bear market stress test
4. [OK] **Theory Papers** (1 week)
 - Update GAP_BONUS_REASSESSMENT.md with empirical findings
 - Write GAP_BONUS_FORMULA.md deriving multiplier formula
 - Update VOLATILITY_ALPHA_THESIS.md with comprehensive validation

**Output:** 24 experiments completed, major theory advancement

---

## TIP: Strategic Insight: The "Infrastructure Flywheel"

Notice the pattern:
- **Early experiments are hard** (manual data wrangling, custom scripts)
- **Infrastructure emerges** from solving concrete problems
- **Later experiments become trivial** (grid search, one-line queries)

**Example progression:**

```
Exp #1 (Manual):
 - Write custom script: analyze_gaps.py
 - Parse CSV manually
 - 4 hours of work

↓ Extract infrastructure ↓

Gap #2: TransactionLog class
 - Reusable gap analysis
 - 30 minutes to add new metric

↓ Compounds ↓

Exp #6 (Automated):
 - log.multi_bracket_gaps()
 - 5 minutes of work
```

**Implication:** First 10 experiments will be **80% infrastructure building**, **20% analysis**. But experiments 11-100 flip to **20% infrastructure**, **80% analysis**.

---

## 🎓 Recommended Attack Sequence

### Week 1: Foundation
- Implement Gap #2 (Transaction log analyzer)
- Implement Gap #3 (Results aggregation)
- Run Exp #51 (Asset leaderboard) - validates infrastructure
- Run Exp #1 (Gap frequency) - uses transaction analyzer
- Run Exp #8 (Transaction multipliers) - uses both tools

**Deliverable:** 3 experiments documented, 2 reusable tools

---

### Week 2-3: Batch Optimization
- Implement Gap #1 (Batch runner)
- Implement Gap #4 (Metrics: drawdown, Sharpe, Sortino)
- Run Exp #11 (SD sweep) - big batch run
- Run Exp #21 (Profit sharing sweep) - another batch run
- Document optimal parameters

**Deliverable:** 5 more experiments (total: 8), batch automation working

---

### Week 4-6: Retirement Planning
- Run Exp #36 (Safe withdrawal rate)
- Run Exp #37 (Withdrawal grid)
- Run Exp #54 (2022 bear market)
- Update EXAMPLES.md with new experimental data
- Marketing materials (blog post on "scientifically derived withdrawal rates")

**Deliverable:** 3 more experiments (total: 11), retirement planning guidance

---

### Month 2: Portfolio Revolution
- Implement Gap #5 (Portfolio framework)
- Run Exp #15 (ATH-only baseline)
- Run Exp #52 (Correlation matrix)
- Run Exp #61 (Portfolio comparisons)
- Proof-of-concept multi-asset retirement portfolio

**Deliverable:** Portfolio system working, 4 more experiments (total: 15)

---

## The "Killer App" Experiment

If I had to pick **ONE** experiment that would demonstrate value immediately:

### Experiment #36+37 Combined: "Retirement Feasibility Study"

**The Question:**
*"Can I retire on $1M using synthetic dividends? What withdrawal rate is safe?"*

**The Output:**
A single comprehensive table:

| Asset | 3% Coverage | 4% Coverage | 5% Coverage | Max Safe Rate | Recommended Strategy |
|-------|-------------|-------------|-------------|---------------|---------------------|
| VOO | 185% [OK] | 122% [OK] | 97% WARNING: | **4.5%** | sd12, 50% profit |
| NVDA | 245% [OK] | 184% [OK] | 147% [OK] | **6.2%** | sd8, 50% profit |
| QQQ | 172% [OK] | 129% [OK] | 103% [OK] | **5.1%** | sd10, 50% profit |
| GLD | 142% [OK] | 106% [OK] | 85% [FAIL] | **4.2%** | sd16, 50% profit |
| BTC | 385% [OK] | 289% [OK] | 231% [OK] | **8.5%** | sd6, 50% profit |

**Why it's the killer app:**
- [OK] Answers THE question every retiree has
- [OK] Quantitative, actionable guidance
- [OK] Demonstrates algorithm's real-world value
- [OK] Differentiates from competitors (no one else has this data)
- [OK] Marketing gold ("Retire with 6% withdrawal on NVDA!")

**Effort:** 6-8 hours (grid search + write-up)

**Impact:** Could drive 100x more user adoption than any other experiment

---

## Summary

**Ideal challenges to attack:**
1. Gap frequency (#1) - foundational data
2. SD parameter sweep (#11) - optimization guidance
3. Profit sharing sweep (#21) - user-facing decision
4. Safe withdrawal rate (#36+37) - **THE killer app**
5. Asset class leaderboard (#51) - quick marketing win

**Infrastructure needed (priority order):**
1. **Transaction log analyzer** (enables 20+ experiments)
2. **Results aggregation** (needed for every experiment)
3. **Batch runner** (makes grids trivial)
4. **Metric calculator** (adds Sharpe, drawdown, etc.)
5. **Portfolio framework** (unlocks 15+ experiments)
6. Time-series analysis (deep dive tool)
7. Experiment templates (quality of life)

**The flywheel:** Build infrastructure while running first 5 experiments. Subsequent experiments get exponentially easier.

**ROI Recommendation:** Start with Exp #36+37 (retirement feasibility). If it takes 8 hours but produces THE table that sells the algorithm, it's worth 10x more than any other single experiment.
