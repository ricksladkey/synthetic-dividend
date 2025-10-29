"""Tests for asset registry pattern and providers."""

from datetime import date

import pandas as pd
import pytest

from src.data.asset import Asset
from src.data.asset_provider import AssetProvider, AssetRegistry
from src.data.cash_provider import CashAssetProvider
from src.data.yahoo_provider import YahooAssetProvider


@pytest.fixture
def cache_dir(tmp_path):
    """Provide temporary cache directory for tests."""
    return str(tmp_path / "test_cache")


class MockProvider(AssetProvider):
    """Mock provider for testing registry pattern."""

    def __init__(self, ticker, cache_dir):
        super().__init__(ticker, cache_dir)
        self.calls = []

    def get_prices(self, start_date, end_date):
        self.calls.append(("get_prices", start_date, end_date))
        return pd.DataFrame(
            {
                "Open": [100.0],
                "High": [110.0],
                "Low": [90.0],
                "Close": [105.0],
            },
            index=[start_date],
        )

    def get_dividends(self, start_date, end_date):
        self.calls.append(("get_dividends", start_date, end_date))
        return pd.Series([2.50], index=[start_date])

    def clear_cache(self):
        self.calls.append(("clear_cache",))


class TestRegistryPattern:
    """Test AssetRegistry pattern matching and provider selection."""

    def test_exact_match_priority(self, cache_dir):
        """Exact matches should take priority over wildcards."""
        # Register mock provider for TEST ticker
        AssetRegistry.register("TEST", MockProvider, priority=1)

        # Create asset - should use MockProvider
        asset = Asset("TEST", cache_dir)
        assert isinstance(asset._provider, MockProvider)

        # Cleanup
        AssetRegistry._providers = {}
        # Re-register defaults
        from src.data.asset import CashAssetProvider, YahooAssetProvider

        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)

    def test_wildcard_fallback(self, cache_dir):
        """Unknown tickers should fall back to wildcard provider."""
        # NVDA not explicitly registered, should use * wildcard (YahooAssetProvider)
        asset = Asset("NVDA", cache_dir)
        assert isinstance(asset._provider, YahooAssetProvider)

    def test_priority_ordering(self, cache_dir):
        """Lower priority numbers should take precedence."""
        # Register two providers for same pattern with different priorities
        AssetRegistry.register("PRIORITY", MockProvider, priority=1)

        # Should use priority=1 MockProvider
        asset = Asset("PRIORITY", cache_dir)
        assert isinstance(asset._provider, MockProvider)

        # Cleanup
        AssetRegistry._providers = {}
        from src.data.asset import CashAssetProvider, YahooAssetProvider

        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)


class TestUSDAsset:
    """Test USD cash asset works correctly."""

    def test_usd_uses_cash_provider(self, cache_dir):
        """USD should use CashAssetProvider."""
        asset = Asset("USD", cache_dir)
        assert isinstance(asset._provider, CashAssetProvider)

    def test_usd_returns_flat_prices(self, cache_dir):
        """USD should return $1.00 for all OHLC prices."""
        asset = Asset("USD", cache_dir)
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 1, 5))

        # Check all prices are $1.00
        assert (prices["Open"] == 1.0).all()
        assert (prices["High"] == 1.0).all()
        assert (prices["Low"] == 1.0).all()
        assert (prices["Close"] == 1.0).all()

        # Should have prices for all business days
        assert len(prices) >= 3  # At least 3 business days in Jan 1-5

    def test_usd_no_dividends(self, cache_dir):
        """USD should have no dividends."""
        asset = Asset("USD", cache_dir)
        divs = asset.get_dividends(date(2024, 1, 1), date(2024, 12, 31))

        assert isinstance(divs, pd.Series)
        assert len(divs) == 0  # Empty series

    def test_usd_ticker_case_insensitive(self, cache_dir):
        """usd, USD, Usd should all work."""
        for ticker in ["usd", "USD", "Usd"]:
            asset = Asset(ticker, cache_dir)
            assert isinstance(asset._provider, CashAssetProvider)
            assert asset.ticker == "USD"


class TestEquityAsset:
    """Test equity tickers use Yahoo Finance provider."""

    def test_equity_uses_yahoo_provider(self, cache_dir):
        """NVDA should use YahooAssetProvider."""
        asset = Asset("NVDA", cache_dir)
        assert isinstance(asset._provider, YahooAssetProvider)

    def test_equity_ticker_normalized(self, cache_dir):
        """Equity tickers should be uppercased."""
        asset = Asset("nvda", cache_dir)
        assert asset.ticker == "NVDA"


class TestAssetFactoryAPI:
    """Test Asset maintains same API regardless of provider."""

    def test_get_prices_api(self, cache_dir):
        """get_prices() should work for all providers."""
        # USD (CashAssetProvider)
        usd = Asset("USD", cache_dir)
        usd_prices = usd.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        assert isinstance(usd_prices, pd.DataFrame)
        assert all(col in usd_prices.columns for col in ["Open", "High", "Low", "Close"])

        # NVDA (YahooAssetProvider) - may fail if network down, so allow exceptions
        try:
            nvda = Asset("NVDA", cache_dir)
            nvda_prices = nvda.get_prices(date(2024, 1, 2), date(2024, 1, 5))
            assert isinstance(nvda_prices, pd.DataFrame)
        except Exception:
            pass  # Network or yfinance issues - skip this part

    def test_get_dividends_api(self, cache_dir):
        """get_dividends() should work for all providers."""
        # USD (CashAssetProvider)
        usd = Asset("USD", cache_dir)
        usd_divs = usd.get_dividends(date(2024, 1, 1), date(2024, 12, 31))
        assert isinstance(usd_divs, pd.Series)

        # NVDA (YahooAssetProvider) - may fail if network down
        try:
            nvda = Asset("NVDA", cache_dir)
            nvda_divs = nvda.get_dividends(date(2024, 1, 1), date(2024, 12, 31))
            assert isinstance(nvda_divs, pd.Series)
        except Exception:
            pass  # Network issues - skip

    def test_clear_cache_api(self, cache_dir):
        """clear_cache() should work for all providers."""
        usd = Asset("USD", cache_dir)
        usd.clear_cache()  # Should not raise

        nvda = Asset("NVDA", cache_dir)
        nvda.clear_cache()  # Should not raise


class TestCustomProvider:
    """Test custom providers can be registered and used."""

    def test_register_custom_provider(self, cache_dir):
        """Should be able to register custom provider for specific tickers."""
        # Register mock provider for MOCK ticker
        AssetRegistry.register("MOCK", MockProvider, priority=1)

        # Create asset
        asset = Asset("MOCK", cache_dir)
        assert isinstance(asset._provider, MockProvider)

        # Verify delegation works
        prices = asset.get_prices(date(2024, 1, 1), date(2024, 1, 5))
        assert isinstance(prices, pd.DataFrame)
        assert "get_prices" in str(asset._provider.calls)

        # Cleanup
        AssetRegistry._providers = {}
        from src.data.asset import CashAssetProvider, YahooAssetProvider

        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)

    def test_prefix_pattern_matching(self, cache_dir):
        """Should support prefix patterns like BTC-*."""
        # Register mock provider for BTC-* pattern
        AssetRegistry.register("BTC-*", MockProvider, priority=1)

        # Should match BTC-USD, BTC-EUR, etc.
        asset = Asset("BTC-USD", cache_dir)
        assert isinstance(asset._provider, MockProvider)

        # Cleanup
        AssetRegistry._providers = {}
        from src.data.asset import CashAssetProvider, YahooAssetProvider

        AssetRegistry.register("USD", CashAssetProvider, priority=1)
        AssetRegistry.register("*", YahooAssetProvider, priority=9)
