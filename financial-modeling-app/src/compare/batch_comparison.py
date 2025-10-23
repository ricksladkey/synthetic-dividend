"""Batch comparison tool for multiple algorithm configurations.

Generates CSV output comparing buy-and-hold vs various synthetic dividend
configurations across different rebalance and profit-sharing parameters.

Output is Excel/Google Sheets importable with one row per configuration.

Usage:
    python -m src.compare.batch_comparison TICKER START END [OUTPUT.csv]

Example:
    python -m src.compare.batch_comparison NVDA 2024-10-22 2025-10-22 results.csv
"""

import csv
import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from src.data.fetcher import HistoryFetcher
from src.models.backtest import build_algo_from_name, run_algorithm_backtest


def parse_date(s: str) -> date:
    """Parse date from MM/DD/YYYY or YYYY-MM-DD format.

    Args:
        s: Date string

    Returns:
        date object

    Raises:
        ValueError: If format not recognized
    """
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    raise ValueError(f"Unrecognized date format: {s}")


def run_single_backtest(
    df: pd.DataFrame,
    ticker: str,
    start_date: date,
    end_date: date,
    algo_name: str,
    initial_qty: int = 10000,
    reference_return_pct: float = 0.0,
    risk_free_rate_pct: float = 0.0,
    reference_asset_df: pd.DataFrame = None,
    risk_free_asset_df: pd.DataFrame = None,
    reference_asset_ticker: str = "",
    risk_free_asset_ticker: str = "",
) -> Dict[str, Any]:
    """Run single backtest and extract key metrics.

    Args:
        df: Historical OHLC price data
        ticker: Stock symbol
        start_date: Backtest start date
        end_date: Backtest end date
        algo_name: Algorithm identifier string
        initial_qty: Initial share quantity
        reference_return_pct: Annual reference return for opportunity cost (fallback, default 0%)
        risk_free_rate_pct: Annual risk-free rate for cash (fallback, default 0%)
        reference_asset_df: Historical data for reference asset (e.g., VOO)
        risk_free_asset_df: Historical data for risk-free asset (e.g., BIL)
        reference_asset_ticker: Ticker symbol for reference asset
        risk_free_asset_ticker: Ticker symbol for risk-free asset

    Returns:
        Dict with extracted metrics for CSV row
    """
    try:
        algo = build_algo_from_name(algo_name)
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=ticker,
            initial_qty=initial_qty,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
            reference_return_pct=reference_return_pct,
            risk_free_rate_pct=risk_free_rate_pct,
            reference_asset_df=reference_asset_df,
            risk_free_asset_df=risk_free_asset_df,
            reference_asset_ticker=reference_asset_ticker,
            risk_free_asset_ticker=risk_free_asset_ticker,
        )

        # Extract key metrics including new bank statistics
        return {
            "algorithm": algo_name,
            "start_date": summary["start_date"].isoformat(),
            "end_date": summary["end_date"].isoformat(),
            "start_price": summary["start_price"],
            "end_price": summary["end_price"],
            "initial_qty": initial_qty,
            "final_shares": summary["holdings"],
            "final_value": summary["end_value"],
            "bank": summary.get("bank", 0.0),
            "bank_min": summary.get("bank_min", 0.0),
            "bank_max": summary.get("bank_max", 0.0),
            "bank_avg": summary.get("bank_avg", 0.0),
            "bank_negative_count": summary.get("bank_negative_count", 0),
            "bank_positive_count": summary.get("bank_positive_count", 0),
            "opportunity_cost": summary.get("opportunity_cost", 0.0),
            "risk_free_gains": summary.get("risk_free_gains", 0.0),
            "total": summary.get("total", summary["end_value"]),
            "total_return_pct": summary["total_return"] * 100,
            "annualized_return_pct": summary["annualized"] * 100,
            "years": summary["years"],
            "num_transactions": len(transactions),
            "start_value": summary["start_value"],
        }
    except Exception as e:
        # Return error row if backtest fails
        return {
            "algorithm": algo_name,
            "error": str(e),
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        }


def generate_algorithm_configs() -> List[str]:
    """Generate list of algorithm configurations to test.

    Returns:
        List of algorithm identifier strings
    """
    configs: List[str] = []

    # Baseline: buy-and-hold
    configs.append("buy-and-hold")

    # Rebalance percentages to test
    rebalance_pcts = [5.0, 7.5, 9.05, 9.15, 10.0, 12.5, 15.0, 20.0, 25.0]

    # Profit sharing percentages to test
    profit_pcts = [25.0, 33.33, 50.0, 66.67, 75.0, 100.0]

    # Generate full SD configurations
    for rebal in rebalance_pcts:
        for profit in profit_pcts:
            configs.append(f"sd/{rebal}%/{profit}%")

    # Generate ATH-only SD configurations (subset of most interesting params)
    ath_rebalance = [9.05, 9.15, 10.0, 15.0]
    ath_profit = [50.0, 75.0, 100.0]

    for rebal in ath_rebalance:
        for profit in ath_profit:
            configs.append(f"sd-ath-only/{rebal}%/{profit}%")

    return configs


def run_batch_comparison(
    ticker: str,
    start_date: date,
    end_date: date,
    initial_qty: int = 10000,
    configs: Optional[List[str]] = None,
    reference_asset: str = "VOO",
    risk_free_asset: str = "BIL",
) -> List[Dict[str, Any]]:
    """Run backtest for all configurations and return results.

    Args:
        ticker: Stock symbol
        start_date: Backtest start date
        end_date: Backtest end date
        initial_qty: Initial share quantity
        configs: List of algorithm configs (None = use defaults)
        reference_asset: Ticker for reference asset (default: VOO for S&P 500)
        risk_free_asset: Ticker for risk-free asset (default: BIL for T-bills)

    Returns:
        List of result dicts, one per configuration
    """
    # Fetch price data once (uses cache)
    print(f"Fetching price data for {ticker}...")
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        raise ValueError(f"No price data available for {ticker}")

    print(f"Data loaded: {len(df)} trading days")

    # Fetch reference and risk-free asset data
    print(f"Fetching {reference_asset} (reference asset)...", end=" ", flush=True)
    reference_df = None
    try:
        reference_df = fetcher.get_history(reference_asset, start_date, end_date)
        if reference_df.empty:
            print("Warning: No data, using fallback rate")
            reference_df = None
        else:
            print(f"OK {len(reference_df)} days")
    except Exception as e:
        print(f"Warning: {e}, using fallback rate")

    print(f"Fetching {risk_free_asset} (risk-free asset)...", end=" ", flush=True)
    risk_free_df = None
    try:
        risk_free_df = fetcher.get_history(risk_free_asset, start_date, end_date)
        if risk_free_df.empty:
            print("Warning: No data, using fallback rate")
            risk_free_df = None
        else:
            print(f"OK {len(risk_free_df)} days")
    except Exception as e:
        print(f"Warning: {e}, using fallback rate")

    # Use default configs if not provided
    if configs is None:
        configs = generate_algorithm_configs()

    print(f"\nRunning {len(configs)} configurations...\n")

    results: List[Dict[str, Any]] = []

    # Run each configuration
    for i, algo_name in enumerate(configs, 1):
        print(f"[{i}/{len(configs)}] {algo_name}...", end=" ", flush=True)

        result = run_single_backtest(
            df=df,
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            algo_name=algo_name,
            initial_qty=initial_qty,
            reference_asset_df=reference_df,
            risk_free_asset_df=risk_free_df,
            reference_asset_ticker=reference_asset,
            risk_free_asset_ticker=risk_free_asset,
        )

        # Add ticker for reference
        result["ticker"] = ticker
        results.append(result)

        # Print completion status
        if "error" in result:
            print(f"ERROR: {result['error']}")
        else:
            print(f"OK Return: {result['total_return_pct']:.2f}%")

    return results


def calculate_deltas(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Calculate differences from buy-and-hold baseline.

    Args:
        results: List of backtest results

    Returns:
        Updated results with delta columns added
    """
    # Find buy-and-hold baseline
    baseline = None
    for r in results:
        if r.get("algorithm") == "buy-and-hold":
            baseline = r
            break

    if baseline is None:
        return results

    # Add delta columns to each result
    for r in results:
        if "error" not in r:
            r["vs_bah_return_pct"] = r["total_return_pct"] - baseline["total_return_pct"]
            r["vs_bah_total"] = r["total"] - baseline["total"]
            r["vs_bah_shares"] = r["final_shares"] - baseline["final_shares"]
        else:
            r["vs_bah_return_pct"] = None
            r["vs_bah_total"] = None
            r["vs_bah_shares"] = None

    return results


def write_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Write results to CSV file.

    Args:
        results: List of backtest results
        output_path: Path to output CSV file
    """
    if not results:
        print("No results to write")
        return

    # Define column order for readability
    columns = [
        "ticker",
        "algorithm",
        "start_date",
        "end_date",
        "years",
        "initial_qty",
        "start_price",
        "end_price",
        "start_value",
        "final_shares",
        "final_value",
        "bank",
        "bank_min",
        "bank_max",
        "bank_avg",
        "bank_negative_count",
        "bank_positive_count",
        "opportunity_cost",
        "risk_free_gains",
        "total",
        "total_return_pct",
        "annualized_return_pct",
        "vs_bah_return_pct",
        "vs_bah_total",
        "vs_bah_shares",
        "num_transactions",
        "error",
    ]

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()

        for result in results:
            # Fill missing columns with None
            row = {col: result.get(col) for col in columns}
            writer.writerow(row)

    print(f"\nOK Results written to: {output_path}")


def print_summary(results: List[Dict[str, Any]]) -> None:
    """Print summary statistics to console.

    Args:
        results: List of backtest results
    """
    if not results:
        return

    # Filter out errors
    valid_results = [r for r in results if "error" not in r]

    if not valid_results:
        print("\nNo valid results to summarize")
        return

    # Find best/worst performers
    sorted_by_return = sorted(valid_results, key=lambda x: x["total_return_pct"], reverse=True)

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(f"\nTotal configurations tested: {len(results)}")
    print(f"Successful: {len(valid_results)}")
    print(f"Errors: {len(results) - len(valid_results)}")

    print("\nTOP 5 PERFORMERS (by total return):")
    print("-" * 80)
    for i, r in enumerate(sorted_by_return[:5], 1):
        print(
            f"{i}. {r['algorithm']:40s} {r['total_return_pct']:8.2f}% "
            f"(vs BAH: {r['vs_bah_return_pct']:+6.2f}%)"
        )

    print("\nBOTTOM 5 PERFORMERS (by total return):")
    print("-" * 80)
    for i, r in enumerate(sorted_by_return[-5:], 1):
        print(
            f"{i}. {r['algorithm']:40s} {r['total_return_pct']:8.2f}% "
            f"(vs BAH: {r['vs_bah_return_pct']:+6.2f}%)"
        )

    # Transaction count analysis
    sorted_by_tx = sorted(valid_results, key=lambda x: x["num_transactions"])

    print("\nTRANSACTION COUNTS:")
    print("-" * 80)
    print(
        f"Minimum: {sorted_by_tx[0]['num_transactions']} transactions ({sorted_by_tx[0]['algorithm']})"
    )
    print(
        f"Maximum: {sorted_by_tx[-1]['num_transactions']} transactions ({sorted_by_tx[-1]['algorithm']})"
    )

    avg_tx = sum(r["num_transactions"] for r in valid_results) / len(valid_results)
    print(f"Average: {avg_tx:.1f} transactions")


def main() -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success)
    """
    if len(sys.argv) < 4:
        print("Usage: python -m src.compare.batch_comparison TICKER START END [OUTPUT.csv]")
        print(
            "Example: python -m src.compare.batch_comparison NVDA 2024-10-22 2025-10-22 results.csv"
        )
        return 2

    ticker = sys.argv[1].upper()
    start = parse_date(sys.argv[2])
    end = parse_date(sys.argv[3])
    output_path = sys.argv[4] if len(sys.argv) > 4 else f"{ticker}_comparison.csv"

    print("=" * 80)
    print(f"BATCH COMPARISON: {ticker}")
    print(f"Period: {start} to {end}")
    print(f"Output: {output_path}")
    print("=" * 80 + "\n")

    # Run all configurations
    results = run_batch_comparison(ticker, start, end)

    # Calculate deltas from baseline
    results = calculate_deltas(results)

    # Write CSV output
    write_csv(results, output_path)

    # Print summary
    print_summary(results)

    print(f"\n✓ Complete. Import {output_path} into Excel/Sheets for analysis.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
