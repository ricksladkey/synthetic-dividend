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

from src.data.fetcher import HistoryFetcher
from src.models.backtest import run_portfolio_backtest  # noqa: E402


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
    ticker: str,
    start_date: date,
    end_date: date,
    algo_name: str,
    initial_qty: int = 10000,
    reference_rate_ticker: str = "",
    risk_free_rate_ticker: str = "",
) -> Dict[str, Any]:
    """Run single backtest and extract key metrics.

    Args:
        ticker: Stock symbol
        start_date: Backtest start date
        end_date: Backtest end date
        algo_name: Algorithm identifier string (portfolio format)
        initial_qty: Initial share quantity
        reference_rate_ticker: Ticker symbol for reference asset
        risk_free_rate_ticker: Ticker symbol for risk-free asset

    Returns:
        Dict with extracted metrics for CSV row
    """
    try:
        # Convert single-ticker to portfolio format
        allocations = {ticker: 1.0}
        
        # Convert algorithm name to portfolio format
        if algo_name == "buy-and-hold":
            portfolio_algo = "per-asset:buy-and-hold"
        elif algo_name.startswith("sd-"):
            portfolio_algo = f"per-asset:{algo_name}"
        else:
            portfolio_algo = algo_name
        
        # Calculate initial investment from initial_qty and start price
        # We'll need to fetch the start price first
        fetcher = HistoryFetcher()
        df = fetcher.get_history(ticker, start_date, end_date)
        if df is None or df.empty:
            raise ValueError(f"No price data available for {ticker}")
        
        # Get start price
        df_indexed = df.copy()
        df_indexed.index = df_indexed.index.date
        
        # Find the actual start date (first available date >= requested start_date)
        available_dates = sorted([d for d in df_indexed.index if d >= start_date])
        if not available_dates:
            raise ValueError(f"No data available for {ticker} starting from {start_date}")
        actual_start_date = available_dates[0]
        
        start_price = float(df_indexed.loc[actual_start_date, "Close"])
        initial_investment = initial_qty * start_price

        # Find the actual end date (last available date <= requested end_date)
        available_end_dates = sorted([d for d in df_indexed.index if d <= end_date])
        if not available_end_dates:
            raise ValueError(f"No data available for {ticker} ending at {end_date}")
        actual_end_date = available_end_dates[-1]
        
        transactions, summary = run_portfolio_backtest(
            allocations=allocations,
            start_date=actual_start_date,
            end_date=actual_end_date,
            portfolio_algo=portfolio_algo,
            initial_investment=initial_investment,
            reference_rate_ticker=reference_rate_ticker if reference_rate_ticker else None,
            risk_free_rate_ticker=risk_free_rate_ticker if risk_free_rate_ticker else None,
        )

        # Extract key metrics from portfolio summary
        asset_results = summary["assets"][ticker]
        
        return {
            "algorithm": algo_name,
            "start_date": summary["start_date"].isoformat(),
            "end_date": summary["end_date"].isoformat(),
            "start_price": start_price,
            "end_price": float(df_indexed.loc[actual_end_date, "Close"]),
            "initial_qty": initial_qty,
            "final_shares": asset_results["final_holdings"],
            "final_value": asset_results["final_value"],
            "bank": summary.get("final_bank", 0.0),
            "bank_min": min(summary.get("daily_bank_values", {}).values()) if summary.get("daily_bank_values") else summary.get("final_bank", 0.0),
            "bank_max": max(summary.get("daily_bank_values", {}).values()) if summary.get("daily_bank_values") else summary.get("final_bank", 0.0),
            "bank_avg": sum(summary.get("daily_bank_values", {}).values()) / len(summary.get("daily_bank_values", {})) if summary.get("daily_bank_values") else summary.get("final_bank", 0.0),
            "bank_negative_count": sum(1 for b in summary.get("daily_bank_values", {}).values() if b < 0),
            "bank_positive_count": sum(1 for b in summary.get("daily_bank_values", {}).values() if b > 0),
            "opportunity_cost": summary.get("opportunity_cost", 0.0),
            "risk_free_gains": summary.get("cash_interest_earned", 0.0),
            "total": summary.get("total_final_value", asset_results["final_value"]),
            "total_return_pct": summary["total_return"],
            "annualized_return_pct": summary["annualized_return"],
            "years": summary["trading_days"] / 365.25,
            "num_transactions": summary.get("transaction_count", len(transactions)),
            "start_value": initial_investment,
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

    # Generate full SD configurations (modern comma-based format)
    for rebal in rebalance_pcts:
        for profit in profit_pcts:
            configs.append(f"sd-{rebal},{profit}")

    # Generate ATH-only SD configurations (subset of most interesting params)
    ath_rebalance = [9.05, 9.15, 10.0, 15.0]
    ath_profit = [50.0, 75.0, 100.0]

    for rebal in ath_rebalance:
        for profit in ath_profit:
            configs.append(f"sd-ath-only-{rebal},{profit}")

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
    # Use default configs if not provided
    if configs is None:
        configs = generate_algorithm_configs()

    print(f"\nRunning {len(configs)} configurations...\n")

    results: List[Dict[str, Any]] = []

    # Run each configuration
    for i, algo_name in enumerate(configs, 1):
        print(f"[{i}/{len(configs)}] {algo_name}...", end=" ", flush=True)

        result = run_single_backtest(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            algo_name=algo_name,
            initial_qty=initial_qty,
            reference_rate_ticker=reference_asset,
            risk_free_rate_ticker=risk_free_asset,
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


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point.

    Returns:
        Exit code (0 = success)
    """
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) < 3:
        print("Usage: python -m src.compare.batch_comparison TICKER START END [OUTPUT.csv]")
        print(
            "Example: python -m src.compare.batch_comparison NVDA 2024-10-22 2025-10-22 results.csv"
        )
        return 2

    ticker = argv[0].upper()
    start = parse_date(argv[1])
    end = parse_date(argv[2])
    output_path = argv[3] if len(argv) > 3 else f"{ticker}_comparison.csv"

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
