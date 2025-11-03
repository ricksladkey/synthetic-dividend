"""Algorithm factory: parse string identifiers into algorithm instances."""

import re

from src.algorithms.base import AlgorithmBase
from src.algorithms.buy_and_hold import BuyAndHoldAlgorithm
from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm


def build_algo_from_name(name: str) -> AlgorithmBase:
    """Factory: parse string identifier into algorithm instance.

    Supported formats (priority order):
        'sdN' → N-th root of 2 (exponential scaling), 50% profit sharing default
        'sdN,P' → N-th root of 2, P% profit sharing
        'buy-and-hold' → BuyAndHoldAlgorithm()
        'sd-9.15,50' → SyntheticDividendAlgorithm(0.0915, 0.5, buyback_enabled=True)
        'sd-9.15,50,100' → SyntheticDividendAlgorithm(0.0915, 0.5, bracket_seed=100.0)
        'sd-ath-only-9.15,50' → SyntheticDividendAlgorithm(0.0915, 0.5, buyback_enabled=False)
        'sd-ath-sell-9.15,50' → SyntheticDividendAlgorithm(0.0915, 0.5, sell_at_new_ath=True)

    Note: String format uses percentages (9.15, 50) for readability, but converts
    to decimals (0.0915, 0.5) internally for mathematical clarity.

    Examples (exponential scaling - Nth root of 2):
        'sd8' → 2^(1/8) - 1 = 9.05% rebalance trigger, 50% profit sharing
        'sd8,75' → 2^(1/8) - 1 = 9.05% rebalance trigger, 75% profit sharing
        'sd12' → 2^(1/12) - 1 = 5.95% rebalance trigger, 50% profit sharing
        'sd16' → 2^(1/16) - 1 = 4.43% rebalance trigger, 50% profit sharing

    Examples (bracket seed alignment):
        'sd-9.15,50,1' → Align all brackets to powers of 2 (unity normalization)
        'sd-9.15,50,100' → Align brackets to multiples of 100 (e.g., 100, 109.15, 118.58...)
        'sd-9.15,50,0' → No normalization (default behavior)

    Rationale: N equal geometric steps to doubling ensures uniform proportional gains
    between rebalances, adapting naturally to asset volatility.

    Legacy formats (backward compatibility):
        'sd/9.15%/50%' → same as 'sd-9.15,50'
        'sd-ath-only/9.15%/50%' → same as 'sd-ath-only-9.15,50'
        'synthetic-dividend/...' → same as 'sd-...'
    """
    name = name.strip()
    print(f"Building algorithm from name: {name}")

    # Buy-and-hold baseline
    if name == "buy-and-hold":
        return BuyAndHoldAlgorithm()

    # Exponential scaling: sdN or sdN,P or sdN,P,S
    # N = Nth root of 2 (N equal geometric steps to doubling)
    # P = profit sharing % (optional, defaults to 50)
    # S = bracket seed (optional, defaults to None)
    m = re.match(r"^sd(\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?))?(?:,(\d+(?:\.\d+)?))?$", name)
    if m:
        n = float(m.group(1))
        profit_pct = float(m.group(2)) if m.group(2) else 50.0
        bracket_seed = float(m.group(3)) if m.group(3) else None
        # Calculate rebalance trigger: Nth root of 2, minus 1 (as decimal)
        rebalance = pow(2.0, 1.0 / n) - 1.0
        print(f"  Exponential scaling: 2^(1/{n}) - 1 = {rebalance*100:.4f}% trigger")
        if bracket_seed is not None:
            print(f"  Bracket seed: {bracket_seed}")
        return SyntheticDividendAlgorithm(
            rebalance_size=rebalance,
            profit_sharing=profit_pct / 100.0,
            buyback_enabled=True,
            bracket_seed=bracket_seed,
        )

    # ATH-sell variant: buys on dips, sells only at new ATHs
    m = re.match(
        r"^(sd|synthetic-dividend)-ath-sell-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?))?$",
        name,
    )
    if m:
        rebalance_pct = float(m.group(2))
        profit_pct = float(m.group(3))
        bracket_seed = float(m.group(4)) if m.group(4) else None
        return SyntheticDividendAlgorithm(
            rebalance_size=rebalance_pct / 100.0,
            profit_sharing=profit_pct / 100.0,
            buyback_enabled=True,
            sell_at_new_ath=True,
            bracket_seed=bracket_seed,
        )

    # ATH-only variant: modern comma-based format
    m = re.match(
        r"^(sd|synthetic-dividend)-ath-only-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?))?$",
        name,
    )
    if m:
        rebalance_pct = float(m.group(2))
        profit_pct = float(m.group(3))
        bracket_seed = float(m.group(4)) if m.group(4) else None
        return SyntheticDividendAlgorithm(
            rebalance_size=rebalance_pct / 100.0,
            profit_sharing=profit_pct / 100.0,
            buyback_enabled=False,
            bracket_seed=bracket_seed,
        )

    # Full algorithm: modern comma-based format
    m = re.match(
        r"^(sd|synthetic-dividend)-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?))?$", name
    )
    if m:
        rebalance_pct = float(m.group(2))
        profit_pct = float(m.group(3))
        bracket_seed = float(m.group(4)) if m.group(4) else None
        return SyntheticDividendAlgorithm(
            rebalance_size=rebalance_pct / 100.0,
            profit_sharing=profit_pct / 100.0,
            buyback_enabled=True,
            bracket_seed=bracket_seed,
        )

    # Legacy: ATH-only variant with slash/percent format
    m = re.match(
        r"^(sd|synthetic-dividend)-ath-only/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%(?:/(\d+(?:\.\d+)?))?$",
        name,
    )
    if m:
        rebalance_pct = float(m.group(2))
        profit_pct = float(m.group(3))
        bracket_seed = float(m.group(4)) if m.group(4) else None
        return SyntheticDividendAlgorithm(
            rebalance_size=rebalance_pct / 100.0,
            profit_sharing=profit_pct / 100.0,
            buyback_enabled=False,
            bracket_seed=bracket_seed,
        )

    # Legacy: Full algorithm with slash/percent format
    m = re.match(
        r"^(sd|synthetic-dividend)/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%(?:/(\d+(?:\.\d+)?))?$", name
    )
    if m:
        rebalance_pct = float(m.group(2))
        profit_pct = float(m.group(3))
        bracket_seed = float(m.group(4)) if m.group(4) else None
        return SyntheticDividendAlgorithm(
            rebalance_size=rebalance_pct / 100.0,
            profit_sharing=profit_pct / 100.0,
            buyback_enabled=True,
            bracket_seed=bracket_seed,
        )

    raise ValueError(f"Unrecognized strategy name: {name}")
