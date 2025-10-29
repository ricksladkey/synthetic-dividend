"""Demo: Mock assets work transparently in the system."""

from datetime import date

from src.data.asset import Asset
from src.data.asset_provider import AssetRegistry
from src.data.mock_provider import MockAssetProvider

# Register mock provider
AssetRegistry.register("MOCK-*", MockAssetProvider, priority=0)

# Create different mock assets
flat = Asset("MOCK-FLAT-100")
trend = Asset("MOCK-LINEAR-100-200")
volatile = Asset("MOCK-SINE-100-20")

# Fetch prices
d1, d2 = date(2024, 1, 1), date(2024, 12, 31)
fp = flat.get_prices(d1, d2)
tp = trend.get_prices(d1, d2)
vp = volatile.get_prices(d1, d2)

print("=" * 60)
print("MOCK ASSET DEMONSTRATION")
print("=" * 60)
print(f"\nFLAT: All prices = ${fp['Close'].iloc[0]:.2f}")
print(f"TREND: Start=${tp['Close'].iloc[0]:.2f}, End=${tp['Close'].iloc[-1]:.2f}")
print(
    f"VOLATILE: Min=${vp['Close'].min():.2f}, Max=${vp['Close'].max():.2f}, Mean=${vp['Close'].mean():.2f}"
)
print("\n" + "=" * 60)
print("KEY INSIGHT: Zero special casing needed!")
print("=" * 60)
print("\nThese mocks work IDENTICALLY to:")
print("  - Asset('NVDA')     # Yahoo Finance")
print("  - Asset('USD')      # Cash provider")
print("  - Asset('BTC-USD')  # Crypto")
print("\nThe algorithm doesn't know or care about providers.")
print("The registry pattern = extensibility without forking.")
