
"""Minimal Asset facade used by tests.

This module provides a small, well-scoped `Asset` class that:
- Prefers registered providers from `src.data.asset_provider.AssetRegistry`.
- Falls back to a tiny yfinance-backed downloader that caches to disk if no
  provider is available.

The file is intentionally minimal to make it safe for focused cherry-picks.
"""

from __future__ import annotations

import os
from datetime import date
from typing import Optional

import pandas as pd

# Optional dependency: yfinance is only required for the fallback implementation
try:
    import yfinance as yf  # type: ignore

    YFINANCE_AVAILABLE = True
except Exception:
    yf = None  # type: ignore
    YFINANCE_AVAILABLE = False


class Asset:
    """Facade for fetching price and dividend data for a single ticker.

    Constructor will attempt to locate a provider via AssetRegistry. If found,
    operations are delegated to that provider instance. Otherwise the class
    implements a small fallback that uses yfinance and a simple on-disk cache.
    """

    def __init__(self, ticker: str, cache_dir: str = "cache") -> None:
        self.ticker = ticker.upper()
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

        # Default cache file paths
        self.pkl_path = os.path.join(cache_dir, f"{self.ticker}.pkl")
        self.csv_path = os.path.join(cache_dir, f"{self.ticker}.csv")
        self.div_pkl_path = os.path.join(cache_dir, f"{self.ticker}_dividends.pkl")
        self.div_csv_path = os.path.join(cache_dir, f"{self.ticker}_dividends.csv")

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
            self._provider = provider_class(self.ticker, cache_dir)
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
        if getattr(self, "_provider", None) is not None:
            return self._provider.get_prices(start_date, end_date)

        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        cached = self._load_price_cache()
        if self._cache_covers_range(cached, start_date, end_date):
            return self._filter_range(cached, start_date, end_date)

        df = self._download_ohlc(start_date, end_date)
        if not df.empty:
            self._save_price_cache(df)
        return df

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        if getattr(self, "_provider", None) is not None:
            return self._provider.get_dividends(start_date, end_date)

        if start_date > end_date:
            raise ValueError("start_date must be <= end_date")

        cached = self._load_dividend_cache()
        if cached is not None and not cached.empty:
            return self._filter_dividends(cached, start_date, end_date)

        series = self._download_dividends()
        if not series.empty:
            self._save_dividend_cache(series)
        return self._filter_dividends(series, start_date, end_date)

    def clear_cache(self) -> None:
        if getattr(self, "_provider", None) is not None:
            try:
                self._provider.clear_cache()
                return
            except Exception:
                # Ignore provider clear_cache errors: fallback to manual cache deletion
                pass

        for path in (self.pkl_path, self.csv_path, self.div_pkl_path, self.div_csv_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception:
                # Ignore file deletion errors: cache clearing is best-effort
                pass

    # --- Internal helpers for the fallback implementation ---
    def _load_price_cache(self) -> Optional[pd.DataFrame]:
        if os.path.exists(self.pkl_path):
            try:
                return pd.read_pickle(self.pkl_path)
            except Exception:
                return None
        return None

    def _save_price_cache(self, df: pd.DataFrame) -> None:
        try:
            df.to_pickle(self.pkl_path)
            df.to_csv(self.csv_path, index=True)
        except Exception:
            # Ignore cache write errors: cache is non-critical and failures should not interrupt main flow
            pass

    def _load_dividend_cache(self) -> Optional[pd.Series]:
        if os.path.exists(self.div_pkl_path):
            try:
                return pd.read_pickle(self.div_pkl_path)
            except Exception:
                return None
        return None

    def _save_dividend_cache(self, series: pd.Series) -> None:
        try:
            series.to_pickle(self.div_pkl_path)
            series.to_frame(name="Dividends").to_csv(self.div_csv_path)
        except Exception:
            # Ignore cache write errors: cache is non-critical and failures should not interrupt main flow
            pass

    def _cache_covers_range(self, cached: Optional[pd.DataFrame], start: date, end: date) -> bool:
        if cached is None or cached.empty:
            return False
        try:
            dates = pd.to_datetime(cached.index).date
            return min(dates) <= start and max(dates) >= end
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
            df = ticker.history(start=start.isoformat(), end=(pd.Timestamp(end) + pd.Timedelta(days=1)).isoformat())
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
    from src.data.yahoo_provider import YahooAssetProvider
    from src.data.mock_provider import MockAssetProvider

    try:
        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)
        AssetRegistry.register("MOCK-*", MockAssetProvider, priority=0)
    except Exception:
        # best-effort: ignore registration failures
        pass
except Exception:
    # provider modules not available — fallback behavior will be used
    pass
