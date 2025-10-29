"""Asset data provider with multi-source support via registry pattern.

This module provides a factory, `Asset`, that delegates to registered providers
based on the asset's ticker. This allows for a consistent interface regardless
of the data source.

Usage:
    >>> from src.data.asset import Asset
    >>>
    >>> # Asset factory delegates to the appropriate provider
    >>> usd = Asset("USD")  # Uses CashAssetProvider
    >>> nvda = Asset("NVDA") # Uses YahooAssetProvider

Default Providers:
- "USD": CashAssetProvider (provides a constant $1.00 price)
- "*": YahooAssetProvider (wildcard for any other ticker, uses yfinance)
"""

from datetime import date
import pandas as pd

from src.data.asset_provider import AssetProvider, AssetRegistry
from src.data.cash_provider import CashAssetProvider
from src.data.yahoo_provider import YahooAssetProvider


# Register default providers
AssetRegistry.register("USD", CashAssetProvider, priority=1)
AssetRegistry.register("*", YahooAssetProvider, priority=9)  # Wildcard fallback


class Asset:
    """Asset data factory using registry pattern.
    
    Transparently delegates to appropriate provider based on ticker:
    - Asset("USD") → CashAssetProvider (flat $1.00)
    - Asset("NVDA") → YahooAssetProvider (Yahoo Finance)
    
    Maintains same public API regardless of underlying provider.
    
    Example:
        >>> usd = Asset("USD")
        >>> usd_prices = usd.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        >>> usd_prices["Close"].unique()
        array([1.0])
        
        >>> nvda = Asset("NVDA")
        >>> nvda_prices = nvda.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        >>> # Fetched from Yahoo Finance, cached locally
    """

    def __init__(self, ticker: str, cache_dir: str = "cache") -> None:
        """Initialize asset using appropriate provider from registry.
        
        Args:
            ticker: Asset symbol (e.g., "USD", "NVDA", "BTC-USD")
            cache_dir: Directory for cache files (used by providers that cache)
            
        Raises:
            ValueError: If no provider registered for ticker
        """
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
        
        # Get provider class from registry
        provider_class = AssetRegistry.get_provider_class(self.ticker)
        
        # Instantiate provider
        self._provider: AssetProvider = provider_class(self.ticker, cache_dir)

    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get OHLC price data for date range.
        
        Delegates to underlying provider (Yahoo, Cash, etc.).
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            DataFrame with OHLC columns, date-indexed
            
        Raises:
            ValueError: If start_date > end_date
        """
        return self._provider.get_prices(start_date, end_date)

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        """Get dividend/interest history for date range.
        
        Delegates to underlying provider.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            Series with dividend amounts indexed by ex-dividend date
            
        Raises:
            ValueError: If start_date > end_date
        """
        return self._provider.get_dividends(start_date, end_date)

    def clear_cache(self) -> None:
        """Clear any cached data for this asset.
        
        Delegates to underlying provider (no-op for providers that don't cache).
        """
        self._provider.clear_cache()
