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
    with high priority (0) so it overrides network-based providers when
    static data is available.
    """
    # Check if we're in CI environment
    is_ci = os.getenv("CI", "false").lower() == "true"
    is_github_actions = os.getenv("GITHUB_ACTIONS", "false").lower() == "true"

    if is_ci or is_github_actions:
        # Import here to avoid issues if modules not available
        try:
            from src.data.asset_provider import AssetRegistry
            from src.data.static_provider import StaticAssetProvider

            # Register static provider with highest priority for all tickers
            # It will return empty DataFrame if file doesn't exist, allowing fallback
            AssetRegistry.register("*", StaticAssetProvider, priority=0)

            print("\n✅ CI mode: StaticAssetProvider registered for offline testing")
        except ImportError as e:
            print(f"\n⚠️  Warning: Could not register StaticAssetProvider: {e}")

    yield  # Run tests

    # No cleanup needed - provider registry resets naturally
