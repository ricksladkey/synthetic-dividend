"""Portfolio definitions: parse named portfolio strings into allocations.

This module provides a factory for converting human-readable portfolio names
into asset allocation dictionaries, similar to how the algorithm factory
converts algorithm names into algorithm instances.

Supported formats:
    Named portfolios with default allocations:
        'classic' → 60% stocks (VOO), 40% bonds (BIL)
        'classic-plus-crypto' → 60% VOO, 30% BIL, 10% BTC-USD
        'buffet' → 90% stocks (VOO), 10% bonds (BIL)
        'all-weather' → 40% VOO, 15% TLT, 15% IEF, 7.5% GLD, 7.5% DBC
        'three-fund' → 40% VTI, 30% VXUS, 30% BND
        'golden-butterfly' → 20% each: VOO, SHY, TLT, GLD, cash/BIL

    Named portfolios with custom allocations (parameters):
        'classic-60,40' → 60% VOO, 40% BIL
        'classic-70,30' → 70% VOO, 30% BIL
        'classic-plus-crypto-60,30,10' → 60% VOO, 30% BIL, 10% BTC-USD
        'classic-plus-crypto-50,30,20' → 50% VOO, 30% BIL, 20% BTC-USD
        'buffet-90,10' → 90% VOO, 10% BIL
        'buffet-95,5' → 95% VOO, 5% BIL
        'tech-growth-60,40' → 60% QQQ, 40% VOO
        'tech-growth-70,30' → 70% QQQ, 30% VOO

Examples:
    >>> allocations = parse_portfolio_name('classic')
    >>> allocations
    {'VOO': 0.6, 'BIL': 0.4}

    >>> allocations = parse_portfolio_name('classic-70,30')
    >>> allocations
    {'VOO': 0.7, 'BIL': 0.3}

    >>> allocations = parse_portfolio_name('classic-plus-crypto-60,30,10')
    >>> allocations
    {'VOO': 0.6, 'BIL': 0.3, 'BTC-USD': 0.1}
"""

import re
from typing import Dict


def parse_portfolio_name(name: str) -> Dict[str, float]:
    """Parse portfolio name into allocations dictionary.

    Args:
        name: Portfolio name string, optionally with parameters

    Returns:
        Dict mapping ticker symbols to allocation fractions (0.0 to 1.0)

    Raises:
        ValueError: If portfolio name is not recognized or parameters are invalid

    Examples:
        >>> parse_portfolio_name('classic')
        {'VOO': 0.6, 'BIL': 0.4}

        >>> parse_portfolio_name('buffet-95,5')
        {'VOO': 0.95, 'BIL': 0.05}
    """
    name = name.strip()
    print(f"Parsing portfolio name: {name}")

    # Classic 60/40 portfolio (stocks/bonds)
    if name == "classic":
        print("  -> Classic 60/40: VOO 60%, BIL 40%")
        return {"VOO": 0.6, "BIL": 0.4}

    # Classic with custom allocations
    m = re.match(r"^classic-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        stock_pct = float(m.group(1))
        bond_pct = float(m.group(2))
        print(f"  -> Classic custom: VOO {stock_pct}%, BIL {bond_pct}%")
        return {"VOO": stock_pct / 100.0, "BIL": bond_pct / 100.0}

    # Classic plus crypto (stocks/bonds/crypto)
    if name == "classic-plus-crypto":
        print("  -> Classic+Crypto 60/30/10: VOO 60%, BIL 30%, BTC-USD 10%")
        return {"VOO": 0.6, "BIL": 0.3, "BTC-USD": 0.1}

    # Classic plus crypto with custom allocations
    m = re.match(
        r"^classic-plus-crypto-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name
    )
    if m:
        stock_pct = float(m.group(1))
        bond_pct = float(m.group(2))
        crypto_pct = float(m.group(3))
        print(
            f"  -> Classic+Crypto custom: VOO {stock_pct}%, BIL {bond_pct}%, "
            f"BTC-USD {crypto_pct}%"
        )
        return {
            "VOO": stock_pct / 100.0,
            "BIL": bond_pct / 100.0,
            "BTC-USD": crypto_pct / 100.0,
        }

    # Buffett portfolio (90/10 stocks/bonds)
    if name == "buffet" or name == "buffett":
        print("  -> Buffett 90/10: VOO 90%, BIL 10%")
        return {"VOO": 0.9, "BIL": 0.1}

    # Buffett with custom allocations
    m = re.match(r"^buffet(?:t)?-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        stock_pct = float(m.group(1))
        bond_pct = float(m.group(2))
        print(f"  -> Buffett custom: VOO {stock_pct}%, BIL {bond_pct}%")
        return {"VOO": stock_pct / 100.0, "BIL": bond_pct / 100.0}

    # All-Weather portfolio (Ray Dalio)
    if name == "all-weather":
        print("  -> All-Weather: VOO 40%, TLT 15%, IEF 15%, GLD 7.5%, DBC 7.5%, BIL 15%")
        return {
            "VOO": 0.40,  # Stocks
            "TLT": 0.15,  # Long-term bonds
            "IEF": 0.15,  # Intermediate bonds
            "GLD": 0.075,  # Gold
            "DBC": 0.075,  # Commodities
            "BIL": 0.15,  # Cash/T-bills
        }

    # Three-fund portfolio (Bogleheads)
    if name == "three-fund":
        print("  -> Three-Fund: VTI 40%, VXUS 30%, BND 30%")
        return {
            "VTI": 0.40,  # Total US stock market
            "VXUS": 0.30,  # Total international stock market
            "BND": 0.30,  # Total bond market
        }

    # Golden Butterfly (Tyler's Portfolio)
    if name == "golden-butterfly":
        print("  -> Golden Butterfly: VOO 20%, SHY 20%, TLT 20%, GLD 20%, BIL 20%")
        return {
            "VOO": 0.20,  # US stocks
            "SHY": 0.20,  # Short-term bonds
            "TLT": 0.20,  # Long-term bonds
            "GLD": 0.20,  # Gold
            "BIL": 0.20,  # Cash
        }

    # Tech growth portfolio
    if name == "tech-growth":
        print("  -> Tech Growth 60/40: QQQ 60%, VOO 40%")
        return {"QQQ": 0.6, "VOO": 0.4}

    # Tech growth with custom allocations
    m = re.match(r"^tech-growth-(\d+(?:\.\d+)?),(\d+(?:\.\d+)?)$", name)
    if m:
        tech_pct = float(m.group(1))
        market_pct = float(m.group(2))
        print(f"  -> Tech Growth custom: QQQ {tech_pct}%, VOO {market_pct}%")
        return {"QQQ": tech_pct / 100.0, "VOO": market_pct / 100.0}

    # High-growth tech portfolio
    if name == "high-growth":
        print("  -> High Growth: NVDA 30%, QQQ 40%, VOO 30%")
        return {
            "NVDA": 0.30,  # High-growth stock
            "QQQ": 0.40,  # Tech-heavy index
            "VOO": 0.30,  # Broad market
        }

    # Crypto-heavy portfolio
    if name == "crypto-heavy":
        print("  -> Crypto Heavy: BTC-USD 40%, ETH-USD 20%, VOO 30%, BIL 10%")
        return {
            "BTC-USD": 0.40,
            "ETH-USD": 0.20,
            "VOO": 0.30,
            "BIL": 0.10,
        }

    raise ValueError(
        f"Unrecognized portfolio name: {name}\n"
        f"Supported portfolios:\n"
        f"  - classic, classic-60,40, classic-70,30\n"
        f"  - classic-plus-crypto, classic-plus-crypto-60,30,10\n"
        f"  - buffet, buffet-90,10, buffet-95,5\n"
        f"  - all-weather (Ray Dalio)\n"
        f"  - three-fund (Bogleheads)\n"
        f"  - golden-butterfly (Tyler's Portfolio)\n"
        f"  - tech-growth, tech-growth-60,40\n"
        f"  - high-growth\n"
        f"  - crypto-heavy\n"
    )
