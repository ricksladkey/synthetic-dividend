"""Mock asset provider for testing and mathematical signposts.

Provides synthetic/deterministic price data for testing algorithms without
network dependencies or real market data variability.
"""

from datetime import date, timedelta

import numpy as np
import pandas as pd

from src.data.asset_provider import AssetProvider


class MockAssetProvider(AssetProvider):
    """Mock asset provider for testing and mathematical scenarios.

    Generates deterministic price data based on configurable patterns:
    - Flat prices (constant value)
    - Linear trends (steady growth/decline)
    - Sine waves (cyclical volatility)
    - Step functions (sudden jumps)
    - Random walk (controlled randomness)

    Example:
        >>> # Register mock for testing
        >>> from src.data.asset_provider import AssetRegistry
        >>> AssetRegistry.register("MOCK-FLAT-100", MockAssetProvider, priority=1)
        >>>
        >>> # Use in backtest
        >>> asset = Asset("MOCK-FLAT-100")
        >>> prices = asset.get_prices(date(2024, 1, 1), date(2024, 12, 31))
        >>> # All prices exactly $100.00

    Pattern Syntax (ticker format):
        MOCK-FLAT-{price}       : Flat prices at specified level
        MOCK-LINEAR-{start}-{end}: Linear trend from start to end price
        MOCK-SINE-{base}-{amp}  : Sine wave with base price and amplitude
        MOCK-STEP-{start}-{step}: Step function with sudden jumps
        MOCK-WALK-{start}       : Random walk starting at price
    """

    def __init__(self, ticker: str, cache_dir: str = "cache") -> None:
        """Initialize mock provider based on ticker pattern.

        Args:
            ticker: Mock ticker pattern (e.g., "MOCK-FLAT-100")
            cache_dir: Ignored (mocks don't cache)
        """
        super().__init__(ticker, cache_dir)
        self._parse_pattern()

    def _parse_pattern(self) -> None:
        """Parse ticker pattern to determine price generation strategy."""
        parts = self.ticker.split("-")

        if len(parts) < 2 or parts[0] != "MOCK":
            raise ValueError(f"Invalid mock pattern: {self.ticker}")

        self.pattern_type = parts[1].upper()
        self.params = parts[2:] if len(parts) > 2 else []

    def get_prices(self, start_date: date, end_date: date) -> pd.DataFrame:
        """Generate mock OHLC prices based on pattern.

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            DataFrame with OHLC columns
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        # Generate daily date range
        dates = pd.date_range(start=start_date, end=end_date, freq="D")
        n = len(dates)

        # Generate close prices based on pattern
        if self.pattern_type == "FLAT":
            # MOCK-FLAT-100 -> constant $100.00
            price = float(self.params[0]) if self.params else 100.0
            close = np.full(n, price)

        elif self.pattern_type == "LINEAR":
            # MOCK-LINEAR-100-200 -> linear from $100 to $200
            start_price = float(self.params[0]) if len(self.params) > 0 else 100.0
            end_price = float(self.params[1]) if len(self.params) > 1 else 200.0
            close = np.linspace(start_price, end_price, n)

        elif self.pattern_type == "SINE":
            # MOCK-SINE-100-20 -> sine wave, base $100, amplitude $20
            base = float(self.params[0]) if len(self.params) > 0 else 100.0
            amplitude = float(self.params[1]) if len(self.params) > 1 else 20.0
            # Complete 4 cycles over the period
            t = np.linspace(0, 4 * 2 * np.pi, n)
            close = base + amplitude * np.sin(t)

        elif self.pattern_type == "STEP":
            # MOCK-STEP-100-10 -> step function, $100 base, $10 steps
            start_price = float(self.params[0]) if len(self.params) > 0 else 100.0
            step_size = float(self.params[1]) if len(self.params) > 1 else 10.0
            # Step up every 30 days
            steps = n // 30
            close = np.repeat(
                [start_price + i * step_size for i in range(steps + 1)],
                [min(30, n - i * 30) for i in range(steps + 1)],
            )[:n]

        elif self.pattern_type == "WALK":
            # MOCK-WALK-100 -> random walk starting at $100
            start_price = float(self.params[0]) if self.params else 100.0
            # Controlled randomness: ±1% daily moves
            np.random.seed(hash(self.ticker) % (2**32))  # Deterministic per ticker
            returns = np.random.normal(0, 0.01, n)
            # Start with first price = start_price, then apply returns
            close = np.empty(n)
            close[0] = start_price
            close[1:] = start_price * np.cumprod(1 + returns[1:])

        else:
            raise ValueError(f"Unknown mock pattern: {self.pattern_type}")

        # Generate OHLC from close prices
        # Add small intraday volatility (±0.5%)
        np.random.seed(hash(self.ticker + str(start_date)) % (2**32))
        noise = np.random.uniform(-0.005, 0.005, n)

        df = pd.DataFrame(
            {
                "Open": close * (1 - abs(noise) / 2),
                "High": close * (1 + abs(noise)),
                "Low": close * (1 - abs(noise)),
                "Close": close,
            },
            index=dates,
        )

        return df

    def get_dividends(self, start_date: date, end_date: date) -> pd.Series:
        """Mock dividends - configurable via pattern extension.

        For now, mocks don't pay dividends. Future: MOCK-DIV-pattern

        Args:
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            Empty Series (no dividends for basic mocks)
        """
        if start_date > end_date:
            raise ValueError(f"start_date ({start_date}) must be <= end_date ({end_date})")

        # Future enhancement: parse dividend patterns
        # MOCK-DIV-QUARTERLY-0.25 -> quarterly $0.25/share payments
        return pd.Series(dtype=float)

    def clear_cache(self) -> None:
        """No-op for mock provider (no caching)."""
        pass


# Convenience factory for common patterns
def create_flat_mock(price: float = 100.0) -> str:
    """Create flat-price mock ticker.

    Args:
        price: Constant price level

    Returns:
        Mock ticker string
    """
    return f"MOCK-FLAT-{price}"


def create_trend_mock(start: float = 100.0, end: float = 200.0) -> str:
    """Create linear trend mock ticker.

    Args:
        start: Starting price
        end: Ending price

    Returns:
        Mock ticker string
    """
    return f"MOCK-LINEAR-{start}-{end}"


def create_volatile_mock(base: float = 100.0, amplitude: float = 20.0) -> str:
    """Create sine wave volatility mock ticker.

    Args:
        base: Base price level
        amplitude: Volatility amplitude

    Returns:
        Mock ticker string
    """
    return f"MOCK-SINE-{base}-{amplitude}"
