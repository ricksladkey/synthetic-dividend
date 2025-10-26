# Synthetic Dividend Theory Documentation# Synthetic Dividend Algorithm - Theoretical Framework



**Complete theoretical framework** for the Synthetic Dividend Algorithm - a rules-based strategy that converts price volatility into predictable cash flow.This folder contains the complete conceptual and theore5. Review `RETURN_METRICS_ANALYSIS.md` - Learn proper interpretation

6. Study `INITIAL_CAPITAL_THEORY.md` - Understand opportunity cost nuances

---7. Read `PRICE_NORMALIZATION.md` - Learn about deterministic brackets

8. Study `WITHDRAWAL_POLICY.md` - Understand orthogonal withdrawal design

## Quick Start9. Explore `PORTFOLIO_VISION.md` - See the long-term vision

10. Reference `CODING_PHILOSOPHY.md` - Internalize development principles

**New to the project?** Start here:

## Key Concepts Across Documents

1. **[INVESTING_THEORY.md](INVESTING_THEORY.md)** (15 min) - Why volatility harvesting works

2. **[VOLATILITY_ALPHA_THESIS.md](VOLATILITY_ALPHA_THESIS.md)** (30 min) - Mathematical proof and validation### Income Generation & Smoothing

3. **[INCOME_GENERATION.md](INCOME_GENERATION.md)** (25 min) - How to generate income from any growth asset

**Irregular → Regular Transformation** (NEW):

**Total**: ~70 minutes for core concepts- Volatility generates cash at unpredictable times (market-driven, lumpy)

- Withdrawals needed at predictable times (lifestyle-driven, regular)

---- Bank balance acts as temporal buffer (smoothing mechanism)

- Coverage ratio measures smoothing effectiveness (>200% = excellent)

## Document Hierarchy

**Sequence-of-Returns Protection** (NEW):

### Tier 1: Core Concepts (Must Read)- Growth stocks particularly vulnerable to early-retirement bear markets

- Bank balance shields against forced sales during drawdowns

These documents explain the fundamental innovation - how to extract cash flow from price volatility while preserving growth exposure.- Goal: Maximize probability of "never selling at a loss"

- Only sell at ATHs + bank buffer during dips = gain-only salesundation for the Synthetic Dividend Algorithm. These documents are designed to be concatenated and used as a comprehensive system prompt for AI assistants or as standalone reference material.

#### [INVESTING_THEORY.md](INVESTING_THEORY.md)

**Purpose**: Foundation - the philosophy and economic principles## Document Overview



**Key Insights**:### Core Theory

- Dividend illusion: All cash withdrawals have opportunity cost (dividends aren't "free")

- Profit sharing: Control income vs growth with one parameter (0% = buy-and-hold, 50% = balanced, 100%+ = de-risking)1. **[INVESTING_THEORY.md](INVESTING_THEORY.md)** - Foundational investment theory

- Time machine effect: Higher profit sharing → proportionally longer to reach goals   - Why traditional dividend strategies fail

- Trigger vs profit sharing: Rebalancing frequency matters far more than profit allocation   - The "selling at strength" principle

   - ATH-only vs Enhanced (with buybacks) strategies

**Read if**: You want to understand *why* this approach works   - Profit sharing ratios and their economic implications

   - Mathematical proofs of key properties

**Reading time**: 15 minutes

2. **[VOLATILITY_ALPHA_THESIS.md](VOLATILITY_ALPHA_THESIS.md)** - Central thesis and mathematics

---   - Definition of volatility alpha

   - Mathematical formulation

#### [VOLATILITY_ALPHA_THESIS.md](VOLATILITY_ALPHA_THESIS.md) ⭐ CENTERPIECE   - Conditions for positive alpha generation

**Purpose**: Mathematical proof that volatility harvesting generates measurable excess returns   - Relationship to exponential scaling

   - Theoretical limits and constraints

**Key Insights**:

- Formula: `Alpha ≈ (trigger%)² / 2 × buy_count` (conservative lower bound)3. **[INCOME_GENERATION.md](INCOME_GENERATION.md)** - ⭐ Income strategy framework

- Four sources: Path exploitation, drawdown recycling, compounding, gap arbitrage   - How volatility becomes cash flow (the core mechanism)

- Empirical validation: 18 scenarios across 6 assets (GLD 1.4% to MSTR 125% alpha)   - Buyback stack as income engine

- Gap bonus: Actual alpha exceeds formula by 1.1x (commodities) to 3.4x (tech)   - Income frequency and reliability

- Visual estimation: Count drawdowns on chart → predict minimum alpha instantly   - Comparison to dividends, covered calls, forced selling

   - Tax efficiency and IRA/Roth killer app

**Read if**: You want mathematical rigor and empirical proof   - Practical implementation guide for income seekers



**Reading time**: 30 minutes4. **[INCOME_SMOOTHING.md](INCOME_SMOOTHING.md)** - ⭐ Temporal arbitrage & sequence-of-returns protection (NEW)

   - Irregular payments → Regular income transformation

---   - Bank balance as temporal buffer (smoothing mechanism)

   - Coverage ratio as smoothing effectiveness metric

#### [INCOME_GENERATION.md](INCOME_GENERATION.md) ⭐ PRACTICAL APPLICATION   - Sequence-of-returns risk mitigation for growth stocks

**Purpose**: Complete guide to converting volatility into predictable cash flow   - "Never forced to sell at a loss" principle

   - Portfolio diversification for robust smoothing

**Key Insights**:   - Graceful degradation to buy-and-hold behavior

- Income mechanism: Volatility in both directions generates cash (bull, bear, sideways)

- Buyback stack: The "volatility battery" that charges during dips, discharges on recovery### Advanced Concepts

- Income smoothing: Bank buffer decouples irregular generation from regular distribution

- Sequence-of-returns protection: Avoid forced selling during crashes (6x reduction in loss-sales)5. **[INITIAL_CAPITAL_THEORY.md](INITIAL_CAPITAL_THEORY.md)** - Opportunity cost framework

- Coverage ratio: Synthetic dividends / withdrawals (>1.0 = self-sustaining)   - Two separate capital streams: equity position vs trading cash flow

- Comparison: Beats dividends, covered calls, forced selling on multiple dimensions   - What we currently track vs what we don't track

   - Conceptual inconsistency in opportunity cost accounting

**Read if**: You need income from growth assets or want retiree-focused strategy   - Three implementation options (with Option A marked as WRONG)

   - Impact on absolute returns vs volatility alpha (alpha unchanged)

**Reading time**: 25 minutes

6. **[PRICE_NORMALIZATION.md](PRICE_NORMALIZATION.md)** - Deterministic bracket placement

---   - Normalizes prices to standard bracket positions (1.0 × (1+r)^n)

   - Makes bracket placement deterministic across backtests

### Tier 2: Implementation Details (Reference)   - Mathematical foundation and implementation

   - Benefits for comparison and analysis

These documents explain specific aspects of the algorithm's implementation and design decisions.   - Usage in backtests and order calculator



#### [WITHDRAWAL_POLICY.md](WITHDRAWAL_POLICY.md)7. **[WITHDRAWAL_POLICY.md](WITHDRAWAL_POLICY.md)** - Orthogonal withdrawal dimension

**Purpose**: How cash withdrawals work across all strategies   - Withdrawals apply uniformly to all strategies

   - Bank-first approach (sell only if needed)

**Key Points**:   - Standard 4% rule with CPI adjustment

- Orthogonal to investment strategy (applies uniformly to all)   - Simple mode for clean testing

- Bank-first approach: Use generated cash, only sell shares if necessary   - Quantifies value of cash generation

- Standard 4% rule with CPI adjustment (maintains purchasing power)

- Reveals value: SD8 maintains position via generated cash, buy-and-hold sells shares relentlessly8. **[PORTFOLIO_VISION.md](PORTFOLIO_VISION.md)** - Multi-stock portfolio strategy (Phase 2 goal)

   - Vision for portfolio-level implementation

**Read if**: Implementing withdrawals or comparing strategy sustainability   - Shared 10% cash reserve across multiple stocks

   - Three-stream capital model: tactical cash + stock positions + trading flow

**Reading time**: 8 minutes   - Portfolio-level opportunity cost tracking

   - Research questions for future work

---

### Practical Framework

#### [RETURN_METRICS_ANALYSIS.md](RETURN_METRICS_ANALYSIS.md)

**Purpose**: How to properly interpret backtest results9. **[RETURN_METRICS_ANALYSIS.md](RETURN_METRICS_ANALYSIS.md)** - Metrics interpretation

   - Primary vs supplementary metrics

**Key Points**:   - Capital utilization and deployment tracking

- Standard metrics: Total return, annualized return (industry standard, keep these)   - "More Shares = Success" fallacy prevention

- Deployment metrics: Capital utilization, return per dollar-day (supplementary)   - Proper interpretation checklist

- Critical for: Strategies with variable cash positions (synthetic dividend, margin-based)   - Variable capital deployment scenarios

- Avoids fallacy: "More shares = better" (wrong - returns matter, not share counts)

10. **[CODING_PHILOSOPHY.md](CODING_PHILOSOPHY.md)** - Development principles

**Read if**: Running backtests or comparing strategies with different deployment patterns   - Test-Driven Trust: tests validate economic behavior

   - Code as documentation

**Reading time**: 7 minutes   - Fail-fast with clear error messages

   - Empirical validation over theory

---   - When to break the rules



#### [PRICE_NORMALIZATION.md](PRICE_NORMALIZATION.md)## Usage as System Prompt

**Purpose**: Why all backtests start at $100

To use these documents as a system prompt for an AI assistant working on the Synthetic Dividend Algorithm:

**Key Points**:

- Normalizes all assets to $100 starting price (deterministic comparisons)### Quick Start (Essential Only)

- Mathematical properties: Returns unchanged, scaling invariant, reversible```bash

- Benefits: Same initial capital across assets, easier mental math, visually comparable chartscat theory/INVESTING_THEORY.md theory/VOLATILITY_ALPHA_THESIS.md > prompt.md

- Implementation: Automatic in data fetcher, transparent to all code```



**Read if**: Understanding backtest setup or implementing new data sources### Comprehensive (Full Context)

```bash

**Reading time**: 5 minutescat theory/INVESTING_THEORY.md \

    theory/VOLATILITY_ALPHA_THESIS.md \

---    theory/INCOME_GENERATION.md \

    theory/INCOME_SMOOTHING.md \

### Tier 3: Advanced Topics (Optional)    theory/INITIAL_CAPITAL_THEORY.md \

    theory/PRICE_NORMALIZATION.md \

These documents explore theoretical edge cases, future directions, and deeper mathematical concepts.    theory/WITHDRAWAL_POLICY.md \

    theory/PORTFOLIO_VISION.md \

#### [INITIAL_CAPITAL_THEORY.md](INITIAL_CAPITAL_THEORY.md)    theory/RETURN_METRICS_ANALYSIS.md \

**Purpose**: Unresolved question about opportunity cost accounting    theory/CODING_PHILOSOPHY.md > full_prompt.md

```

**Key Points**:

- Current: Track opportunity cost on trading cash flow (bank balance)### Recommended Order for Learning

- Missing: Track opportunity cost on initial equity deployment1. Start with `INVESTING_THEORY.md` - Understand the "why"

- Implication: Absolute returns overstated, but volatility alpha unchanged (cancels in subtraction)2. Read `VOLATILITY_ALPHA_THESIS.md` - Grasp the mathematics

- Open question: How to properly account for initial capital vs reference asset (VOO)3. ⭐ Study `INCOME_GENERATION.md` - See the practical application (income from volatility)

4. ⭐ **NEW**: Read `INCOME_SMOOTHING.md` - Understand irregular → regular transformation and sequence-of-returns protection

**Read if**: Curious about opportunity cost modeling or comparing to index funds5. Review `RETURN_METRICS_ANALYSIS.md` - Learn proper interpretation

5. Study `INITIAL_CAPITAL_THEORY.md` - Understand opportunity cost nuances

**Reading time**: 10 minutes6. Read `PRICE_NORMALIZATION.md` - Learn about deterministic brackets

7. Study `WITHDRAWAL_POLICY.md` - Understand orthogonal withdrawal design

---8. Explore `PORTFOLIO_VISION.md` - See the long-term vision

9. Reference `CODING_PHILOSOPHY.md` - Internalize development principles

#### [PORTFOLIO_VISION.md](PORTFOLIO_VISION.md)

**Purpose**: Future vision for multi-asset portfolio implementation## Key Concepts Across Documents



**Key Points**:### The Two Strategies

- Current: Single-asset backtests (one stock at a time)- **ATH-only**: Sell at all-time highs only, never buy back

- Vision: Multi-asset portfolio with shared 10% cash reserve- **Enhanced**: Sell at ATH + buy back during dips (generates volatility alpha)

- Benefits: Diversification + uncorrelated assets → smoother income

- Research questions: Optimal cash reserve, correlation effects, rebalancing triggers### The Three Questions

- **Question A**: "How much money did I make?" (gross return)

**Read if**: Interested in future roadmap or portfolio-level applications- **Question B**: "Did I beat opportunity cost?" (net return after costs)

- **Question C**: "Should I use this vs buy-and-hold?" (volatility alpha)

**Reading time**: 7 minutes

**We're asking Question C, but currently reporting like Question A.**

---

### The Three Capital Streams (Portfolio Vision)

### Archived (Historical Context)1. **Tactical Cash Reserve** (10%) - Strategic buffer, earns 0%, enables buybacks

2. **Stock Positions** (90%) - Equity holdings with opportunity cost vs baseline

**Location**: [theory/archive/](archive/)3. **Trading Cash Flow** (variable) - Algorithm's cash generation from transactions



These documents capture research history and past analyses:### Critical Distinctions

- Research planning and test analysis

- Comparison results and profit-sharing studies**Initial Capital vs Trading Cash Flow**

- See [archive/README.md](archive/README.md) for details- Initial capital = Equity position (what we invest to buy shares)

- Trading cash flow = Bank balance (algorithm's sells/buys)

**Read if**: Understanding project evolution or replicating past experiments- **WRONG**: Starting bank at -$100k (would break bank semantics)

- **RIGHT**: Bank starts at $0, track initial capital opportunity cost separately

---

**Shares vs Returns**

## Reading Paths by Persona- ❌ WRONG: "Enhanced has 7,337 shares vs 7,221, so it's better"

- ✅ RIGHT: "Enhanced returned 45.2% vs 42.1%, so it's better"

### For Investors (70 min)- Share counts are diagnostic, not success metrics

Focus on **practical application** and **empirical results**:

**Opportunity Cost Components**

1. INVESTING_THEORY.md (15 min) - Philosophy and principles- Currently track: Negative bank during trading (when algorithm borrows)

2. VOLATILITY_ALPHA_THESIS.md (30 min) - Proof it works (skip derivation, read validation)- Missing: Initial capital deployment (the $100k equity position)

3. INCOME_GENERATION.md (25 min) - How to generate income from NVDA, BTC, etc.- Impact: Volatility alpha UNCHANGED (cancels in subtraction), but absolute returns overstated



**Outcome**: Understand why volatility = opportunity, how to extract cash flow from growth assets## Mathematical Foundations



---### Exponential Scaling

```

### For Developers (50 min)Next rebalance trigger = Last price × (1 + rebalance_size_pct)

Focus on **implementation** and **metrics**:```



1. INVESTING_THEORY.md (15 min) - Economic modelCommon triggers:

2. PRICE_NORMALIZATION.md (5 min) - Data preprocessing- sd4: 18.92% (4th root of 2)

3. WITHDRAWAL_POLICY.md (8 min) - Withdrawal mechanics- sd6: 12.25% (6th root of 2)

4. RETURN_METRICS_ANALYSIS.md (7 min) - Proper result interpretation- sd8: 9.05% (8th root of 2)

5. VOLATILITY_ALPHA_THESIS.md (15 min) - Skim for parameter selection (sdN guide)- sd10: 7.18% (10th root of 2)



**Outcome**: Implement backtests correctly, interpret results properly### Profit Sharing

```

---Sell Amount = (Holdings × Rebalance %) × (Profit Sharing % / 100)

```

### For Researchers (120 min)

Read **everything** in document order for complete theoretical foundation:- 0%: Never sell (pure buy-and-hold)

- 50%: Balanced (sell half of profit, keep half compounding)

1. INVESTING_THEORY.md (15 min)- 100%: Aggressive cash flow (sell all profit portion)

2. VOLATILITY_ALPHA_THESIS.md (30 min) - Read every derivation- 125%+: Reduce share count (de-risk, harvest gains)

3. INCOME_GENERATION.md (25 min)

4. WITHDRAWAL_POLICY.md (8 min)### Volatility Alpha

5. RETURN_METRICS_ANALYSIS.md (7 min)```

6. PRICE_NORMALIZATION.md (5 min)Volatility Alpha = Algorithm Return - Buy-and-Hold Return

7. INITIAL_CAPITAL_THEORY.md (10 min) - Open research question```

8. PORTFOLIO_VISION.md (7 min) - Future directions

9. Archive docs (13+ min) - Historical contextPositive alpha requires:

1. Volatility (price must oscillate)

**Outcome**: Deep understanding, identify research opportunities, extend the work2. End at new ATH (thesis requirement)

3. Successful buyback unwinding (sell high, buy low)

---

## Evolution of Understanding

### For Retirees (60 min)

Focus on **income generation** and **sequence-of-returns protection**:### Phase 1: Core Algorithm

- Developed ATH-only and Enhanced strategies

1. INVESTING_THEORY.md (15 min) - Dividend illusion, profit sharing- Established exponential scaling principle

2. INCOME_GENERATION.md (25 min) - Full read, especially Parts 2-3 (smoothing + protection)- Validated with backtests across 12 assets

3. VOLATILITY_ALPHA_THESIS.md (20 min) - Skim for frequency selection, empirical validation

### Phase 2: Metrics Refinement

**Outcome**: Design income-focused portfolio, understand protection from early crashes- Added capital utilization tracking

- Recognized "More Shares ≠ Success" fallacy

---- Distinguished primary vs supplementary metrics



## Key Formulas### Phase 3: Opportunity Cost Analysis (Current)

- Identified missing initial capital opportunity cost

### Volatility Alpha (Minimum)- Clarified two-stream model (equity vs trading)

```- Documented three implementation options

Alpha per cycle ≈ (trigger%)² / 2- **Critical fix**: Separated equity position from trading cash flow

Total alpha ≈ buy_count × (trigger%)² / 2

### Phase 4: Portfolio Vision (Future)

Example (SD8 = 9.05% trigger):- Multi-stock portfolio with shared cash reserve

- Per cycle: 0.0905² / 2 ≈ 0.41%- Portfolio-level opportunity cost tracking

- 20 cycles: 20 × 0.41% ≈ 8.2% minimum alpha- Cross-asset cash flow optimization

```- Realistic investment scenario testing



### Time Machine Effect## Common Pitfalls to Avoid

```

Time_to_goal ≈ Buy_and_hold_time / (1 - profit_sharing_ratio)1. **Don't conflate equity position with bank balance**

   - Initial $100k is equity (holdings), not a loan to ourselves

Examples:   - Bank tracks trading cash flow, starts at $0

- 0%:   1.0x time (pure buy-and-hold)

- 50%:  2.0x time (balanced)2. **Don't judge strategies by share counts**

- 75%:  4.0x time (income-focused)   - More shares only matters if returns are better

- 90%: 10.0x time (maximum income)   - Capital utilization explains deployment, not success

```

3. **Don't assume opportunity cost affects alpha**

### Rebalancing Triggers (sdN)   - Alpha = difference in returns (opportunity cost cancels)

```   - But absolute returns are overstated without full accounting

Trigger = 2^(1/N) - 1

4. **Don't treat tactical cash as idle capital**

Common values:   - 10% cash reserve enables buybacks without borrowing

- SD4:  18.92% (4 steps to double)   - Strategic value beyond opportunity cost measurement

- SD6:  12.25% (6 steps to double)

- SD8:   9.05% (8 steps to double)5. **Don't cherry-pick test results**

- SD10:  7.18% (10 steps to double)   - Document all experiments, including failures

- SD12:  5.95% (12 steps to double)   - Empirical validation requires honest reporting

- SD16:  4.43% (16 steps to double)

- SD20:  3.53% (20 steps to double)## Questions This Framework Answers

```

✅ Why sell only at all-time highs? (Never realize losses, only gains)

### Coverage Ratio✅ How do buybacks generate alpha? (Buy low, sell high on volatility)

```✅ What's the optimal profit-sharing ratio? (50% balances cash + growth)

Coverage = Synthetic_dividends_generated / Withdrawals_requested✅ Why does volatility alpha exist? (Harvesting mean reversion)

✅ How to measure capital efficiency? (Utilization + return on deployed)

Interpretation:✅ What's missing in opportunity cost? (Initial capital not tracked)

- > 1.0: Self-sustaining (bank grows)✅ How does portfolio-level strategy work? (Shared cash reserve)

- = 1.0: Balanced (zero net share sales)✅ Is this better than buy-and-hold? (If volatility alpha > 0)

- 0.5-1.0: Partial coverage (some share sales)

- < 0.5: Heavy share depletion## Contributing to This Framework

```

When adding new theoretical insights:

---

1. **Document the "why" not just the "what"**

## The Central Thesis (TL;DR)   - Explain economic intuition

   - Show mathematical derivation

**Traditional view**: Volatility = risk = bad (minimize standard deviation)   - Provide concrete examples



**Our view**: Volatility = harvestable asset class = opportunity2. **Connect to existing concepts**

   - How does this relate to volatility alpha?

**The innovation**: Systematic rebalancing with buyback stack converts price oscillations into:   - Does it change our interpretation of metrics?

1. Measurable excess returns (volatility alpha: 0.5-40% depending on asset volatility)   - What are the portfolio-level implications?

2. Predictable cash flow (irregular generation → smooth distribution via bank buffer)

3. Sequence-of-returns protection (avoid forced sales during crashes)3. **Identify trade-offs**

4. Universal application (works on any volatile asset: stocks, crypto, commodities)   - Every strategy has costs and benefits

   - Make them explicit

**The result**: Turn **any growth asset** into a **predictable income stream** while preserving long-term compound potential.   - Quantify when possible



**Empirically validated**: 18 scenarios across 6 assets, 3 timeframes. Formula predicts minimum alpha within 1.1-3.4x (actual exceeds due to gaps).4. **Update cross-references**

   - Maintain consistency across documents

---   - Update this README.md with new concepts

   - Add to appropriate document section

## Usage as System Prompt

5. **Consider the system prompt use case**

These documents are designed to concatenate for AI assistant context.   - Will an AI assistant understand this standalone?

   - Is the notation consistent across documents?

**Minimal** (core concepts only):   - Are key terms defined before use?

```bash

cat INVESTING_THEORY.md VOLATILITY_ALPHA_THESIS.md > prompt.md---

```

**Last Updated**: October 2025  

**Recommended** (complete foundation):**Status**: Active development (Phase 3: Opportunity Cost Analysis)  

```bash**Next**: Complete initial capital opportunity cost implementation

cat INVESTING_THEORY.md \
    VOLATILITY_ALPHA_THESIS.md \
    INCOME_GENERATION.md \
    WITHDRAWAL_POLICY.md > prompt.md
```

**Comprehensive** (everything):
```bash
cat INVESTING_THEORY.md \
    VOLATILITY_ALPHA_THESIS.md \
    INCOME_GENERATION.md \
    WITHDRAWAL_POLICY.md \
    RETURN_METRICS_ANALYSIS.md \
    PRICE_NORMALIZATION.md \
    INITIAL_CAPITAL_THEORY.md \
    PORTFOLIO_VISION.md > full_prompt.md
```

---

## Document Status

**Last Updated**: October 26, 2025

**Consolidation**: Phases 1-4 complete
- ✅ Archived historical documents (4 files, 1,007 lines)
- ✅ Expanded core thesis (VOLATILITY_ALPHA: 137 → 620 lines)
- ✅ Merged overlapping content (INCOME docs: 2,185 → 850 lines)
- ✅ Streamlined all remaining docs (40.7% total reduction)
- ✅ Hierarchy fixed: Core concepts comprehensive, applications streamlined
- ✅ Zero duplication: Every concept explained once, in best place

**Philosophy**: Every paragraph contains new information. No repetition across documents. Maximum information density.

**See also**: [THEORY_CONSOLIDATION_PLAN.md](../THEORY_CONSOLIDATION_PLAN.md) and [THEORY_CONSOLIDATION_PROGRESS.md](../THEORY_CONSOLIDATION_PROGRESS.md) for consolidation details.

---

**Questions?** Each document includes cross-references to related topics. Start with Tier 1 (core concepts), reference Tier 2 (implementation) as needed, explore Tier 3 (advanced) when curious.
