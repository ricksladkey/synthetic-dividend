"""Trading algorithms for backtesting.

This package contains all trading algorithm implementations, each in its own
focused module for better maintainability and testability.

Available algorithms:
- AlgorithmBase: Abstract base class
- BuyAndHoldAlgorithm: Passive buy-and-hold strategy
- SyntheticDividendAlgorithm: Volatility harvesting strategy
"""

from .base import AlgorithmBase
from .buy_and_hold import BuyAndHoldAlgorithm
from .factory import build_algo_from_name
from .synthetic_dividend import SyntheticDividendAlgorithm

__all__ = [
    "AlgorithmBase",
    "BuyAndHoldAlgorithm",
    "SyntheticDividendAlgorithm",
    "build_algo_from_name",
]
