"""CPI (Consumer Price Index) data fetcher with caching and provider pattern.

This module provides a CPIFetcher class to access Consumer Price Index data,
which is essential for inflation adjustments.

It uses a provider pattern to abstract the data source:
- FredCPIProvider: Fetches real CPI data (series: CPIAUCSL) from FRED.
- SyntheticCPIProvider: Generates predictable, synthetic CPI data for testing.
"""

import logging
from abc import ABC, abstractmethod
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import pandas_datareader.data as pdr

_log = logging.getLogger(__name__)

# --- CPI Data Providers ---


class _CPIProvider(ABC):
    """Abstract base class for a CPI data provider."""

    @abstractmethod
    def fetch(self) -> pd.DataFrame:
        """Fetches the entire history of CPI data.

        Returns:
            pd.DataFrame: A DataFrame with a DatetimeIndex and a 'CPI' column.
        """
        pass


class FredCPIProvider(_CPIProvider):
    """Fetches real CPI data from FRED."""

    def fetch(self) -> pd.DataFrame:
        """Fetches CPIAUCSL series from FRED, starting from the year 2000."""
        _log.info("Fetching real CPI data (CPIAUCSL) from FRED...")
        try:
            # Fetch data from FRED
            cpi_df = pdr.DataReader("CPIAUCSL", "fred", start="2000-01-01")
            # Rename column for consistency
            cpi_df = cpi_df.rename(columns={"CPIAUCSL": "CPI"})
            return cpi_df
        except Exception as e:
            _log.error(f"Failed to fetch CPI data from FRED: {e}")
            # Return an empty DataFrame on failure
            return pd.DataFrame({"CPI": []})


class SyntheticCPIProvider(_CPIProvider):
    """Generates synthetic CPI data with a fixed annual inflation rate."""

    def __init__(self, annual_inflation: float = 0.03, start_year: int = 2000):
        self.annual_inflation = annual_inflation
        self.start_year = start_year

    def fetch(self) -> pd.DataFrame:
        """Generates monthly CPI values from start_year to present."""
        _log.info(
            f"Generating synthetic CPI data with {self.annual_inflation:.1%} annual inflation..."
        )
        base_cpi = 100.0
        monthly_inflation = (1 + self.annual_inflation) ** (1 / 12) - 1

        start_date = pd.Timestamp(f"{self.start_year}-01-01")
        end_date = pd.Timestamp.today()
        dates = pd.date_range(start=start_date, end=end_date, freq="MS")

        months = range(len(dates))
        cpi_values = [base_cpi * ((1 + monthly_inflation) ** m) for m in months]

        return pd.DataFrame({"CPI": cpi_values}, index=dates)


# --- Main CPI Fetcher Class ---


class CPIFetcher:
    """Fetches, caches, and processes Consumer Price Index data."""

    def __init__(self, provider: _CPIProvider, cache_dir: str = "data/cache"):
        self.provider = provider
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cpi_data.csv"
        self._cache: Optional[pd.DataFrame] = None

    def get_cpi(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get daily CPI values for a date range (forward-filled)."""
        if self._cache is None:
            self._cache = self._load_or_fetch_cpi()

        start_ts = pd.Timestamp(start_date)
        end_ts = pd.Timestamp(end_date)

        # Ensure cache index is timezone-naive before filtering
        cache_index = self._cache.index
        if cache_index.tz is not None:
            cache_index = cache_index.tz_localize(None)

        mask = (cache_index >= start_ts) & (cache_index <= end_ts)
        return self._cache.loc[mask].copy()

    def get_inflation_adjustment(self, from_date: date, to_date: date) -> float:
        """Calculate the inflation adjustment factor between two dates."""
        cpi_data = self.get_cpi(from_date, to_date)
        if len(cpi_data) < 2:
            raise ValueError(f"Insufficient CPI data for range {from_date} to {to_date}")

        from_cpi = cpi_data.iloc[0]["CPI"]
        to_cpi = cpi_data.iloc[-1]["CPI"]
        return float(to_cpi / from_cpi)

    def get_monthly_inflation_series(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get a series of monthly CPI changes."""
        cpi_data = self.get_cpi(start_date, end_date)
        monthly = cpi_data.resample("MS").first()

        monthly["MonthlyChange"] = monthly["CPI"] / monthly["CPI"].shift(1)
        monthly["CumulativeChange"] = monthly["CPI"] / monthly["CPI"].iloc[0]
        monthly["MonthlyChange"].fillna(1.0, inplace=True)
        return monthly

    def _load_or_fetch_cpi(self) -> pd.DataFrame:
        """Load CPI from cache or fetch from the provider."""
        if self.cache_file.exists():
            cached_data = pd.read_csv(self.cache_file, index_col=0, parse_dates=True)
            cache_date = cached_data.index[-1].date()

            # CPI data lags by about a month, so 35 days is a safe buffer.
            if (date.today() - cache_date).days < 35:
                _log.info(f"Loading CPI from cache (latest: {cache_date})")
                return cached_data

        # Fetch fresh data using the provider
        df = self.provider.fetch()
        if df.empty:
            _log.warning("Fetched CPI data is empty. Using stale cache if available.")
            if self.cache_file.exists():
                return pd.read_csv(self.cache_file, index_col=0, parse_dates=True)
            return df  # Return empty df if no cache exists

        # Process and cache the new data
        df = df.resample("D").ffill()
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        df.to_csv(self.cache_file)
        _log.info(f"CPI data cached to {self.cache_file}")
        return df

    def clear_cache(self):
        """Clear cached CPI data to force a fresh fetch."""
        if self.cache_file.exists():
            self.cache_file.unlink()
            _log.info(f"Cleared CPI cache: {self.cache_file}")
        self._cache = None
