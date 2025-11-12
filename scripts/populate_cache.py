#!/usr/bin/env python3
"""
Populate cache with 5 years of historical data for commonly used tickers.

This ensures all examples and tests can run offline without hitting Yahoo Finance.
Covers any date range request in the last 5 years for these tickers.

Usage:
    python scripts/populate_cache.py
    python scripts/populate_cache.py --tickers NVDA SPY  # Specific tickers only
    python scripts/populate_cache.py --years 10  # Fetch 10 years instead of 5
"""

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.fetcher import HistoryFetcher

# Commonly used tickers in examples, tests, and research
COMMON_TICKERS = [
    # Growth stocks (high volatility)
    "NVDA",  # NVIDIA - AI/GPU leader
    "MSTR",  # MicroStrategy - Bitcoin proxy
    "PLTR",  # Palantir - Data analytics
    "SHOP",  # Shopify - E-commerce
    "GOOG",  # Google - Tech giant

    # Small cap growth (very high volatility)
    "SOUN",  # SoundHound AI - Voice AI
    "APP",   # AppLovin - Mobile advertising

    # Crypto (extreme volatility)
    "BTC-USD",  # Bitcoin
    "ETH-USD",  # Ethereum

    # Index ETFs (moderate volatility)
    "SPY",   # S&P 500
    "VOO",   # Vanguard S&P 500
    "QQQ",   # NASDAQ-100
    "DIA",   # Dow Jones
    "IWM",   # Russell 2000 Small Cap

    # Gold/Commodities (low-moderate volatility)
    "GLD",   # SPDR Gold Trust
    "GLDM",  # SPDR Gold Shares (lower expense)
    "SLV",   # Silver ETF

    # Risk-free/Cash equivalents
    "BIL",   # 1-3 Month T-Bills
    "^IRX",  # 13-week Treasury Bill yield

    # Sector ETFs
    "XLK",   # Technology sector
    "XLF",   # Financial sector
    "XLE",   # Energy sector
]


def populate_cache(tickers: list, years: int = 5, cache_dir: str = "cache"):
    """
    Fetch and cache historical data for specified tickers.

    Args:
        tickers: List of ticker symbols
        years: Number of years of historical data to fetch
        cache_dir: Cache directory path
    """
    # Calculate date range (years ago to today)
    end_date = date.today()
    start_date = end_date - timedelta(days=years * 365)

    print("=" * 70)
    print(f"CACHE POPULATION: {years} years of data")
    print("=" * 70)
    print(f"Date range: {start_date} to {end_date}")
    print(f"Cache directory: {cache_dir}")
    print(f"Tickers: {len(tickers)}")
    print()

    fetcher = HistoryFetcher(cache_dir=cache_dir)

    success_count = 0
    fail_count = 0
    skipped_count = 0

    for i, ticker in enumerate(tickers, 1):
        print(f"[{i}/{len(tickers)}] {ticker}...", end=" ", flush=True)

        try:
            # Fetch OHLC data (automatically caches)
            df = fetcher.get_history(ticker, start_date, end_date)

            if df is None or df.empty:
                print("❌ No data available")
                fail_count += 1
                continue

            days = len(df)
            date_start = df.index[0].date()
            date_end = df.index[-1].date()

            print(f"✅ {days} days ({date_start} to {date_end})")
            success_count += 1

            # Also try to fetch dividends (bonus, don't fail on error)
            try:
                div_data = fetcher.get_dividends(ticker, start_date, end_date)
                if div_data is not None and not div_data.empty:
                    print(f"    └─ Dividends: {len(div_data)} payments")
            except Exception:
                pass  # Dividends optional

        except Exception as e:
            print(f"❌ Error: {e}")
            fail_count += 1

    print()
    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed:  {fail_count}")
    print(f"Total:     {len(tickers)}")
    print()
    print(f"Cache populated in: {cache_dir}/")
    print(f"Any date range in last {years} years will now work offline! 🎉")


def main():
    parser = argparse.ArgumentParser(
        description="Populate cache with historical data for common tickers"
    )
    parser.add_argument(
        "--tickers",
        nargs="+",
        default=COMMON_TICKERS,
        help=f"Tickers to cache (default: {len(COMMON_TICKERS)} common tickers)",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=5,
        help="Years of historical data to fetch (default: 5)",
    )
    parser.add_argument(
        "--cache-dir",
        default="cache",
        help="Cache directory path (default: cache)",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List default tickers and exit",
    )

    args = parser.parse_args()

    if args.list:
        print("Default tickers:")
        for category, tickers_group in [
            ("Growth Stocks", COMMON_TICKERS[0:5]),
            ("Small Cap Growth", COMMON_TICKERS[5:7]),
            ("Crypto", COMMON_TICKERS[7:9]),
            ("Index ETFs", COMMON_TICKERS[9:14]),
            ("Gold/Commodities", COMMON_TICKERS[14:17]),
            ("Risk-Free", COMMON_TICKERS[17:19]),
            ("Sector ETFs", COMMON_TICKERS[19:]),
        ]:
            print(f"\n{category}:")
            for ticker in tickers_group:
                print(f"  - {ticker}")
        return

    populate_cache(args.tickers, args.years, args.cache_dir)


if __name__ == "__main__":
    main()
