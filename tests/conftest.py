"""Pytest configuration for synthetic-dividend tests.

This file is automatically loaded by pytest and sets up global test fixtures.
"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_static_provider_for_ci():
    """Auto-register StaticAssetProvider when running in CI environment.

    This enables tests to run without network access by using committed
    historical data from testdata/ directory.

    The fixture runs once per test session and registers the static provider
    with high priority (0) ONLY for tickers that have data available.
    """
    # Check if we're in CI environment
    is_ci = os.getenv("CI", "false").lower() == "true"
    is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"

    if is_ci or is_github_actions:
        # Import here to avoid issues if modules not available
        try:
            from src.data.asset_provider import AssetRegistry
            from src.data.static_provider import StaticAssetProvider

            # Find testdata directory
            src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            testdata_dir = os.path.join(src_dir, "testdata")

            # Register static provider only for tickers that have data
            if os.path.exists(testdata_dir):
                registered_count = 0
                for filename in os.listdir(testdata_dir):
                    if filename.endswith(".csv") and not filename.endswith("_dividends.csv"):
                        ticker = filename[:-4]  # Remove .csv extension
                        AssetRegistry.register(ticker, StaticAssetProvider, priority=0)
                        registered_count += 1

                print(
                    f"\n✅ CI mode: StaticAssetProvider registered for {registered_count} tickers with offline data"
                )
            else:
                print(f"\n⚠️  Warning: testdata directory not found at {testdata_dir}")
        except ImportError as e:
            print(f"\n⚠️  Warning: Could not register StaticAssetProvider: {e}")

    yield  # Run tests

    # No cleanup needed - provider registry resets naturally
