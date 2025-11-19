"""
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

from __future__ import annotations

import os
from datetime import date
from typing import TYPE_CHECKING, Optional

import pandas as pd

from src.paths import get_cache_dir

# Optional dependency: yfinance is only required for the fallback implementation
try:
    import yfinance as yf  # type: ignore

    YFINANCE_AVAILABLE = True
except Exception:
    yf = None  # type: ignore
    YFINANCE_AVAILABLE = False

if TYPE_CHECKING:
    from src.data.asset_provider import AssetProvider


class Asset:
    """Facade for fetching price and dividend data for a single ticker.

    Constructor will attempt to locate a provider via AssetRegistry. If found,
    operations are delegated to that provider instance. Otherwise the class
    implements a small fallback that uses yfinance and a simple on-disk cache.
    """

    def __init__(self, ticker: str, cache_dir: Optional[str] = None) -> None:
        self.ticker = ticker.upper()
        # Use centralized cache directory from src/paths.py if not specified
        if cache_dir is None:
            self.cache_dir = str(get_cache_dir())
        else:
            self.cache_dir = cache_dir
        os.makedirs(self.cache_dir, exist_ok=True)

        # Default cache file paths
        self.pkl_path = os.path.join(self.cache_dir, f"{self.ticker}.pkl")
        self.csv_path = os.path.join(self.cache_dir, f"{self.ticker}.csv")
        self.div_pkl_path = os.path.join(self.cache_dir, f"{self.ticker}_dividends.pkl")
        self.div_csv_path = os.path.join(self.cache_dir, f"{self.ticker}_dividends.csv")

        # Provider instance (None = use fallback)
        self._provider: Optional["AssetProvider"] = None

        # Attempt to use a registered provider if available. Import locally to
        # avoid import cycles during package import.
        provider_class = None
        try:
            from src.data.asset_provider import AssetRegistry

            provider_class = AssetRegistry.get_provider_class(self.ticker)
        except Exception:
            provider_class = None

        if provider_class is not None:
            # Instantiate provider and mirror common cache attributes
            self._provider = provider_class(self.ticker, self.cache_dir)
            self.pkl_path = getattr(self._provider, "pkl_path", self.pkl_path)
            self.csv_path = getattr(self._provider, "csv_path", self.csv_path)
            self.div_pkl_path = getattr(self._provider, "div_pkl_path", self.div_pkl_path)
            self.div_csv_path = getattr(self._provider, "div_csv_path", self.div_csv_path)
            return

        # No provider: ensure fallback can operate
        if not YFINANCE_AVAILABLE:
            raise RuntimeError("yfinance not available; install with: pip install yfinance")

        self._provider = None

    # Public API
    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        if getattr(self, "_provider", None) is not None:
            assert self._provider is not None

            # Check if we're requesting data that includes today
            from datetime import date as date_class
            today = date_class.today()
            requesting_today = end_date >= today

            # If requesting today, check cache for historical data and fetch fresh for today
            if requesting_today and start_date < today:
                # Get cached historical data (everything before today)
                cached = self._load_price_cache()
                if cached is not None and not cached.empty:
                    cached_dates = pd.to_datetime(cached.index).date
                    # Filter cached data to only include dates before today
                    historical_mask = [d < today for d in cached_dates]
                    historical_data = cached.loc[historical_mask]

                    # Check if cache covers the historical range
                    if not historical_data.empty and min(cached_dates) <= start_date:
                        # Fetch only today's data from provider
                        fresh_result = self._provider.get_prices(today, end_date)

                        if not fresh_result.empty:
                            # Combine historical cache with fresh today data
                            combined = pd.concat([historical_data, fresh_result], axis=0)
                            combined = combined[~combined.index.duplicated(keep="last")]
                            combined = combined.sort_index()

                            # Save the combined data (caches today, will be historical tomorrow)
                            from src.data.static_provider import StaticAssetProvider
                            if not isinstance(self._provider, StaticAssetProvider):
                                self._save_price_cache(combined)

                            # Return only the requested range
                            return self._filter_range(combined, start_date, end_date)

            # Standard path: fetch from provider
            result = self._provider.get_prices(start_date, end_date)
            # If primary provider returns empty data, try fallback providers
            if not result.empty:
                # Cache the result (but not for StaticAssetProvider - it reads committed test data)
                from src.data.static_provider import StaticAssetProvider

                if not isinstance(self._provider, StaticAssetProvider):
                    self._save_price_cache(result)
                return result

            # Try fallback providers in priority order (excluding the primary)
            # Skip fallback for mock assets, cash assets, and static assets in test environments
            from src.data.static_provider import StaticAssetProvider

            if not (
                self.ticker.startswith("MOCK-")
                or self.ticker == "USD"
                or isinstance(self._provider, StaticAssetProvider)
            ):
                try:
                    from src.data.asset_provider import AssetRegistry

                    for pattern, provider_class, priority in AssetRegistry._providers:
                        if provider_class == self._provider.__class__:
                            continue  # Skip the primary provider that failed
                        if AssetRegistry._pattern_matches(pattern, self.ticker):
                            fallback_provider = provider_class(self.ticker, self.cache_dir)
                            fallback_result = fallback_provider.get_prices(start_date, end_date)
                            if not fallback_result.empty:
                                # Cache the result
                                self._save_price_cache(fallback_result)
                                return fallback_result
                except Exception:
                    pass

            # If all providers failed, try to load from cache as last resort (only for Yahoo provider)
            from src.data.yahoo_provider import YahooAssetProvider

            if isinstance(self._provider, YahooAssetProvider):
                cached = self._load_price_cache()
                if self._cache_covers_range(cached, start_date, end_date):
                    return self._filter_range(cached, start_date, end_date)

            # Return empty result if no provider or cache worked
            return result

        cached = self._load_price_cache()
        if self._cache_covers_range(cached, start_date, end_date):
            return self._filter_range(cached, start_date, end_date)

        df = self._download_ohlc(start_date, end_date)
        if not df.empty:
            self._save_price_cache(df)
        return df

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        if getattr(self, "_provider", None) is not None:
            assert self._provider is not None
            result = self._provider.get_dividends(start_date, end_date)
            # If primary provider returns empty data, try fallback providers
            if not result.empty:
                # Cache the result (but not for StaticAssetProvider - it reads committed test data)
                from src.data.static_provider import StaticAssetProvider

                if not isinstance(self._provider, StaticAssetProvider):
                    self._save_dividend_cache(result)
                return result

            # Try fallback providers in priority order (excluding the primary)
            # Skip fallback for mock assets, cash assets, and static assets in test environments
            from src.data.static_provider import StaticAssetProvider

            if not (
                self.ticker.startswith("MOCK-")
                or self.ticker == "USD"
                or isinstance(self._provider, StaticAssetProvider)
            ):
                try:
                    from src.data.asset_provider import AssetRegistry

                    for pattern, provider_class, priority in AssetRegistry._providers:
                        if provider_class == self._provider.__class__:
                            continue  # Skip the primary provider that failed
                        if AssetRegistry._pattern_matches(pattern, self.ticker):
                            fallback_provider = provider_class(self.ticker, self.cache_dir)
                            fallback_result = fallback_provider.get_dividends(start_date, end_date)
                            if not fallback_result.empty:
                                # Cache the result
                                self._save_dividend_cache(fallback_result)
                                return fallback_result
                except Exception:
                    pass

            # If all providers failed, try to load from cache as last resort (only for Yahoo provider)
            from src.data.yahoo_provider import YahooAssetProvider

            if isinstance(self._provider, YahooAssetProvider):
                cached = self._load_dividend_cache()
                if cached is not None and not cached.empty:
                    return self._filter_dividends(cached, start_date, end_date)

            # Return empty result if no provider or cache worked
            return result

        cached = self._load_dividend_cache()
        if cached is not None and not cached.empty:
            return self._filter_dividends(cached, start_date, end_date)

        series = self._download_dividends()
        if not series.empty:
            self._save_dividend_cache(series)
        return self._filter_dividends(series, start_date, end_date)

    def clear_cache(self) -> None:
        if getattr(self, "_provider", None) is not None:
            assert self._provider is not None
            try:
                self._provider.clear_cache()
                return
            except Exception:
                # Ignore provider clear_cache errors: fallback to manual cache deletion
                pass

        for path in (self.pkl_path, self.csv_path, self.div_pkl_path, self.div_csv_path):
            if path is not None:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except Exception:
                    # Ignore file deletion errors: cache clearing is best-effort
                    pass

    @property
    def supports_fractional_shares(self) -> bool:
        """
        Whether this asset supports fractional shares.

        Returns:
            True for crypto and mutual funds
            False for traditional stocks and ETFs
        """
        if getattr(self, "_provider", None) is not None:
            assert self._provider is not None
            return self._provider.supports_fractional_shares

        # Fallback implementation for when no provider is available
        ticker = self.ticker.upper()
        # Crypto tickers (BTC-USD, ETH-USD, etc.)
        if "-" in ticker and any(
            crypto in ticker for crypto in ["BTC", "ETH", "ADA", "SOL", "DOT"]
        ):
            return True
        # Mutual funds (typically start with VF, VG, etc.)
        if any(ticker.startswith(prefix) for prefix in ["VF", "VG"]):
            return True
        # Default to False for traditional stocks and ETFs
        return False

    # --- Internal helpers for the fallback implementation ---
    def _load_price_cache(self) -> Optional[pd.DataFrame]:
        if self.pkl_path is not None and os.path.exists(self.pkl_path):
            try:
                return pd.read_pickle(self.pkl_path)
            except Exception:
                return None
        return None

    def _save_price_cache(self, df: pd.DataFrame) -> None:
        try:
            # Load existing cache if it exists
            existing_df = self._load_price_cache()

            if existing_df is not None and not existing_df.empty:
                # Normalize indices to ensure compatibility
                # Convert both to datetime for consistent comparison
                existing_dates = pd.to_datetime(existing_df.index)
                new_dates = pd.to_datetime(df.index)

                # Reset indices to datetime objects for consistent merging
                existing_df = existing_df.copy()
                existing_df.index = existing_dates
                df = df.copy()
                df.index = new_dates

                # Combine existing cache with new data (union operation)
                combined_df = pd.concat([existing_df, df], axis=0)
                # Remove duplicates based on index (date), keeping the last occurrence
                combined_df = combined_df[~combined_df.index.duplicated(keep="last")]
                # Sort by index to maintain chronological order
                combined_df = combined_df.sort_index()
                df = combined_df

            # Save the (possibly extended) cache
            if self.pkl_path is not None:
                df.to_pickle(self.pkl_path)
            if self.csv_path is not None:
                # Ensure the index has a proper name for CSV header
                df_copy = df.copy()
                df_copy.index.name = "Date"
                df_copy.to_csv(self.csv_path, index=True)
        except Exception:
            # Ignore cache write errors: cache is non-critical and failures should not interrupt main flow
            pass

    def _load_dividend_cache(self) -> Optional[pd.Series]:
        if self.div_pkl_path is not None and os.path.exists(self.div_pkl_path):
            try:
                return pd.read_pickle(self.div_pkl_path)
            except Exception:
                return None
        return None

    def _save_dividend_cache(self, series: pd.Series) -> None:
        try:
            # Load existing cache if it exists
            existing_series = self._load_dividend_cache()

            if existing_series is not None and not existing_series.empty:
                # Normalize indices to ensure compatibility
                # Convert both to datetime for consistent comparison
                existing_dates = pd.to_datetime(existing_series.index)
                new_dates = pd.to_datetime(series.index)

                # Reset indices to datetime objects for consistent merging
                existing_series = existing_series.copy()
                existing_series.index = existing_dates
                series = series.copy()
                series.index = new_dates

                # Combine existing cache with new data (union operation)
                combined_series = pd.concat([existing_series, series], axis=0)
                # Remove duplicates based on index (date), keeping the last occurrence
                combined_series = combined_series[~combined_series.index.duplicated(keep="last")]
                # Sort by index to maintain chronological order
                combined_series = combined_series.sort_index()
                series = combined_series

            # Save the (possibly extended) cache
            if self.div_pkl_path is not None:
                series.to_pickle(self.div_pkl_path)
            if self.div_csv_path is not None:
                series.to_frame(name="Dividends").to_csv(self.div_csv_path)
        except Exception:
            # Ignore cache write errors: cache is non-critical and failures should not interrupt main flow
            pass

    def _cache_covers_range(self, cached: Optional[pd.DataFrame], start: date, end: date) -> bool:
        if cached is None or cached.empty:
            return False
        try:
            dates = pd.to_datetime(cached.index).date
            return bool(min(dates) <= start and max(dates) >= end)
        except Exception:
            return False

    def _filter_range(self, cached: pd.DataFrame, start: date, end: date) -> pd.DataFrame:
        try:
            idx = pd.to_datetime(cached.index).date
            mask = [(d >= start and d <= end) for d in idx]
            return cached.loc[mask]
        except Exception:
            return cached

    def _filter_dividends(self, series: pd.Series, start: date, end: date) -> pd.Series:
        try:
            idx = pd.to_datetime(series.index).date
            mask = [(d >= start and d <= end) for d in idx]
            return series.loc[mask]
        except Exception:
            return series

    def _download_ohlc(self, start: date, end: date) -> pd.DataFrame:
        # Minimal wrapper around yfinance. Tests using Mock providers should not
        # hit this code path.
        if not YFINANCE_AVAILABLE:
            return pd.DataFrame()

        try:
            ticker = yf.Ticker(self.ticker)
            # yfinance requires end date to be exclusive, so add one day
            end_date = pd.Timestamp(end) + pd.Timedelta(days=1)
            df = ticker.history(start=start.isoformat(), end=end_date.isoformat())
            # Ensure index is a DatetimeIndex and return expected columns
            return df
        except Exception:
            return pd.DataFrame()

    def _download_dividends(self) -> pd.Series:
        if not YFINANCE_AVAILABLE:
            return pd.Series(dtype=float)
        try:
            ticker = yf.Ticker(self.ticker)
            s = ticker.dividends
            if isinstance(s, pd.Series):
                return s
            return pd.Series(dtype=float)
        except Exception:
            return pd.Series(dtype=float)


# Optional: register default providers where available (best-effort)
try:
    from src.data.asset_provider import AssetRegistry
    from src.data.cash_provider import CashAssetProvider
    from src.data.mock_provider import MockAssetProvider
    from src.data.yahoo_provider import YahooAssetProvider

    try:
        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)
        AssetRegistry.register("MOCK-*", MockAssetProvider, priority=0)
    except Exception:
        # best-effort: ignore registration failures
        pass
except Exception:
    # provider modules not available  fallback behavior will be used
    pass
