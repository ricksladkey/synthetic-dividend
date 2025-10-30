"""Trading algorithms for backtesting.

This package contains all trading algorithm implementations, each in its own
focused module for better maintainability and testability.

Available per-asset algorithms:
- AlgorithmBase: Abstract base class for per-asset algorithms
- BuyAndHoldAlgorithm: Passive buy-and-hold strategy
- SyntheticDividendAlgorithm: Volatility harvesting strategy

Available portfolio algorithms:
- PortfolioAlgorithmBase: Abstract base class for portfolio-level algorithms
- PerAssetPortfolioAlgorithm: Adapter for running per-asset algorithms in portfolio
- QuarterlyRebalanceAlgorithm: Traditional quarterly rebalancing
"""

from .base import AlgorithmBase
from .buy_and_hold import BuyAndHoldAlgorithm
from .factory import build_algo_from_name
from .per_asset_portfolio import PerAssetPortfolioAlgorithm
from .portfolio_base import PortfolioAlgorithmBase
from .quarterly_rebalance import QuarterlyRebalanceAlgorithm
from .synthetic_dividend import SyntheticDividendAlgorithm

__all__ = [
    "AlgorithmBase",
    "BuyAndHoldAlgorithm",
    "SyntheticDividendAlgorithm",
    "PortfolioAlgorithmBase",
    "PerAssetPortfolioAlgorithm",
    "QuarterlyRebalanceAlgorithm",
    "build_algo_from_name",
]
