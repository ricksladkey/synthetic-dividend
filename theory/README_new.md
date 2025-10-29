# Synthetic Dividend Theory Documentation

**Complete theoretical framework** for the Synthetic Dividend Algorithm - a rules-based strategy that converts price volatility into predictable cash flow.

---

## Executive Summary

The Synthetic Dividend Algorithm transforms any volatile asset into a predictable income stream while preserving long-term growth potential. Through systematic rebalancing with strategic buyback mechanisms, it harvests volatility for measurable excess returns (volatility alpha) beyond traditional buy-and-hold strategies.

**Key Innovation**: Four algorithm variants provide different risk/reward profiles:
- **Buy-and-Hold**: Traditional baseline (0% volatility alpha)
- **ATH-Only**: Profit-taking at all-time highs only (path-independent returns)
- **Standard SD**: ATH profit-taking + buybacks during dips (volatility harvesting)
- **ATH-Sell**: Buybacks during dips, but sells only at new all-time highs (maximum compounding)

**Empirical Validation**: 18 scenarios across 6 assets show volatility alpha ranging from 1.4% (GLD) to 125% (MSTR) over 3-year periods.

---

## Document Structure

### 1. Core Concepts (`01-core-concepts.md`)
**Why volatility harvesting works** - Foundational economic principles
- Dividend illusion and opportunity cost
- Time machine effect of profit sharing
- Volatility as harvestable asset class

### 2. Algorithm Variants (`02-algorithm-variants.md`)
**The four strategy implementations** - Complete catalog with mechanics
- Buy-and-Hold: Traditional baseline
- ATH-Only: Profit-taking at all-time highs
- Standard SD: ATH sales + dip buybacks
- **NEW**: ATH-Sell: Dip buybacks, ATH-only resales (maximum compounding)

### 3. Mathematical Framework (`03-mathematical-framework.md`)
**Why it generates excess returns** - Complete mathematical foundation
- Volatility alpha formula: `α ≈ N × (trigger%)² / 2`
- Four sources of alpha generation
- Empirical validation across assets
- Gap bonus and compounding effects

### 4. Income Generation (`04-income-generation.md`)
**How volatility becomes cash flow** - Practical income mechanics
- Buyback stack as income engine
- Irregular → regular income transformation
- Sequence-of-returns protection
- Coverage ratios and sustainability

### 5. Implementation Details (`05-implementation-details.md`)
**How it works in practice** - Technical execution details
- Rebalancing triggers and profit sharing
- Price normalization and bracket placement
- Withdrawal policy and bank mechanics
- Capital utilization and deployment tracking

### 6. Applications & Use Cases (`06-applications-use-cases.md`)
**Real-world applications** - Practical deployment scenarios
- Retirement income generation
- Portfolio diversification strategies
- Risk management and drawdown protection
- Multi-asset portfolio vision

### 7. Research & Validation (`07-research-validation.md`)
**Empirical evidence** - Backtesting results and validation
- 18 scenario validation matrix
- Performance across market conditions
- Comparative analysis vs alternatives
- Future research directions

---

## Quick Start Guide

### For Investors (Income Focus)
1. Read `01-core-concepts.md` (15 min) - Understand the "why"
2. Read `04-income-generation.md` (25 min) - See practical income mechanics
3. Read `02-algorithm-variants.md` (20 min) - Choose your strategy variant

### For Researchers (Technical Deep Dive)
1. Read `01-core-concepts.md` (15 min) - Foundation
2. Read `03-mathematical-framework.md` (30 min) - Mathematical rigor
3. Read `07-research-validation.md` (45 min) - Empirical evidence

### For Developers (Implementation Focus)
1. Read `05-implementation-details.md` (20 min) - Technical details
2. Read `02-algorithm-variants.md` (20 min) - Algorithm variants
3. Reference `03-mathematical-framework.md` - Mathematical validation

---

## Key Concepts Across Documents

### The Four Algorithm Variants

| Variant | Buybacks | Sell Triggers | Risk Profile | Best For |
|---------|----------|---------------|--------------|----------|
| Buy-and-Hold | ❌ | Never | Lowest | Traditional investors |
| ATH-Only | ❌ | New ATHs only | Low | Conservative profit-taking |
| Standard SD | ✅ | ATHs + brackets | Medium | Balanced growth + income |
| **ATH-Sell** | ✅ | New ATHs only | Medium-High | Maximum compounding |

### Core Mathematical Insights

- **Volatility Alpha Formula**: `α ≥ N × (trigger%)² / 2` (conservative lower bound)
- **Time Machine Effect**: Higher profit sharing → proportionally longer to reach goals
- **Gap Bonus**: Actual alpha exceeds formula by 1.1x-3.4x due to price discontinuities
- **Coverage Ratio**: Synthetic dividends / withdrawals (>1.0 = self-sustaining)

### Economic Principles

- **Dividend Illusion**: All cash withdrawals have opportunity cost
- **Sequence Protection**: Avoid forced sales during early retirement bear markets
- **Capital Efficiency**: Track deployment metrics, not just share counts
- **Path Independence**: ATH-only strategies guarantee total returns regardless of path

---

## Usage as System Prompt

These documents are designed to concatenate for AI assistant context:

**Core Concepts Only**:
```bash
cat 01-core-concepts.md 02-algorithm-variants.md 03-mathematical-framework.md > prompt.md
```

**Complete Foundation**:
```bash
cat 0[1-7]-*.md > full_prompt.md
```

---

## Document Status

**Last Updated**: October 29, 2025
**Consolidation**: Complete rewrite from scratch
- ✅ Eliminated redundancy across 20+ legacy files
- ✅ Incorporated new ATH-Sell algorithm variant
- ✅ Streamlined from ~4,000 lines to ~2,500 lines (37% reduction)
- ✅ Organized around user needs rather than development history
- ✅ Zero duplication: every concept explained once in optimal location

**Philosophy**: Maximum information density with complete conceptual coverage. Each document serves a distinct purpose in the learning journey.

---

## Contributing

When adding new theoretical insights:
1. **Identify the right document** based on the concept hierarchy above
2. **Check for redundancy** - don't duplicate existing explanations
3. **Maintain cross-references** to related concepts
4. **Update this README** with new concepts or structural changes

**Questions?** Start with the Quick Start guide above, then dive deeper based on your interests.</content>
<parameter name="filePath">c:\build\synthetic-dividend\theory\README.md