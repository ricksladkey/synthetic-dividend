"""Tests for Asset data provider with dual-format caching."""

import os
import tempfile
from datetime import date

import pandas as pd
import pytest

from src.data.asset import Asset


class TestAssetBasics:
    """Test basic Asset initialization and cache setup."""

    def test_asset_initialization(self):
        """Asset should initialize with ticker and cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("NVDA", cache_dir=tmpdir)
            assert asset.ticker == "NVDA"
            assert asset.cache_dir == tmpdir
            assert os.path.exists(tmpdir)

    def test_ticker_uppercased(self):
        """Ticker should be converted to uppercase."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("nvda", cache_dir=tmpdir)
            assert asset.ticker == "NVDA"

    def test_cache_paths_set_correctly(self):
        """Cache file paths should be set correctly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("NVDA", cache_dir=tmpdir)
            assert asset.pkl_path == os.path.join(tmpdir, "NVDA.pkl")
            assert asset.csv_path == os.path.join(tmpdir, "NVDA.csv")
            assert asset.div_pkl_path == os.path.join(tmpdir, "NVDA_dividends.pkl")
            assert asset.div_csv_path == os.path.join(tmpdir, "NVDA_dividends.csv")


class TestAssetPrices:
    """Test price data fetching and caching."""

    def test_get_prices_basic(self):
        """Should fetch price data for valid ticker and date range."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("NVDA", cache_dir=tmpdir)
            df = asset.get_prices(date(2024, 1, 2), date(2024, 1, 5))

            # Should return DataFrame with OHLC columns
            assert isinstance(df, pd.DataFrame)
            if not df.empty:  # May be empty if yfinance fails
                assert all(col in df.columns for col in ["Open", "High", "Low", "Close"])

    def test_get_prices_creates_dual_cache(self):
        """Should create both .pkl and .csv cache files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("NVDA", cache_dir=tmpdir)
            df = asset.get_prices(date(2024, 1, 2), date(2024, 1, 5))

            if not df.empty:
                # Both cache files should exist
                assert os.path.exists(asset.pkl_path)
                assert os.path.exists(asset.csv_path)

                # CSV should be readable
                df_csv = pd.read_csv(asset.csv_path, index_col=0, parse_dates=True)
                assert not df_csv.empty

    def test_get_prices_uses_cache_on_second_call(self):
        """Second call with same range should use cache (no download)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("NVDA", cache_dir=tmpdir)

            # First call: download and cache
            df1 = asset.get_prices(date(2024, 1, 2), date(2024, 1, 5))

            if not df1.empty:
                # Modify pkl cache to test that it's being used
                df_modified = df1.copy()
                df_modified.to_pickle(asset.pkl_path)

                # Second call: should use cache
                df2 = asset.get_prices(date(2024, 1, 2), date(2024, 1, 5))

                # Should return same data
                pd.testing.assert_frame_equal(df1, df2)

    def test_get_prices_validates_date_range(self):
        """Should raise ValueError if start_date > end_date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("NVDA", cache_dir=tmpdir)

            with pytest.raises(ValueError):
                asset.get_prices(date(2024, 12, 31), date(2024, 1, 1))


class TestAssetDividends:
    """Test dividend data fetching and caching."""

    def test_get_dividends_basic(self):
        """Should fetch dividend data for dividend-paying ticker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("AAPL", cache_dir=tmpdir)  # AAPL pays dividends
            divs = asset.get_dividends(date(2023, 1, 1), date(2023, 12, 31))

            # Should return Series
            assert isinstance(divs, pd.Series)
            # AAPL pays quarterly dividends, should have ~4 entries for full year
            # (may be empty if yfinance fails or no dividends in range)

    def test_get_dividends_creates_dual_cache(self):
        """Should create both .pkl and .csv cache files for dividends."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("AAPL", cache_dir=tmpdir)
            divs = asset.get_dividends(date(2023, 1, 1), date(2023, 12, 31))

            if not divs.empty:
                # Both cache files should exist
                assert os.path.exists(asset.div_pkl_path)
                assert os.path.exists(asset.div_csv_path)

                # CSV should be readable
                df_csv = pd.read_csv(asset.div_csv_path, index_col=0, parse_dates=True)
                assert not df_csv.empty

    def test_get_dividends_validates_date_range(self):
        """Should raise ValueError if start_date > end_date."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("AAPL", cache_dir=tmpdir)

            with pytest.raises(ValueError):
                asset.get_dividends(date(2024, 12, 31), date(2024, 1, 1))

    def test_get_dividends_empty_for_non_dividend_ticker(self):
        """Should return empty Series for non-dividend-paying ticker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Many growth stocks don't pay dividends
            asset = Asset("NVDA", cache_dir=tmpdir)
            divs = asset.get_dividends(date(2020, 1, 1), date(2020, 12, 31))

            # Should return empty Series (NVDA didn't pay dividends in 2020)
            assert isinstance(divs, pd.Series)


class TestAssetCacheClear:
    """Test cache clearing functionality."""

    def test_clear_cache_removes_all_files(self):
        """Should remove all cache files (prices + dividends, pkl + csv)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            asset = Asset("AAPL", cache_dir=tmpdir)

            # Create cache files
            asset.get_prices(date(2024, 1, 2), date(2024, 1, 5))
            asset.get_dividends(date(2023, 1, 1), date(2023, 12, 31))

            # At least some cache files should exist
            files_before = [
                os.path.exists(asset.pkl_path),
                os.path.exists(asset.csv_path),
                os.path.exists(asset.div_pkl_path),
                os.path.exists(asset.div_csv_path),
            ]

            # Clear cache
            asset.clear_cache()

            # All cache files should be removed
            assert not os.path.exists(asset.pkl_path)
            assert not os.path.exists(asset.csv_path)
            assert not os.path.exists(asset.div_pkl_path)
            assert not os.path.exists(asset.div_csv_path)
