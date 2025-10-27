"""Asset provider interface and registry for multi-source data.

Enables Asset class to fetch data from multiple sources:
- CashAssetProvider: Flat $1.00 prices for USD
- YahooAssetProvider: Market data from Yahoo Finance
- Future: Crypto providers, custom instruments, mock data, etc.

Registry pattern allows priority-based provider selection.
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import Dict, Type, Optional, List, Tuple
import pandas as pd


class AssetProvider(ABC):
    """Abstract base class for asset data providers.
    
    All providers must implement get_prices() and get_dividends()
    with consistent return types. This enables Asset class to work
    with any data source transparently.
    """
    
    def __init__(self, ticker: str, cache_dir: str = "cache"):
        """Initialize provider for given ticker.
        
        Args:
            ticker: Asset symbol (e.g., "USD", "NVDA", "BTC-USD")
            cache_dir: Directory for caching (may not be used by all providers)
        """
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
    
    @abstractmethod
    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get OHLC price data for date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            DataFrame with columns: Open, High, Low, Close
            Index: dates
            Empty DataFrame if no data available
        """
        pass
    
    @abstractmethod
    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        """Get dividend/interest history for date range.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Series with dividend amounts indexed by ex-dividend date
            Empty Series if no dividends
        """
        pass
    
    def clear_cache(self) -> None:
        """Clear any cached data for this asset.
        
        Optional: providers that don't cache can leave this as no-op.
        """
        pass


class AssetRegistry:
    """Registry for asset data providers with priority-based lookup.
    
    Maps ticker patterns to provider classes. Supports:
    - Exact matches: "USD" -> CashAssetProvider
    - Wildcard fallback: "*" -> YahooAssetProvider
    - Priority ordering: higher priority checked first
    
    Example:
        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)
        
        provider = AssetRegistry.get_provider("USD")  # -> CashAssetProvider
        provider = AssetRegistry.get_provider("NVDA") # -> YahooAssetProvider
    """
    
    # Class-level storage: List of (pattern, provider_class, priority)
    _providers: List[Tuple[str, Type[AssetProvider], int]] = []
    
    @classmethod
    def register(
        cls,
        pattern: str,
        provider_class: Type[AssetProvider],
        priority: int = 5
    ) -> None:
        """Register a provider for ticker pattern.
        
        Args:
            pattern: Ticker pattern ("USD", "BTC-*", "*" for wildcard)
            provider_class: Provider class to instantiate
            priority: Lower number = higher priority (checked first)
        """
        # Remove existing registration for same pattern
        cls._providers = [
            (p, pc, pr) for p, pc, pr in cls._providers if p != pattern
        ]
        
        # Add new registration
        cls._providers.append((pattern, provider_class, priority))
        
        # Sort by priority (lower number = higher priority)
        cls._providers.sort(key=lambda x: x[2])
    
    @classmethod
    def get_provider_class(cls, ticker: str) -> Type[AssetProvider]:
        """Get provider class for given ticker.
        
        Checks patterns in priority order. Returns first match.
        
        Args:
            ticker: Ticker symbol (e.g., "USD", "NVDA")
            
        Returns:
            Provider class to instantiate
            
        Raises:
            ValueError: If no provider registered for ticker
        """
        ticker = ticker.upper()
        
        for pattern, provider_class, _ in cls._providers:
            if cls._pattern_matches(pattern, ticker):
                return provider_class
        
        raise ValueError(
            f"No asset provider registered for ticker: {ticker}. "
            f"Register a wildcard provider with AssetRegistry.register('*', ProviderClass)"
        )
    
    @staticmethod
    def _pattern_matches(pattern: str, ticker: str) -> bool:
        """Check if ticker matches pattern.
        
        Supports:
        - Exact match: "USD" matches "USD"
        - Wildcard: "*" matches anything
        - Prefix wildcard: "BTC-*" matches "BTC-USD", "BTC-EUR", etc.
        """
        if pattern == "*":
            return True
        
        if pattern == ticker:
            return True
        
        # Simple prefix wildcard (e.g., "BTC-*")
        if pattern.endswith("*"):
            prefix = pattern[:-1]
            return ticker.startswith(prefix)
        
        return False
    
    @classmethod
    def clear(cls) -> None:
        """Clear all registered providers (mainly for testing)."""
        cls._providers = []
