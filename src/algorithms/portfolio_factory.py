"""Portfolio algorithm factory: parse string identifiers into portfolio algorithm instances."""

import re
from typing import Dict, List

from src.algorithms.base import AlgorithmBase
from src.algorithms.buy_and_hold import BuyAndHoldAlgorithm
from src.algorithms.factory import build_algo_from_name
from src.algorithms.per_asset_portfolio import PerAssetPortfolioAlgorithm
from src.algorithms.portfolio_base import PortfolioAlgorithmBase
from src.algorithms.quarterly_rebalance import QuarterlyRebalanceAlgorithm
from src.algorithms.synthetic_dividend import SyntheticDividendAlgorithm


def build_portfolio_algo_from_name(
    name: str, allocations: Dict[str, float]
) -> PortfolioAlgorithmBase:
    """Factory: parse string identifier into portfolio algorithm instance.

    Supported formats:
        Portfolio-level algorithms:
            'quarterly-rebalance' → Rebalance to target allocations quarterly (Mar/Jun/Sep/Dec)
            'quarterly-rebalance:3,6,9,12' → Custom rebalance months
            'monthly-rebalance' → Rebalance every month
            'annual-rebalance' → Rebalance once per year (December)

        Per-asset algorithms (applied to all assets with shared bank):
            'per-asset:sd8' → Apply sd8 to all assets
            'per-asset:sd8,75' → Apply sd8 with 75% profit sharing to all
            'per-asset:buy-and-hold' → All assets buy-and-hold

        Auto-selection (analyzes each asset):
            'auto' → Choose optimal per-asset strategy based on historical volatility

    Args:
        name: Algorithm identifier string
        allocations: Dict of ticker → target allocation (used for rebalancing targets)

    Returns:
        PortfolioAlgorithmBase instance

    Examples:
        >>> build_portfolio_algo_from_name('quarterly-rebalance', {'VOO': 0.6, 'BIL': 0.4})
        QuarterlyRebalanceAlgorithm({'VOO': 0.6, 'BIL': 0.4}, [3,6,9,12])

        >>> build_portfolio_algo_from_name('per-asset:sd8', {'NVDA': 0.5, 'VOO': 0.5})
        PerAssetPortfolioAlgorithm({'NVDA': SyntheticDividendAlgorithm(...), 'VOO': ...})

        >>> build_portfolio_algo_from_name('auto', {'NVDA': 0.3, 'BTC-USD': 0.2, 'VOO': 0.5})
        PerAssetPortfolioAlgorithm({'NVDA': sd8, 'BTC-USD': sd4, 'VOO': sd10})
    """
    name = name.strip()
    print(f"Building portfolio algorithm from name: {name}")

    # Quarterly rebalancing (default months)
    if name == "quarterly-rebalance":
        print("  -> QuarterlyRebalanceAlgorithm (default: Mar/Jun/Sep/Dec)")
        return QuarterlyRebalanceAlgorithm(
            target_allocations=allocations, rebalance_months=[3, 6, 9, 12]
        )

    # Quarterly rebalancing (custom months)
    m = re.match(r"^quarterly-rebalance:(\d+(?:,\d+)*)$", name)
    if m:
        months_str = m.group(1)
        months = [int(x) for x in months_str.split(",")]
        print(f"  -> QuarterlyRebalanceAlgorithm (months: {months})")
        return QuarterlyRebalanceAlgorithm(target_allocations=allocations, rebalance_months=months)

    # Monthly rebalancing
    if name == "monthly-rebalance":
        print("  -> QuarterlyRebalanceAlgorithm (monthly: all 12 months)")
        return QuarterlyRebalanceAlgorithm(
            target_allocations=allocations, rebalance_months=list(range(1, 13))
        )

    # Annual rebalancing
    if name == "annual-rebalance":
        print("  -> QuarterlyRebalanceAlgorithm (annual: December only)")
        return QuarterlyRebalanceAlgorithm(target_allocations=allocations, rebalance_months=[12])

    # Per-asset: apply same strategy to all assets
    m = re.match(r"^per-asset:(.+)$", name)
    if m:
        per_asset_algo_name = m.group(1)
        print(f"  -> PerAssetPortfolioAlgorithm applying '{per_asset_algo_name}' to all assets")

        # Build the per-asset algorithm once
        per_asset_algo = build_algo_from_name(per_asset_algo_name)

        # Apply to all tickers
        strategies: Dict[str, AlgorithmBase] = {}
        for ticker in allocations.keys():
            # Create separate instance for each ticker
            strategies[ticker] = build_algo_from_name(per_asset_algo_name)

        return PerAssetPortfolioAlgorithm(strategies)

    # Auto: analyze each asset and choose optimal strategy
    if name == "auto":
        print("  -> Auto-selecting strategies per asset based on historical volatility")
        strategies = _build_auto_strategies(allocations)
        return PerAssetPortfolioAlgorithm(strategies)

    raise ValueError(
        f"Unrecognized portfolio algorithm: {name}\n"
        f"Supported: quarterly-rebalance, monthly-rebalance, annual-rebalance, "
        f"per-asset:<algo>, auto"
    )


def _build_auto_strategies(allocations: Dict[str, float]) -> Dict[str, AlgorithmBase]:
    """Auto-select optimal per-asset strategy for each ticker.

    Strategy selection based on asset characteristics:
    - Crypto (BTC, ETH, etc.): sd4 (18.92% trigger) - high volatility
    - High-growth tech (NVDA, PLTR, MSTR): sd6-sd8 (9-12% trigger)
    - Indices (VOO, SPY, QQQ): sd8-sd10 (7-9% trigger)
    - Bonds/cash (BIL, SHY, AGG): buy-and-hold (no rebalancing)

    This is a heuristic-based approach. Future enhancement: calculate historical
    volatility and select trigger dynamically.

    Args:
        allocations: Dict of ticker → allocation percentage

    Returns:
        Dict of ticker → AlgorithmBase instance
    """
    strategies: Dict[str, AlgorithmBase] = {}

    # Asset classification heuristics
    CRYPTO_TICKERS = {"BTC-USD", "ETH-USD", "BTC", "ETH"}
    HIGH_GROWTH_TICKERS = {"NVDA", "PLTR", "MSTR", "TSLA", "COIN"}
    BOND_TICKERS = {"BIL", "SHY", "AGG", "TLT", "BND", "SGOV"}
    INDEX_TICKERS = {"VOO", "SPY", "QQQ", "VTI", "IWM", "DIA"}

    for ticker in allocations.keys():
        if ticker in CRYPTO_TICKERS:
            # Very high volatility → wide brackets
            print(f"    {ticker}: sd4 (crypto - high volatility)")
            strategies[ticker] = SyntheticDividendAlgorithm(
                rebalance_size=0.1892, profit_sharing=0.5  # sd4 = 18.92%
            )
        elif ticker in HIGH_GROWTH_TICKERS:
            # High volatility growth stocks → medium brackets
            print(f"    {ticker}: sd6 (high-growth tech)")
            strategies[ticker] = SyntheticDividendAlgorithm(
                rebalance_size=0.1225, profit_sharing=0.5  # sd6 = 12.25%
            )
        elif ticker in BOND_TICKERS:
            # Low volatility bonds → no rebalancing
            print(f"    {ticker}: buy-and-hold (bond/cash)")
            strategies[ticker] = BuyAndHoldAlgorithm()
        elif ticker in INDEX_TICKERS:
            # Medium volatility indices → standard brackets
            print(f"    {ticker}: sd8 (index - standard)")
            strategies[ticker] = SyntheticDividendAlgorithm(
                rebalance_size=0.0905, profit_sharing=0.5  # sd8 = 9.05%
            )
        else:
            # Unknown ticker → conservative default
            print(f"    {ticker}: sd10 (unknown - conservative)")
            strategies[ticker] = SyntheticDividendAlgorithm(
                rebalance_size=0.0718, profit_sharing=0.5  # sd10 = 7.18%
            )

    return strategies
