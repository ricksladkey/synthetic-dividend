"""Demo: Ticker data retrieval and aggregation.

Shows how to retrieve OHLC candle data for assets with different time aggregations
(daily, weekly, monthly) using the synthetic-dividend-tool ticker command.
"""

import subprocess
import sys
from datetime import date, timedelta


def run_command(cmd):
    """Run a command and return the result."""
    print(f"$ {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode


def main():
    print("=" * 80)
    print("TICKER DATA DEMO: OHLC Candle Data Retrieval")
    print("=" * 80)
    print()

    # Use NVDA as our example ticker
    ticker = "NVDA"
    end_date = date.today()
    start_date = end_date - timedelta(days=90)  # Last 3 months

    print(f"Using ticker: {ticker}")
    print(f"Date range: {start_date} to {end_date}")
    print()

    # Demo 1: Daily data
    print("-" * 80)
    print("Demo 1: Daily OHLC Data")
    print("-" * 80)
    print("Retrieving daily candle data (most recent 10 days):")
    print()

    cmd = f"python -m src.synthetic_dividend_tool run ticker --ticker {ticker} --start {start_date} --end {end_date} --interval daily | head -11"
    run_command(cmd)

    print()

    # Demo 2: Weekly aggregation
    print("-" * 80)
    print("Demo 2: Weekly Aggregated Data")
    print("-" * 80)
    print("Same data aggregated to weekly candles:")
    print()

    cmd = f"python -m src.synthetic_dividend_tool run ticker --ticker {ticker} --start {start_date} --end {end_date} --interval weekly"
    run_command(cmd)

    print()

    # Demo 3: Monthly aggregation
    print("-" * 80)
    print("Demo 3: Monthly Aggregated Data")
    print("-" * 80)
    print("Same data aggregated to monthly candles:")
    print()

    cmd = f"python -m src.synthetic_dividend_tool run ticker --ticker {ticker} --start {start_date} --end {end_date} --interval monthly"
    run_command(cmd)

    print()

    # Demo 4: Saving to file
    print("-" * 80)
    print("Demo 4: Saving Results to CSV File")
    print("-" * 80)
    print("Saving weekly data to ticker_demo_output.csv:")
    print()

    output_file = "ticker_demo_output.csv"
    cmd = f"python -m src.synthetic_dividend_tool run ticker --ticker {ticker} --start {start_date} --end {end_date} --interval weekly --output {output_file}"
    run_command(cmd)

    print(f"File saved. First 5 lines of {output_file}:")
    try:
        with open(output_file, "r") as f:
            for i, line in enumerate(f):
                if i < 5:
                    print(line.rstrip())
                else:
                    break
    except FileNotFoundError:
        print("File not found")

    # Clean up
    import os

    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"\nCleaned up {output_file}")

    print()
    print("=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print()
    print("The ticker command provides OHLC data in CSV format with columns:")
    print("Date,Ticker,O,C,L,H")
    print()
    print("Use cases:")
    print("- Technical analysis and charting")
    print("- Backtesting trading strategies")
    print("- Data export for other analysis tools")
    print("- Historical price research")


if __name__ == "__main__":
    main()
