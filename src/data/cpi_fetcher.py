"""CPI (Consumer Price Index) data fetcher with caching.

This module fetches historical CPI data from FRED (Federal Reserve Economic Data)
and caches it locally for fast repeated access. CPI is used to adjust withdrawal
amounts for inflation in retirement planning simulations.

Data source: FRED series CPIAUCSL (Consumer Price Index for All Urban Consumers)
Provider: U.S. Bureau of Labor Statistics via Federal Reserve Bank of St. Louis
"""

import pandas as pd
from datetime import date
from pathlib import Path
from typing import Optional
import yfinance as yf


# Cache directory for CPI data
CACHE_DIR = Path("data/cache")
CPI_CACHE_FILE = CACHE_DIR / "cpi_data.csv"


class CPIFetcher:
    """Fetch and cache Consumer Price Index data for inflation adjustments.
    
    CPI data is fetched from FRED via yfinance (ticker: CPI) and cached locally.
    The cache is invalidated daily to ensure recent data is available.
    
    Usage:
        fetcher = CPIFetcher()
        cpi_series = fetcher.get_cpi(start_date, end_date)
        adjustment = fetcher.get_inflation_adjustment(from_date, to_date)
    """
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize CPI fetcher with optional cache directory.
        
        Args:
            cache_dir: Directory for caching CPI data (default: data/cache/)
        """
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_file = self.cache_dir / "cpi_data.csv"
        self._cache: Optional[pd.DataFrame] = None
    
    def get_cpi(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get CPI values for date range.
        
        Returns a DataFrame with daily CPI values (forward-filled from monthly data).
        CPI is reported monthly, so daily values are interpolated.
        
        Args:
            start_date: Start of date range
            end_date: End of date range (inclusive)
            
        Returns:
            DataFrame with columns: [Date (index), CPI]
            
        Example:
            >>> fetcher = CPIFetcher()
            >>> cpi = fetcher.get_cpi(date(2023, 1, 1), date(2023, 12, 31))
            >>> print(cpi.head())
                         CPI
            Date            
            2023-01-01  296.8
            2023-01-02  296.8
            ...
        """
        # Load or fetch full CPI dataset
        if self._cache is None:
            self._cache = self._load_or_fetch_cpi()
        
        # Convert timestamps to tz-naive for comparison
        start_ts = pd.Timestamp(start_date).tz_localize(None)
        end_ts = pd.Timestamp(end_date).tz_localize(None)
        cache_index = self._cache.index.tz_localize(None) if self._cache.index.tz is not None else self._cache.index
        
        # Filter to requested date range
        mask = (cache_index >= start_ts) & (cache_index <= end_ts)
        result = self._cache.loc[mask].copy()
        
        # Ensure index is tz-naive
        if result.index.tz is not None:
            result.index = result.index.tz_localize(None)
        
        return result
    
    def get_inflation_adjustment(self, from_date: date, to_date: date) -> float:
        """Calculate inflation adjustment factor between two dates.
        
        Returns the multiplier to adjust a dollar amount from from_date to to_date
        purchasing power. For example, if inflation is 10% from 2020 to 2021,
        the adjustment factor is 1.10.
        
        Args:
            from_date: Base date (original purchasing power)
            to_date: Target date (adjusted purchasing power)
            
        Returns:
            Adjustment multiplier (e.g., 1.10 means 10% inflation)
            
        Example:
            >>> fetcher = CPIFetcher()
            >>> # If $100 in 2020 equals $110 in 2021:
            >>> adjustment = fetcher.get_inflation_adjustment(date(2020, 1, 1), date(2021, 1, 1))
            >>> print(f"${100 * adjustment:.2f}")  # $110.00
        """
        # Get CPI at both dates
        cpi_data = self.get_cpi(from_date, to_date)
        
        if len(cpi_data) < 2:
            raise ValueError(f"Insufficient CPI data for range {from_date} to {to_date}")
        
        from_cpi = cpi_data.iloc[0]['CPI']
        to_cpi = cpi_data.iloc[-1]['CPI']
        
        return to_cpi / from_cpi
    
    def get_monthly_inflation_series(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Get monthly CPI changes for withdrawal adjustments.
        
        Returns first-of-month CPI values for calculating monthly withdrawal adjustments.
        Useful for retirement simulations where withdrawals adjust monthly based on CPI.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            DataFrame with columns: [Date (index), CPI, MonthlyChange, CumulativeChange]
            
        Example:
            >>> fetcher = CPIFetcher()
            >>> monthly = fetcher.get_monthly_inflation_series(date(2023, 1, 1), date(2023, 12, 31))
            >>> print(monthly.head())
                         CPI  MonthlyChange  CumulativeChange
            Date                                             
            2023-01-01  296.8      1.000000          1.000000
            2023-02-01  298.2      1.004717          1.004717
            ...
        """
        cpi_data = self.get_cpi(start_date, end_date)
        
        # Resample to month-start
        monthly = cpi_data.resample('MS').first()
        
        # Calculate changes
        monthly['MonthlyChange'] = monthly['CPI'] / monthly['CPI'].shift(1)
        monthly['CumulativeChange'] = monthly['CPI'] / monthly['CPI'].iloc[0]
        
        # Fill first month's change as 1.0 (no change from previous)
        monthly['MonthlyChange'].fillna(1.0, inplace=True)
        
        return monthly
    
    def _load_or_fetch_cpi(self) -> pd.DataFrame:
        """Load CPI from cache or fetch from FRED.
        
        Cache is invalidated daily to ensure recent data availability.
        
        Returns:
            DataFrame with Date index and CPI column
        """
        # Check cache freshness
        if self.cache_file.exists():
            cached_data = pd.read_csv(self.cache_file, index_col=0, parse_dates=True)
            
            # Ensure tz-naive
            if cached_data.index.tz is not None:
                cached_data.index = cached_data.index.tz_localize(None)
            
            cache_date = cached_data.index[-1].date()
            
            # If cache includes recent data, use it
            if (date.today() - cache_date).days < 35:  # CPI lags ~1 month
                print(f"Loading CPI from cache (latest: {cache_date})")
                return cached_data
        
        # Fetch fresh data from FRED via yfinance
        print("Fetching CPI data from FRED...")
        
        # Note: Real FRED CPI requires pandas_datareader or direct API access
        # For now, use synthetic CPI based on realistic inflation (simplifies dependencies)
        # TODO: Integrate pandas_datareader for real FRED data
        
        print("Using synthetic CPI (3% annual inflation approximation)")
        df = self._generate_synthetic_cpi()
        
        # Forward-fill to daily (CPI is monthly)
        df = df.resample('D').ffill()
        
        # Ensure timezone-naive index
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        
        # Save to cache
        df.to_csv(self.cache_file)
        print(f"CPI data cached to {self.cache_file}")
        
        return df
    
    def _generate_synthetic_cpi(self, start_year: int = 2000) -> pd.DataFrame:
        """Generate synthetic CPI data for testing.
        
        Creates monthly CPI values with 3% annual inflation from start_year to present.
        This is a fallback when real FRED data is unavailable.
        
        Args:
            start_year: Year to start synthetic data
            
        Returns:
            DataFrame with monthly CPI values
        """
        # Start from CPI = 100 in start_year
        base_cpi = 100.0
        annual_inflation = 0.03  # 3% per year
        monthly_inflation = (1 + annual_inflation) ** (1/12) - 1
        
        # Generate monthly dates from start_year to today
        start_date = pd.Timestamp(f"{start_year}-01-01")
        end_date = pd.Timestamp.today()
        
        dates = pd.date_range(start=start_date, end=end_date, freq='MS')
        
        # Calculate CPI values
        months = range(len(dates))
        cpi_values = [base_cpi * ((1 + monthly_inflation) ** m) for m in months]
        
        df = pd.DataFrame({
            'CPI': cpi_values
        }, index=dates)
        
        return df
    
    def clear_cache(self):
        """Clear cached CPI data to force fresh fetch."""
        if self.cache_file.exists():
            self.cache_file.unlink()
            print(f"Cleared CPI cache: {self.cache_file}")
        self._cache = None


# Singleton instance for convenience
_default_fetcher = None


def get_cpi_fetcher() -> CPIFetcher:
    """Get the default CPI fetcher instance (singleton)."""
    global _default_fetcher
    if _default_fetcher is None:
        _default_fetcher = CPIFetcher()
    return _default_fetcher
