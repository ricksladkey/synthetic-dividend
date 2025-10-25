"""Asset class definitions and metadata for research studies.

Categorizes assets by volatility regime and provides lookup functions
for batch testing and analysis.
"""
from typing import Dict, List

# Asset class definitions with expected volatility characteristics
ASSET_CLASSES: Dict[str, Dict[str, any]] = {
    "growth_stocks": {
        "tickers": ["NVDA", "GOOG", "PLTR", "MSTR", "SHOP"],
        "description": "High-growth technology and data companies",
        "expected_volatility": "high",
        "recommended_sd": [6, 8, 10, 12],  # Test range for exponential scaling
    },
    "crypto": {
        "tickers": ["BTC-USD", "ETH-USD"],
        "description": "Cryptocurrency assets (Bitcoin, Ethereum)",
        "expected_volatility": "extreme",
        "recommended_sd": [4, 6, 8, 10],  # More frequent rebalancing for high vol
    },
    "commodities": {
        "tickers": ["GLD", "SLV"],
        "description": "Precious metals ETFs",
        "expected_volatility": "moderate",
        "recommended_sd": [8, 10, 12, 16],  # Less frequent for stable assets
    },
    "indices": {
        "tickers": ["SPY", "QQQ", "DIA"],
        "description": "Major market index ETFs",
        "expected_volatility": "low-moderate",
        "recommended_sd": [10, 12, 16, 20],  # Lowest frequency for stable indices
    },
}

# Exponential scaling lookup: sdN → rebalance trigger %
# Formula: 2^(1/N) - 1
SD_LOOKUP: Dict[int, float] = {
    4: 18.9207,   # 2^(1/4) - 1
    5: 14.8698,   # 2^(1/5) - 1
    6: 12.2462,   # 2^(1/6) - 1
    8: 9.0508,    # 2^(1/8) - 1 (legacy default)
    10: 7.1773,   # 2^(1/10) - 1
    12: 5.9463,   # 2^(1/12) - 1
    16: 4.4271,   # 2^(1/16) - 1
    20: 3.5265,   # 2^(1/20) - 1
    24: 2.9302,   # 2^(1/24) - 1
}


def get_all_tickers() -> List[str]:
    """Return flattened list of all tickers across asset classes."""
    tickers = []
    for asset_class in ASSET_CLASSES.values():
        tickers.extend(asset_class["tickers"])
    return tickers


def get_tickers_by_class(class_name: str) -> List[str]:
    """Return tickers for a specific asset class."""
    if class_name not in ASSET_CLASSES:
        raise ValueError(f"Unknown asset class: {class_name}")
    return ASSET_CLASSES[class_name]["tickers"]


def get_class_for_ticker(ticker: str) -> str:
    """Return asset class name for a given ticker."""
    for class_name, data in ASSET_CLASSES.items():
        if ticker in data["tickers"]:
            return class_name
    return "unknown"


def get_recommended_sd_values(ticker: str) -> List[int]:
    """Return recommended sdN values to test for a given ticker."""
    class_name = get_class_for_ticker(ticker)
    if class_name == "unknown":
        return [4, 6, 8, 10, 12, 16]  # Default test range
    return ASSET_CLASSES[class_name]["recommended_sd"]


def calculate_sd_trigger(n: int) -> float:
    """Calculate rebalance trigger % for sdN exponential scaling.
    
    Formula: (2^(1/N) - 1) * 100
    
    Args:
        n: Number of geometric steps to doubling
        
    Returns:
        Rebalance trigger percentage
    """
    return (pow(2.0, 1.0 / n) - 1.0) * 100.0


def print_sd_reference_table():
    """Print comprehensive reference table for sdN values."""
    print("\n" + "="*70)
    print("EXPONENTIAL SCALING REFERENCE: sdN → Rebalance Trigger")
    print("="*70)
    print(f"{'sdN':<8} {'Trigger %':<12} {'Description':<50}")
    print("-"*70)
    
    sd_values = [4, 5, 6, 8, 10, 12, 16, 20, 24]
    for n in sd_values:
        trigger = calculate_sd_trigger(n)
        if n == 8:
            desc = "(Legacy default: 9.05% rebalance)"
        elif n <= 6:
            desc = "(Aggressive: high volatility assets)"
        elif n <= 12:
            desc = "(Moderate: balanced approach)"
        else:
            desc = "(Conservative: stable assets)"
        print(f"sd{n:<6} {trigger:>10.4f}%  {desc}")
    
    print("="*70)
    print("\nFormula: rebalance_trigger = (2^(1/N) - 1) * 100")
    print("N = number of equal geometric steps to reach doubling (100% gain)")
    print("="*70 + "\n")


if __name__ == "__main__":
    print_sd_reference_table()
    
    print("\nASSET CLASSES:")
    for class_name, data in ASSET_CLASSES.items():
        print(f"\n{class_name.upper()}:")
        print(f"  Tickers: {', '.join(data['tickers'])}")
        print(f"  Volatility: {data['expected_volatility']}")
        print(f"  Recommended sdN values: {data['recommended_sd']}")
