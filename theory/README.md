# Synthetic Dividend Algorithm - Theoretical Framework

This folder contains the complete conceptual and theoretical foundation for the Synthetic Dividend Algorithm. These documents are designed to be concatenated and used as a comprehensive system prompt for AI assistants or as standalone reference material.

## Document Overview

### Core Theory

1. **[INVESTING_THEORY.md](INVESTING_THEORY.md)** - Foundational investment theory
   - Why traditional dividend strategies fail
   - The "selling at strength" principle
   - ATH-only vs Enhanced (with buybacks) strategies
   - Profit sharing ratios and their economic implications
   - Mathematical proofs of key properties

2. **[VOLATILITY_ALPHA_THESIS.md](VOLATILITY_ALPHA_THESIS.md)** - Central thesis and mathematics
   - Definition of volatility alpha
   - Mathematical formulation
   - Conditions for positive alpha generation
   - Relationship to exponential scaling
   - Theoretical limits and constraints

### Advanced Concepts

3. **[INITIAL_CAPITAL_THEORY.md](INITIAL_CAPITAL_THEORY.md)** - Opportunity cost framework
   - Two separate capital streams: equity position vs trading cash flow
   - What we currently track vs what we don't track
   - Conceptual inconsistency in opportunity cost accounting
   - Three implementation options (with Option A marked as WRONG)
   - Impact on absolute returns vs volatility alpha (alpha unchanged)

4. **[PORTFOLIO_VISION.md](PORTFOLIO_VISION.md)** - Multi-stock portfolio strategy (Phase 2 goal)
   - Vision for portfolio-level implementation
   - Shared 10% cash reserve across multiple stocks
   - Three-stream capital model: tactical cash + stock positions + trading flow
   - Portfolio-level opportunity cost tracking
   - Research questions for future work

### Practical Framework

5. **[RETURN_METRICS_ANALYSIS.md](RETURN_METRICS_ANALYSIS.md)** - Metrics interpretation
   - Primary vs supplementary metrics
   - Capital utilization and deployment tracking
   - "More Shares = Success" fallacy prevention
   - Proper interpretation checklist
   - Variable capital deployment scenarios

6. **[CODING_PHILOSOPHY.md](CODING_PHILOSOPHY.md)** - Development principles
   - Test-Driven Trust: tests validate economic behavior
   - Code as documentation
   - Fail-fast with clear error messages
   - Empirical validation over theory
   - When to break the rules

## Usage as System Prompt

To use these documents as a system prompt for an AI assistant working on the Synthetic Dividend Algorithm:

### Quick Start (Essential Only)
```bash
cat theory/INVESTING_THEORY.md theory/VOLATILITY_ALPHA_THESIS.md > prompt.md
```

### Comprehensive (Full Context)
```bash
cat theory/INVESTING_THEORY.md \
    theory/VOLATILITY_ALPHA_THESIS.md \
    theory/INITIAL_CAPITAL_THEORY.md \
    theory/PORTFOLIO_VISION.md \
    theory/RETURN_METRICS_ANALYSIS.md \
    theory/CODING_PHILOSOPHY.md > full_prompt.md
```

### Recommended Order for Learning
1. Start with `INVESTING_THEORY.md` - Understand the "why"
2. Read `VOLATILITY_ALPHA_THESIS.md` - Grasp the mathematics
3. Review `RETURN_METRICS_ANALYSIS.md` - Learn proper interpretation
4. Study `INITIAL_CAPITAL_THEORY.md` - Understand opportunity cost nuances
5. Explore `PORTFOLIO_VISION.md` - See the long-term vision
6. Reference `CODING_PHILOSOPHY.md` - Internalize development principles

## Key Concepts Across Documents

### The Two Strategies
- **ATH-only**: Sell at all-time highs only, never buy back
- **Enhanced**: Sell at ATH + buy back during dips (generates volatility alpha)

### The Three Questions
- **Question A**: "How much money did I make?" (gross return)
- **Question B**: "Did I beat opportunity cost?" (net return after costs)
- **Question C**: "Should I use this vs buy-and-hold?" (volatility alpha)

**We're asking Question C, but currently reporting like Question A.**

### The Three Capital Streams (Portfolio Vision)
1. **Tactical Cash Reserve** (10%) - Strategic buffer, earns 0%, enables buybacks
2. **Stock Positions** (90%) - Equity holdings with opportunity cost vs baseline
3. **Trading Cash Flow** (variable) - Algorithm's cash generation from transactions

### Critical Distinctions

**Initial Capital vs Trading Cash Flow**
- Initial capital = Equity position (what we invest to buy shares)
- Trading cash flow = Bank balance (algorithm's sells/buys)
- **WRONG**: Starting bank at -$100k (would break bank semantics)
- **RIGHT**: Bank starts at $0, track initial capital opportunity cost separately

**Shares vs Returns**
- ❌ WRONG: "Enhanced has 7,337 shares vs 7,221, so it's better"
- ✅ RIGHT: "Enhanced returned 45.2% vs 42.1%, so it's better"
- Share counts are diagnostic, not success metrics

**Opportunity Cost Components**
- Currently track: Negative bank during trading (when algorithm borrows)
- Missing: Initial capital deployment (the $100k equity position)
- Impact: Volatility alpha UNCHANGED (cancels in subtraction), but absolute returns overstated

## Mathematical Foundations

### Exponential Scaling
```
Next rebalance trigger = Last price × (1 + rebalance_size_pct)
```

Common triggers:
- sd4: 18.92% (4th root of 2)
- sd6: 12.25% (6th root of 2)
- sd8: 9.05% (8th root of 2)
- sd10: 7.18% (10th root of 2)

### Profit Sharing
```
Sell Amount = (Holdings × Rebalance %) × (Profit Sharing % / 100)
```

- 0%: Never sell (pure buy-and-hold)
- 50%: Balanced (sell half of profit, keep half compounding)
- 100%: Aggressive cash flow (sell all profit portion)
- 125%+: Reduce share count (de-risk, harvest gains)

### Volatility Alpha
```
Volatility Alpha = Algorithm Return - Buy-and-Hold Return
```

Positive alpha requires:
1. Volatility (price must oscillate)
2. End at new ATH (thesis requirement)
3. Successful buyback unwinding (sell high, buy low)

## Evolution of Understanding

### Phase 1: Core Algorithm
- Developed ATH-only and Enhanced strategies
- Established exponential scaling principle
- Validated with backtests across 12 assets

### Phase 2: Metrics Refinement
- Added capital utilization tracking
- Recognized "More Shares ≠ Success" fallacy
- Distinguished primary vs supplementary metrics

### Phase 3: Opportunity Cost Analysis (Current)
- Identified missing initial capital opportunity cost
- Clarified two-stream model (equity vs trading)
- Documented three implementation options
- **Critical fix**: Separated equity position from trading cash flow

### Phase 4: Portfolio Vision (Future)
- Multi-stock portfolio with shared cash reserve
- Portfolio-level opportunity cost tracking
- Cross-asset cash flow optimization
- Realistic investment scenario testing

## Common Pitfalls to Avoid

1. **Don't conflate equity position with bank balance**
   - Initial $100k is equity (holdings), not a loan to ourselves
   - Bank tracks trading cash flow, starts at $0

2. **Don't judge strategies by share counts**
   - More shares only matters if returns are better
   - Capital utilization explains deployment, not success

3. **Don't assume opportunity cost affects alpha**
   - Alpha = difference in returns (opportunity cost cancels)
   - But absolute returns are overstated without full accounting

4. **Don't treat tactical cash as idle capital**
   - 10% cash reserve enables buybacks without borrowing
   - Strategic value beyond opportunity cost measurement

5. **Don't cherry-pick test results**
   - Document all experiments, including failures
   - Empirical validation requires honest reporting

## Questions This Framework Answers

✅ Why sell only at all-time highs? (Never realize losses, only gains)
✅ How do buybacks generate alpha? (Buy low, sell high on volatility)
✅ What's the optimal profit-sharing ratio? (50% balances cash + growth)
✅ Why does volatility alpha exist? (Harvesting mean reversion)
✅ How to measure capital efficiency? (Utilization + return on deployed)
✅ What's missing in opportunity cost? (Initial capital not tracked)
✅ How does portfolio-level strategy work? (Shared cash reserve)
✅ Is this better than buy-and-hold? (If volatility alpha > 0)

## Contributing to This Framework

When adding new theoretical insights:

1. **Document the "why" not just the "what"**
   - Explain economic intuition
   - Show mathematical derivation
   - Provide concrete examples

2. **Connect to existing concepts**
   - How does this relate to volatility alpha?
   - Does it change our interpretation of metrics?
   - What are the portfolio-level implications?

3. **Identify trade-offs**
   - Every strategy has costs and benefits
   - Make them explicit
   - Quantify when possible

4. **Update cross-references**
   - Maintain consistency across documents
   - Update this README.md with new concepts
   - Add to appropriate document section

5. **Consider the system prompt use case**
   - Will an AI assistant understand this standalone?
   - Is the notation consistent across documents?
   - Are key terms defined before use?

---

**Last Updated**: October 2025  
**Status**: Active development (Phase 3: Opportunity Cost Analysis)  
**Next**: Complete initial capital opportunity cost implementation
