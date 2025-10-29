"""Return adjustment utilities for inflation and market adjustments.

This module provides utilities for calculating and displaying returns in three perspectives:
1. Nominal returns - absolute dollar gains
2. Real returns - inflation-adjusted (purchasing power)
3. Alpha - market-adjusted (outperformance vs benchmark)

The framework reuses the existing Asset provider system to fetch CPI and benchmark data.
"""

from datetime import date
from typing import Any, Dict


def calculate_adjusted_returns(
    summary: Dict[str, Any],
    start_date: date,
    end_date: date,
    inflation_ticker: str = "CPI",
    market_ticker: str = "VOO",
    adjust_inflation: bool = False,
    adjust_market: bool = False,
) -> Dict[str, Any]:
    """Calculate inflation and market-adjusted returns.

    This function takes backtest results and computes additional return perspectives:
    - Real return: Adjusts for inflation using CPI data
    - Alpha: Adjusts for market performance using benchmark ticker

    Args:
        summary: Backtest summary dict with 'total_return', 'start_value', etc.
        start_date: Period start date
        end_date: Period end date
        inflation_ticker: Ticker for inflation data (default: CPI)
        market_ticker: Ticker for market benchmark (default: VOO)
        adjust_inflation: Calculate real (inflation-adjusted) returns
        adjust_market: Calculate alpha (market-adjusted) returns

    Returns:
        Dict with adjusted metrics:
            - nominal_return: Original return percentage
            - nominal_dollars: Original dollar gain
            - real_return: Inflation-adjusted return (if adjust_inflation=True)
            - real_dollars: Inflation-adjusted dollars (if adjust_inflation=True)
            - cpi_multiplier: CPI end/start ratio (if adjust_inflation=True)
            - inflation_rate: Period inflation rate (if adjust_inflation=True)
            - alpha: Excess return vs market (if adjust_market=True)
            - alpha_dollars: Excess dollars vs market (if adjust_market=True)
            - market_return: Benchmark return (if adjust_market=True)
            - benchmark: Ticker used for benchmark (if adjust_market=True)

    Example:
        >>> from datetime import date
        >>> summary = {'total_return': 0.518, 'start_value': 10000, 'total': 15180}
        >>> adjustments = calculate_adjusted_returns(
        ...     summary,
        ...     date(2024, 1, 1),
        ...     date(2024, 12, 31),
        ...     adjust_inflation=True,
        ...     adjust_market=True
        ... )
        >>> print(f"Nominal: {adjustments['nominal_return']*100:.1f}%")
        Nominal: 51.8%
        >>> print(f"Real: {adjustments['real_return']*100:.1f}%")
        Real: 48.2%
        >>> print(f"Alpha: {adjustments['alpha']*100:.1f}%")
        Alpha: 11.8%
    """
    # Import here to avoid circular dependencies
    from src.data.fetcher import Asset

    # Extract nominal metrics from summary
    nominal_return = summary.get("total_return", 0.0)
    start_val = summary.get("start_value", 0.0)
    end_val = summary.get("total", start_val)
    nominal_dollars = end_val - start_val

    result = {
        "nominal_return": nominal_return,
        "nominal_dollars": nominal_dollars,
        "start_value": start_val,
        "end_value": end_val,
    }

    # Inflation adjustment
    if adjust_inflation:
        try:
            inflation_asset = Asset(inflation_ticker)
            inflation_prices = inflation_asset.get_prices(start_date, end_date)

            if len(inflation_prices) < 2:
                raise ValueError(f"Insufficient {inflation_ticker} data for period")

            cpi_start = float(inflation_prices.iloc[0]["Close"])
            cpi_end = float(inflation_prices.iloc[-1]["Close"])
            cpi_multiplier = cpi_end / cpi_start

            # Real return = nominal return adjusted for purchasing power loss
            # If you gained 50% but inflation was 10%, your real gain is less
            real_end_val = end_val / cpi_multiplier
            real_dollars = real_end_val - start_val
            real_return = real_dollars / start_val if start_val > 0 else 0.0

            result.update(
                {
                    "real_return": real_return,
                    "real_dollars": real_dollars,
                    "cpi_multiplier": cpi_multiplier,
                    "inflation_rate": (cpi_multiplier - 1.0),
                    "purchasing_power_lost": nominal_dollars - real_dollars,
                }
            )
        except Exception as e:
            print(f"Warning: Could not calculate inflation adjustment: {e}")
            result.update(
                {
                    "real_return": None,
                    "real_dollars": None,
                    "inflation_error": str(e),
                }
            )

    # Market adjustment
    if adjust_market:
        try:
            market_asset = Asset(market_ticker)
            market_prices = market_asset.get_prices(start_date, end_date)

            if len(market_prices) < 2:
                raise ValueError(f"Insufficient {market_ticker} data for period")

            market_start = float(market_prices.iloc[0]["Close"])
            market_end = float(market_prices.iloc[-1]["Close"])
            market_return = (market_end - market_start) / market_start

            # Alpha = your return - market return
            # If you made 50% and market made 40%, your alpha is 10%
            alpha = nominal_return - market_return
            alpha_dollars = nominal_dollars - (start_val * market_return)

            result.update(
                {
                    "market_return": market_return,
                    "alpha": alpha,
                    "alpha_dollars": alpha_dollars,
                    "benchmark": market_ticker,
                }
            )
        except Exception as e:
            print(f"Warning: Could not calculate market adjustment: {e}")
            result.update(
                {
                    "alpha": None,
                    "alpha_dollars": None,
                    "market_error": str(e),
                }
            )

    return result


def print_adjusted_returns(adjustments: Dict[str, Any], verbose: bool = False) -> None:
    """Print formatted adjusted return metrics.

    Args:
        adjustments: Dict from calculate_adjusted_returns()
        verbose: If True, print detailed multi-line format.
                 If False, print compact single-line format.

    Example (verbose=False):
        Nominal: +51.8% ($5,180) | Real: +38.2% ($3,820) | Alpha: +11.8% ($1,180 vs VOO)

    Example (verbose=True):
        ======================================================================
        RETURN BREAKDOWN
        ======================================================================

        Nominal Return:
          Total Return:                     +51.80%
          Dollar Gain:                   $5,180.00

        Inflation-Adjusted Return:
          Real Return:                      +38.20%
          Real Dollar Gain:              $3,820.00
          CPI Multiplier:                    1.100
          Period Inflation:                 +10.00%
          Purchasing Power Lost:         $1,360.00

        Market-Adjusted Return (vs VOO):
          Alpha:                            +11.80%
          Alpha Dollars:                 $1,180.00
          Market Return:                    +40.00%
        ======================================================================
    """
    if verbose:
        print("\n" + "=" * 70)
        print("RETURN BREAKDOWN")
        print("=" * 70)
        print()
        print("Nominal Return:")
        print(f"  Total Return:                {adjustments['nominal_return']*100:>10.2f}%")
        print(f"  Dollar Gain:                 ${adjustments['nominal_dollars']:>10,.2f}")

        if "real_return" in adjustments and adjustments["real_return"] is not None:
            print()
            print("Inflation-Adjusted Return:")
            print(f"  Real Return:                 {adjustments['real_return']*100:>10.2f}%")
            print(f"  Real Dollar Gain:            ${adjustments['real_dollars']:>10,.2f}")
            print(f"  CPI Multiplier:              {adjustments['cpi_multiplier']:>10.3f}")
            print(f"  Period Inflation:            {adjustments['inflation_rate']*100:>10.2f}%")
            print(f"  Purchasing Power Lost:       ${adjustments['purchasing_power_lost']:>10,.2f}")
        elif "inflation_error" in adjustments:
            print()
            print(f"Inflation-Adjusted Return: ERROR - {adjustments['inflation_error']}")

        if "alpha" in adjustments and adjustments["alpha"] is not None:
            print()
            print(f"Market-Adjusted Return (vs {adjustments['benchmark']}):")
            print(f"  Alpha:                       {adjustments['alpha']*100:>10.2f}%")
            print(f"  Alpha Dollars:               ${adjustments['alpha_dollars']:>10,.2f}")
            print(f"  Market Return:               {adjustments['market_return']*100:>10.2f}%")
        elif "market_error" in adjustments:
            print()
            print(f"Market-Adjusted Return: ERROR - {adjustments['market_error']}")

        print("=" * 70)
    else:
        # Compact format
        parts = [
            f"Nominal: {adjustments['nominal_return']*100:+.2f}% (${adjustments['nominal_dollars']:,.2f})"
        ]

        if "real_return" in adjustments and adjustments["real_return"] is not None:
            parts.append(
                f"Real: {adjustments['real_return']*100:+.2f}% (${adjustments['real_dollars']:,.2f})"
            )

        if "alpha" in adjustments and adjustments["alpha"] is not None:
            parts.append(
                f"Alpha: {adjustments['alpha']*100:+.2f}% (${adjustments['alpha_dollars']:,.2f} vs {adjustments['benchmark']})"
            )

        print(" | ".join(parts))


def format_adjustment_summary(adjustments: Dict[str, Any]) -> str:
    """Format adjustment summary as a single-line string for logging.

    Args:
        adjustments: Dict from calculate_adjusted_returns()

    Returns:
        Formatted string like "Nominal: +51.8%, Real: +38.2%, Alpha: +11.8%"
    """
    parts = [f"Nominal: {adjustments['nominal_return']*100:+.2f}%"]

    if "real_return" in adjustments and adjustments["real_return"] is not None:
        parts.append(f"Real: {adjustments['real_return']*100:+.2f}%")

    if "alpha" in adjustments and adjustments["alpha"] is not None:
        parts.append(f"Alpha: {adjustments['alpha']*100:+.2f}%")

    return ", ".join(parts)


def add_adjusted_columns_to_summary(
    summary: Dict[str, Any], adjustments: Dict[str, Any]
) -> Dict[str, Any]:
    """Add adjusted return columns to backtest summary dict.

    This is useful for CSV export and programmatic access.

    Args:
        summary: Original backtest summary dict
        adjustments: Dict from calculate_adjusted_returns()

    Returns:
        Updated summary dict with additional keys:
            - real_return, real_dollars (if available)
            - alpha, alpha_dollars, market_return (if available)
            - inflation_rate, cpi_multiplier (if available)
    """
    result = summary.copy()

    # Add inflation-adjusted metrics
    if "real_return" in adjustments and adjustments["real_return"] is not None:
        result.update(
            {
                "real_return": adjustments["real_return"],
                "real_dollars": adjustments["real_dollars"],
                "inflation_rate": adjustments["inflation_rate"],
                "cpi_multiplier": adjustments["cpi_multiplier"],
                "purchasing_power_lost": adjustments["purchasing_power_lost"],
            }
        )

    # Add market-adjusted metrics
    if "alpha" in adjustments and adjustments["alpha"] is not None:
        result.update(
            {
                "alpha": adjustments["alpha"],
                "alpha_dollars": adjustments["alpha_dollars"],
                "market_return": adjustments["market_return"],
                "benchmark": adjustments["benchmark"],
            }
        )

    return result
