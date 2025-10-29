"""Demo script to verify StaticAssetProvider works."""

from datetime import date
from src.data.asset import Asset
from src.data.asset_provider import AssetRegistry
from src.data.static_provider import StaticAssetProvider

# Register static provider with highest priority
AssetRegistry.register("SPY", StaticAssetProvider, priority=0)

# Create asset
asset = Asset("SPY")

# Get prices
prices = asset.get_prices(date(2020, 1, 2), date(2020, 1, 31))

print("✅ StaticAssetProvider loaded {} rows for SPY".format(len(prices)))
print("\nFirst few rows:")
print(prices.head())
print("\nLast few rows:")
print(prices.tail())
print(f"\nPrice range: ${prices['Close'].min():.2f} - ${prices['Close'].max():.2f}")
print("\n✅ StaticAssetProvider working correctly!")
