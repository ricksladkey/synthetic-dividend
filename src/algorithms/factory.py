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
        'sd-9.15,50' → SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=True)
        'sd-ath-only-9.15,50' → SyntheticDividendAlgorithm(9.15, 50, buyback_enabled=False)

    Examples (exponential scaling - Nth root of 2):
        'sd8' → 2^(1/8) - 1 = 9.05% rebalance trigger, 50% profit sharing
        'sd8,75' → 2^(1/8) - 1 = 9.05% rebalance trigger, 75% profit sharing
        'sd12' → 2^(1/12) - 1 = 5.95% rebalance trigger, 50% profit sharing
        'sd16' → 2^(1/16) - 1 = 4.43% rebalance trigger, 50% profit sharing

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

    # Exponential scaling: sdN or sdN,P
    # N = Nth root of 2 (N equal geometric steps to doubling)
    # P = profit sharing % (optional, defaults to 50)
    m = re.match(r"^sd(\d+(?:\.\d+)?)(?:,(\d+(?:\.\d+)?))?$", name)
    if m:
        n = float(m.group(1))
        profit = float(m.group(2)) if m.group(2) else 50.0
        # Calculate rebalance trigger: Nth root of 2, minus 1, as percentage
        rebalance = (pow(2.0, 1.0 / n) - 1.0) * 100.0
        print(f"  Exponential scaling: 2^(1/{n}) - 1 = {rebalance:.4f}% trigger")
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=True
        )

    # ATH-only variant: modern comma-based format
    m = re.match(r"^(sd|synthetic-dividend)-ath-only-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=False
        )

    # Full algorithm: modern comma-based format
    m = re.match(r"^(sd|synthetic-dividend)-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=True
        )

    # Legacy: ATH-only variant with slash/percent format
    m = re.match(r"^(sd|synthetic-dividend)-ath-only/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=False
        )

    # Legacy: Full algorithm with slash/percent format
    m = re.match(r"^(sd|synthetic-dividend)/(\d+(?:\.\d+)?)%/(\d+(?:\.\d+)?)%$", name)
    if m:
        rebalance = float(m.group(2))
        profit = float(m.group(3))
        return SyntheticDividendAlgorithm(
            rebalance_size_pct=rebalance, profit_sharing_pct=profit, buyback_enabled=True
        )

    raise ValueError(f"Unrecognized strategy name: {name}")
