"""Portfolio comparison command-line tool.

Compare multiple portfolio allocations and visualize results.

Usage:
    python -m src.tools.portfolio_comparison --preset crypto_stocks
    python -m src.tools.portfolio_comparison --custom "NVDA:0.5,VOO:0.5"
"""

import argparse
from datetime import date, datetime
from typing import Dict, TypedDict

from src.models.portfolio_simulator import compare_portfolios, simulate_portfolio
from src.visualization.composition_chart import (
    plot_portfolio_comparison,
    plot_portfolio_composition,
)

class Preset(TypedDict):
    name: str
    allocations: Dict[str, float]

# Preset portfolio allocations
PRESETS: Dict[str, Preset] = {
    "crypto_stocks": {
        "name": "Crypto/Stocks Mix",
        "allocations": {
            "NVDA": 0.20,
            "GOOG": 0.20,
            "PLTR": 0.20,
            "BTC-USD": 0.20,
            "ETH-USD": 0.20,
        },
    },
    "tech_heavy": {
        "name": "Tech Heavy",
        "allocations": {
            "NVDA": 0.30,
            "GOOG": 0.30,
            "MSFT": 0.20,
            "AAPL": 0.20,
        },
    },
    "conservative": {
        "name": "Conservative (100% VOO)",
        "allocations": {
            "VOO": 1.00,
        },
    },
    "balanced": {
        "name": "Balanced",
        "allocations": {
            "VOO": 0.60,
            "NVDA": 0.20,
            "BTC-USD": 0.10,
            "ETH-USD": 0.10,
        },
    },
}


def parse_custom_allocation(allocation_str: str) -> Dict[str, float]:
    """Parse custom allocation string like 'NVDA:0.5,VOO:0.5'."""
    allocations = {}
    for pair in allocation_str.split(","):
        ticker, weight = pair.split(":")
        allocations[ticker.strip()] = float(weight.strip())
    return allocations


def parse_date(date_str: str) -> date:
    """Parse date from string (YYYY-MM-DD or MM/DD/YYYY)."""
    for fmt in ["%Y-%m-%d", "%m/%d/%Y"]:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date format: {date_str}. Use YYYY-MM-DD or MM/DD/YYYY")


def main():
    parser = argparse.ArgumentParser(
        description="Compare portfolio allocations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Compare crypto/stocks mix vs VOO
  python -m src.tools.portfolio_comparison --compare crypto_stocks conservative

  # Single portfolio with custom allocation
  python -m src.tools.portfolio_comparison --custom "NVDA:0.5,VOO:0.5"

  # Use preset
  python -m src.tools.portfolio_comparison --preset tech_heavy --start 2023-01-01
        """,
    )

    parser.add_argument("--preset", choices=list(PRESETS.keys()), help="Use preset allocation")

    parser.add_argument("--custom", help='Custom allocation (e.g., "NVDA:0.5,VOO:0.5")')

    parser.add_argument(
        "--compare",
        nargs="+",
        choices=list(PRESETS.keys()),
        help="Compare multiple preset portfolios",
    )

    parser.add_argument(
        "--start",
        default="2023-01-01",
        help="Start date (YYYY-MM-DD or MM/DD/YYYY, default: 2023-01-01)",
    )

    parser.add_argument(
        "--end",
        default="2024-12-31",
        help="End date (YYYY-MM-DD or MM/DD/YYYY, default: 2024-12-31)",
    )

    parser.add_argument(
        "--initial", type=float, default=1_000_000, help="Initial investment (default: 1,000,000)"
    )

    parser.add_argument("--output", help="Output chart filename (PNG/PDF)")

    parser.add_argument("--no-chart", action="store_true", help="Skip chart generation")

    args = parser.parse_args()

    # Parse dates
    start_date = parse_date(args.start)
    end_date = parse_date(args.end)

    # Comparison mode
    if args.compare:
        portfolio_configs = [
            (PRESETS[preset]["name"], PRESETS[preset]["allocations"]) for preset in args.compare  # type: ignore
        ]

        result = compare_portfolios(portfolio_configs, start_date, end_date, args.initial)

        print(result["summary"])

        if not args.no_chart:
            output_file = args.output or f"portfolio_comparison_{args.start}_{args.end}.png"
            plot_portfolio_comparison(
                result["results"],
                title=f"Portfolio Comparison ({args.start} to {args.end})",
                output_file=output_file,
            )

    # Single portfolio mode
    elif args.preset or args.custom:
        if args.preset:
            name = PRESETS[args.preset]["name"]
            allocations = PRESETS[args.preset]["allocations"]  # type: ignore
        else:
            name = "Custom Portfolio"
            allocations = parse_custom_allocation(args.custom)

        result = simulate_portfolio(allocations, start_date, end_date, args.initial)

        print(f"\n{result['summary']}")

        if not args.no_chart:
            output_file = (
                args.output
                or f"portfolio_{name.lower().replace(' ', '_')}_{args.start}_{args.end}.png"
            )
            plot_portfolio_composition(
                result["daily_values"],
                allocations,
                title=f"{name} ({args.start} to {args.end})",
                output_file=output_file,
            )

    else:
        parser.print_help()
        print("\nError: Must specify --preset, --custom, or --compare")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
