"""Tests for cache integrity and isolation.

These tests ensure that cache files are not corrupted by test data and that
tests properly isolate their cache usage.
"""

import os
import tempfile

import pandas as pd
import pytest

from src.data.asset import Asset


@pytest.fixture
def temp_cache_dir():
    """Provide a temporary cache directory for tests."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


class TestCacheIntegrity:
    """Test that cache files maintain data integrity."""

    def test_cache_not_corrupted_by_uniform_data(self, temp_cache_dir):
        """Ensure cache doesn't get polluted with uniform test data."""
        # Create an asset with temp cache
        asset = Asset("TEST", temp_cache_dir)

        # Simulate real market data (varying prices)
        real_data = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0, 103.0],
                "High": [105.0, 106.0, 107.0, 108.0],
                "Low": [95.0, 96.0, 97.0, 98.0],
                "Close": [102.0, 103.0, 104.0, 105.0],
            },
            index=pd.date_range("2024-01-01", periods=4),
        )

        # Cache the real data
        asset._save_price_cache(real_data)

        # Verify cache contains varying data
        cached = asset._load_price_cache()
        assert cached is not None
        assert not cached.empty

        # Check that OHLC values are not all identical (uniform)
        for col in ["Open", "High", "Low", "Close"]:
            unique_values = cached[col].unique()
            assert len(unique_values) > 1, f"Column {col} has uniform values: {unique_values}"

    def test_cache_merge_preserves_existing_data(self, temp_cache_dir):
        """Test that cache merging doesn't overwrite existing data."""
        asset = Asset("TEST", temp_cache_dir)

        # First batch of data
        data1 = pd.DataFrame(
            {
                "Open": [100.0, 101.0],
                "High": [105.0, 106.0],
                "Low": [95.0, 96.0],
                "Close": [102.0, 103.0],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )

        # Second batch of data (different dates)
        data2 = pd.DataFrame(
            {
                "Open": [102.0, 103.0],
                "High": [107.0, 108.0],
                "Low": [97.0, 98.0],
                "Close": [104.0, 105.0],
            },
            index=pd.date_range("2024-01-03", periods=2),
        )

        # Cache first batch
        asset._save_price_cache(data1)

        # Cache second batch (should merge)
        asset._save_price_cache(data2)

        # Verify all data is preserved
        cached = asset._load_price_cache()
        assert cached is not None
        assert len(cached) == 4  # All 4 days

        # Check chronological order
        assert cached.index.is_monotonic_increasing

    def test_detect_uniform_cache_corruption(self, temp_cache_dir):
        """Test that we can detect when cache has been corrupted with uniform data."""
        asset = Asset("BIL", temp_cache_dir)

        # Simulate corrupted cache (uniform values)
        corrupted_data = pd.DataFrame(
            {
                "Open": [100.0] * 10,
                "High": [100.0] * 10,
                "Low": [100.0] * 10,
                "Close": [100.0] * 10,
            },
            index=pd.date_range("2024-01-01", periods=10),
        )

        asset._save_price_cache(corrupted_data)

        # Function to check for corruption
        def is_cache_corrupted(asset_obj):
            cached = asset_obj._load_price_cache()
            if cached is None or cached.empty:
                return False  # Empty cache is not corrupted

            # Check if all OHLC values are identical across all rows
            for col in ["Open", "High", "Low", "Close"]:
                unique_vals = cached[col].unique()
                if len(unique_vals) <= 1:  # All values are the same
                    return True
            return False

        # Should detect corruption
        assert is_cache_corrupted(asset), "Failed to detect uniform cache corruption"

    def test_cache_isolation_prevents_cross_test_pollution(self, temp_cache_dir):
        """Test that using temp cache directories prevents test pollution."""
        # Test 1: Create asset with varying data
        asset1 = Asset("SHARED", temp_cache_dir)
        data1 = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [95.0, 96.0, 97.0],
                "Close": [102.0, 103.0, 104.0],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        asset1._save_price_cache(data1)

        # Test 2: Different asset instance should not see test 1's data
        # (since we're using the same temp directory, this tests isolation doesn't work)
        # Actually, this demonstrates the problem - shared cache dirs cause pollution

        asset2 = Asset("SHARED", temp_cache_dir)
        cached = asset2._load_price_cache()

        # This should have the data from test 1, demonstrating pollution
        assert cached is not None
        assert len(cached) == 3

        # But if we use different cache dirs, there should be no pollution
        with tempfile.TemporaryDirectory() as tmp_dir2:
            asset3 = Asset("SHARED", tmp_dir2)
            cached2 = asset3._load_price_cache()
            assert cached2 is None  # No data in isolated cache


class TestCacheValidation:
    """Test cache validation utilities."""

    def test_validate_cache_data_integrity(self, temp_cache_dir):
        """Test function to validate cache data integrity."""

        def validate_cache_integrity(cache_file_path):
            """Check if cache file contains valid, non-uniform data."""
            if not os.path.exists(cache_file_path):
                return True  # Non-existent cache is valid

            try:
                df = pd.read_csv(cache_file_path, index_col=0, parse_dates=True)
            except Exception:
                return False  # Can't read = invalid

            if df.empty:
                return True  # Empty cache is valid

            # Check for uniform values (corruption indicator)
            for col in ["Open", "High", "Low", "Close"]:
                if col not in df.columns:
                    continue
                unique_vals = df[col].unique()
                if len(unique_vals) <= 1 and len(df) > 1:
                    return False  # Uniform values in multi-row cache = corrupted

            # Check for reasonable price ranges (not all zeros or extreme values)
            for col in ["Open", "High", "Low", "Close"]:
                if col not in df.columns:
                    continue
                values = df[col].dropna()
                if len(values) == 0:
                    continue
                if (values <= 0).all():
                    return False  # All non-positive prices = invalid
                if (values > 1e6).all():
                    return False  # All extremely high prices = suspicious

            return True

        asset = Asset("TEST", temp_cache_dir)

        # Test valid data
        valid_data = pd.DataFrame(
            {
                "Open": [100.0, 101.0, 102.0],
                "High": [105.0, 106.0, 107.0],
                "Low": [95.0, 96.0, 97.0],
                "Close": [102.0, 103.0, 104.0],
            },
            index=pd.date_range("2024-01-01", periods=3),
        )

        asset._save_price_cache(valid_data)
        assert validate_cache_integrity(asset.csv_path), "Valid cache should pass validation"

        # Test corrupted data (uniform values) - use different asset
        corrupted_asset = Asset("CORRUPTED", temp_cache_dir)
        corrupted_data = pd.DataFrame(
            {
                "Open": [100.0] * 5,
                "High": [100.0] * 5,
                "Low": [100.0] * 5,
                "Close": [100.0] * 5,
            },
            index=pd.date_range("2024-01-01", periods=5),
        )

        corrupted_asset._save_price_cache(corrupted_data)
        assert not validate_cache_integrity(
            corrupted_asset.csv_path
        ), "Corrupted cache should fail validation"

        # Test invalid data (negative prices) - use different asset
        invalid_asset = Asset("INVALID", temp_cache_dir)
        invalid_data = pd.DataFrame(
            {
                "Open": [-100.0, -101.0],
                "High": [-105.0, -106.0],
                "Low": [-95.0, -96.0],
                "Close": [-102.0, -103.0],
            },
            index=pd.date_range("2024-01-01", periods=2),
        )

        invalid_asset._save_price_cache(invalid_data)
        assert not validate_cache_integrity(
            invalid_asset.csv_path
        ), "Invalid cache should fail validation"


class TestCacheIsolation:
    """Test that tests properly isolate cache usage."""

    def test_asset_uses_specified_cache_dir(self, temp_cache_dir):
        """Asset should use the cache directory specified in constructor."""
        asset = Asset("TEST", temp_cache_dir)

        # Cache some data
        data = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [95.0],
                "Close": [102.0],
            },
            index=pd.date_range("2024-01-01", periods=1),
        )

        asset._save_price_cache(data)

        # Check that files were created in the specified directory
        assert os.path.exists(os.path.join(temp_cache_dir, "TEST.csv"))
        assert os.path.exists(os.path.join(temp_cache_dir, "TEST.pkl"))

        # Note: Some other code may create files in default cache directory,
        # but this test verifies that the Asset uses the specified cache dir

    def test_cache_cleanup_removes_files(self, temp_cache_dir):
        """Asset.clear_cache() should remove cache files."""
        asset = Asset("TEST", temp_cache_dir)

        # Cache some data
        data = pd.DataFrame(
            {
                "Open": [100.0],
                "High": [105.0],
                "Low": [95.0],
                "Close": [102.0],
            },
            index=pd.date_range("2024-01-01", periods=1),
        )

        asset._save_price_cache(data)

        # Verify files exist
        assert os.path.exists(asset.csv_path)
        assert os.path.exists(asset.pkl_path)

        # Clear cache
        asset.clear_cache()

        # Verify files are gone
        assert not os.path.exists(asset.csv_path)
        assert not os.path.exists(asset.pkl_path)
