"""Tests for the CPI fetcher and its data providers."""

import pandas as pd
import pytest
from datetime import date
from pathlib import Path

from src.data.cpi_fetcher import (
    CPIFetcher,
    FredCPIProvider,
    SyntheticCPIProvider,
)


@pytest.fixture
def temp_cache_dir(tmp_path: Path) -> Path:
    """Provides a temporary directory for caching."""
    return tmp_path / "test_cache"


class TestSyntheticCPIProvider:
    def test_fetch_returns_dataframe(self):
        """Ensures the synthetic provider returns a valid DataFrame."""
        provider = SyntheticCPIProvider()
        df = provider.fetch()
        assert isinstance(df, pd.DataFrame)
        assert "CPI" in df.columns
        assert isinstance(df.index, pd.DatetimeIndex)
        assert not df.empty

    def test_inflation_rate(self):
        """Check if the synthetic data reflects the specified inflation rate."""
        provider = SyntheticCPIProvider(annual_inflation=0.05) # 5% inflation
        df = provider.fetch()
        # Check CPI after one year
        cpi_year_0 = df['CPI'].iloc[0]
        cpi_year_1 = df['CPI'].iloc[12] # 12 months later
        assert cpi_year_1 == pytest.approx(cpi_year_0 * 1.05, rel=1e-3)


class TestFredCPIProvider:
    def test_fetch_with_mock(self, monkeypatch):
        """Tests the FRED provider by mocking the pandas_datareader call."""
        # Create a mock DataFrame that looks like FRED data
        mock_dates = pd.date_range(start="2023-01-01", periods=3, freq='MS')
        mock_df = pd.DataFrame({"CPIAUCSL": [300, 301, 302]}, index=mock_dates)

        # Mock the DataReader function
        def mock_datareader(*args, **kwargs):
            return mock_df

        monkeypatch.setattr("pandas_datareader.data.DataReader", mock_datareader)

        provider = FredCPIProvider()
        df = provider.fetch()

        assert isinstance(df, pd.DataFrame)
        assert "CPI" in df.columns  # Should be renamed from CPIAUCSL
        assert not df.empty
        pd.testing.assert_series_equal(df['CPI'], mock_df['CPIAUCSL'], check_names=False)


class TestCPIFetcher:
    def test_initialization(self, temp_cache_dir: Path):
        """Test that the fetcher initializes correctly with a provider."""
        provider = SyntheticCPIProvider()
        fetcher = CPIFetcher(provider=provider, cache_dir=str(temp_cache_dir))
        assert fetcher.provider is provider
        assert fetcher.cache_dir == temp_cache_dir

    def test_get_cpi_with_synthetic_data(self, temp_cache_dir: Path):
        """Test fetching and processing of synthetic CPI data."""
        provider = SyntheticCPIProvider()
        fetcher = CPIFetcher(provider=provider, cache_dir=str(temp_cache_dir))

        start = date(2022, 1, 1)
        end = date(2022, 12, 31)
        cpi_data = fetcher.get_cpi(start, end)

        assert isinstance(cpi_data, pd.DataFrame)
        assert not cpi_data.empty
        assert cpi_data.index.min().date() == start
        assert cpi_data.index.max().date() == end

    def test_inflation_adjustment(self, temp_cache_dir: Path):
        """Test the inflation adjustment calculation."""
        provider = SyntheticCPIProvider(annual_inflation=0.1) # 10% for easy math
        fetcher = CPIFetcher(provider=provider, cache_dir=str(temp_cache_dir))

        adj = fetcher.get_inflation_adjustment(date(2010, 1, 1), date(2011, 1, 1))
        assert adj == pytest.approx(1.10, rel=1e-3)

    def test_cache_creation_and_usage(self, temp_cache_dir: Path, monkeypatch):
        """Ensure cache is created on first call and used on second call."""
        # Mock provider to track calls
        class MockProvider(SyntheticCPIProvider):
            fetch_calls = 0
            def fetch(self):
                self.fetch_calls += 1
                return super().fetch()

        provider = MockProvider()
        fetcher = CPIFetcher(provider=provider, cache_dir=str(temp_cache_dir))
        cache_file = fetcher.cache_file

        # 1. First call: should fetch and create cache
        assert not cache_file.exists()
        fetcher.get_cpi(date(2020, 1, 1), date(2020, 1, 31))
        assert provider.fetch_calls == 1
        assert cache_file.exists()

        # 2. Second call: should use cache, not fetch
        fetcher.get_cpi(date(2020, 1, 1), date(2020, 1, 31))
        assert provider.fetch_calls == 1 # Should not have increased

    def test_clear_cache(self, temp_cache_dir: Path):
        """Test that clear_cache removes the cache file."""
        provider = SyntheticCPIProvider()
        fetcher = CPIFetcher(provider=provider, cache_dir=str(temp_cache_dir))
        cache_file = fetcher.cache_file

        # Create the cache
        fetcher.get_cpi(date(2020, 1, 1), date(2020, 1, 31))
        assert cache_file.exists()

        # Clear it
        fetcher.clear_cache()
        assert not cache_file.exists()
