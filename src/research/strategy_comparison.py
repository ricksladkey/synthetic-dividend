#!/usr/bin/env python3
"""Comprehensive rebalancing strategy comparison for portfolio planning.

Compares three key strategies to quantify volatility alpha and cash flow patterns:
1. Buy-and-Hold: Passive baseline
2. SD8-ATH-Only: Only sells at new all-time highs (LTCG only)
3. SD8 Full: Embraces volatility with buybacks (LTCG + STCG mix)

Outputs:
- Annualized returns by strategy
- Volatility alpha (extra return from rebalancing)
- Yearly cash flow analysis
- Transaction frequency and tax implications
- Capital deployment statistics

This comparison provides the quantified metrics needed for 10-year portfolio planning.

Usage:
    python -m src.research.strategy_comparison TICKER START END [--output CSVFILE]
    python -m src.research.strategy_comparison NVDA 2020-01-01 2025-01-01
    python -m src.research.strategy_comparison SPY 2020-01-01 2025-01-01 --output spy_results.csv
"""

import argparse
import csv
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.algorithms.factory import build_algo_from_name  # noqa: E402
from src.data.fetcher import HistoryFetcher  # noqa: E402
from src.models.backtest import run_algorithm_backtest  # noqa: E402


def parse_date(s: str) -> date:
    """Parse date string in MM/DD/YYYY or YYYY-MM-DD format."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(s, fmt).date()
        except Exception:
            pass
    raise ValueError(f"Unrecognized date format: {s}")


def calculate_yearly_cash_flow(
    transactions: List[str], start_date: date, end_date: date
) -> Dict[int, float]:
    """Calculate net cash flow by year from transaction history.

    Args:
        transactions: List of transaction strings
        start_date: Backtest start date
        end_date: Backtest end date

    Returns:
        Dict mapping year to net cash flow (positive = received cash, negative = paid cash)

    Note: Excludes the initial BUY transaction to focus on ongoing cash generation
    """
    yearly_cash: Dict[int, float] = {}

    # Initialize all years in range
    for year in range(start_date.year, end_date.year + 1):
        yearly_cash[year] = 0.0

    # Skip first transaction (initial BUY)
    for tx in transactions[1:] if len(transactions) > 1 else []:
        # Parse transaction format: "2024-01-15 SELL 100 NVDA @ 500.00 = 50000.00, holdings = 9900, bank = 50000.00  # Notes"
        try:
            parts = tx.split()
            if len(parts) < 7:
                continue

            tx_date_str = parts[0]
            action = parts[1]
            # qty_str = parts[2]  # Not used for cash flow
            # ticker = parts[3]  # Not used
            # at_sym = parts[4]  # '@'
            # price_str = parts[5]  # Not used for cash flow
            # eq_sym = parts[6]  # '='
            value_str = parts[7].rstrip(",")

            tx_date = datetime.fromisoformat(tx_date_str).date()
            value = float(value_str)

            year = tx_date.year
            if year not in yearly_cash:
                yearly_cash[year] = 0.0

            if action == "SELL":
                # Received cash
                yearly_cash[year] += value
            elif action == "BUY":
                # Paid cash
                yearly_cash[year] -= value

        except Exception:
            # Skip malformed transactions
            continue

    return yearly_cash


def analyze_cash_flow_patterns(yearly_cash: Dict[int, float]) -> Dict[str, Any]:
    """Analyze cash flow patterns for withdrawal feasibility.

    Args:
        yearly_cash: Dict mapping year to net cash flow

    Returns:
        Dict with cash flow statistics
    """
    if not yearly_cash:
        return {
            "positive_years": 0,
            "negative_years": 0,
            "total_years": 0,
            "avg_yearly_cash": 0.0,
            "min_yearly_cash": 0.0,
            "max_yearly_cash": 0.0,
            "positive_cash_ratio": 0.0,
        }

    cash_values = list(yearly_cash.values())
    positive_years = sum(1 for v in cash_values if v > 0)
    negative_years = sum(1 for v in cash_values if v < 0)
    total_years = len(cash_values)

    return {
        "positive_years": positive_years,
        "negative_years": negative_years,
        "total_years": total_years,
        "avg_yearly_cash": sum(cash_values) / total_years if total_years > 0 else 0.0,
        "min_yearly_cash": min(cash_values) if cash_values else 0.0,
        "max_yearly_cash": max(cash_values) if cash_values else 0.0,
        "positive_cash_ratio": positive_years / total_years if total_years > 0 else 0.0,
    }


def run_strategy_backtest(
    ticker: str,
    start_date: date,
    end_date: date,
    strategy_name: str,
    initial_qty: int = 10000,
) -> Dict[str, Any]:
    """Run backtest for a single strategy and extract comprehensive metrics.

    Args:
        ticker: Stock symbol
        start_date: Backtest start date
        end_date: Backtest end date
        strategy_name: Strategy identifier (buy-and-hold, sd8, sd8-ath-only)
        initial_qty: Initial share quantity

    Returns:
        Dict with comprehensive backtest results and analysis
    """
    print(f"\n{'='*80}")
    print(f"Running strategy: {strategy_name}")
    print(f"{'='*80}")

    # Fetch data
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        return {
            "strategy": strategy_name,
            "error": "No data available",
        }

    # Build algorithm
    try:
        algo = build_algo_from_name(strategy_name)
    except Exception as e:
        return {
            "strategy": strategy_name,
            "error": f"Failed to build algorithm: {e}",
        }

    # Run backtest
    try:
        transactions, summary = run_algorithm_backtest(
            df=df,
            ticker=ticker,
            initial_qty=initial_qty,
            start_date=start_date,
            end_date=end_date,
            algo=algo,
        )
    except Exception as e:
        return {
            "strategy": strategy_name,
            "error": f"Backtest failed: {e}",
        }

    # Calculate yearly cash flow
    transaction_strings = [tx.to_string() for tx in transactions]
    yearly_cash = calculate_yearly_cash_flow(transaction_strings, start_date, end_date)
    cash_flow_stats = analyze_cash_flow_patterns(yearly_cash)

    # Extract metrics
    result = {
        "strategy": strategy_name,
        "ticker": ticker,
        "start_date": summary["start_date"].isoformat(),
        "end_date": summary["end_date"].isoformat(),
        "years": summary["years"],
        # Price metrics
        "start_price": summary["start_price"],
        "end_price": summary["end_price"],
        "price_change_pct": (
            ((summary["end_price"] - summary["start_price"]) / summary["start_price"] * 100)
            if summary["start_price"] > 0
            else 0.0
        ),
        # Portfolio metrics
        "initial_qty": initial_qty,
        "final_shares": summary["holdings"],
        "final_value": summary["end_value"],
        "bank": summary.get("bank", 0.0),
        "total": summary.get("total", summary["end_value"]),
        # Return metrics
        "total_return_pct": summary["total_return"] * 100,
        "annualized_return_pct": summary["annualized"] * 100,
        "volatility_alpha_pct": summary.get("volatility_alpha", 0.0) * 100,
        # Transaction metrics
        "num_transactions": len(transactions) - 1,  # Exclude initial BUY
        "transactions_per_year": (
            (len(transactions) - 1) / summary["years"] if summary["years"] > 0 else 0.0
        ),
        # Bank balance metrics
        "bank_min": summary.get("bank_min", 0.0),
        "bank_max": summary.get("bank_max", 0.0),
        "bank_avg": summary.get("bank_avg", 0.0),
        "bank_negative_count": summary.get("bank_negative_count", 0),
        "bank_positive_count": summary.get("bank_positive_count", 0),
        # Capital deployment metrics
        "capital_utilization": summary.get("capital_utilization", 0.0),
        "deployment_min_pct": summary.get("deployment_min_pct", 0.0) * 100,
        "deployment_max_pct": summary.get("deployment_max_pct", 0.0) * 100,
        # Cash flow metrics
        "positive_cash_years": cash_flow_stats["positive_years"],
        "negative_cash_years": cash_flow_stats["negative_years"],
        "avg_yearly_cash": cash_flow_stats["avg_yearly_cash"],
        "min_yearly_cash": cash_flow_stats["min_yearly_cash"],
        "max_yearly_cash": cash_flow_stats["max_yearly_cash"],
        "positive_cash_ratio": cash_flow_stats["positive_cash_ratio"],
        # Yearly cash flow breakdown
        "yearly_cash_flow": yearly_cash,
    }

    # Print summary
    print("\nResults:")
    print(f"  Total Return: {result['total_return_pct']:.2f}%")
    print(f"  Annualized: {result['annualized_return_pct']:.2f}%")
    print(f"  Volatility Alpha: {result['volatility_alpha_pct']:.2f}%")
    print(
        f"  Transactions: {result['num_transactions']} ({result['transactions_per_year']:.1f}/year)"
    )
    print(f"  Final Value: ${result['total']:,.2f}")
    print(f"  Bank Balance: ${result['bank']:,.2f}")
    print("\nCash Flow Analysis:")
    print(
        f"  Positive Cash Years: {result['positive_cash_years']} / {cash_flow_stats['total_years']}"
    )
    print(f"  Average Yearly Cash: ${result['avg_yearly_cash']:,.2f}")
    print(f"  Range: ${result['min_yearly_cash']:,.2f} to ${result['max_yearly_cash']:,.2f}")

    return result


def run_comparison(
    ticker: str,
    start_date: date,
    end_date: date,
    initial_qty: int = 10000,
) -> List[Dict[str, Any]]:
    """Run comprehensive comparison of all three strategies.

    Args:
        ticker: Stock symbol
        start_date: Backtest start date
        end_date: Backtest end date
        initial_qty: Initial share quantity

    Returns:
        List of results dicts, one per strategy
    """
    strategies = [
        ("buy-and-hold", "Buy and Hold (Baseline)"),
        ("sd8", "SD8 Full (Buybacks Enabled)"),
        ("sd-ath-only-9.15,50", "SD8 ATH-Only (LTCG Only)"),
    ]

    results = []

    for strategy_id, strategy_display in strategies:
        print(f"\n{'#'*80}")
        print(f"# {strategy_display}")
        print(f"{'#'*80}")

        result = run_strategy_backtest(
            ticker=ticker,
            start_date=start_date,
            end_date=end_date,
            strategy_name=strategy_id,
            initial_qty=initial_qty,
        )

        result["strategy_display"] = strategy_display
        results.append(result)

    return results


def save_results_to_csv(results: List[Dict[str, Any]], output_path: str) -> None:
    """Save comparison results to CSV file.

    Args:
        results: List of result dicts
        output_path: Path to output CSV file
    """
    if not results:
        print("No results to save")
        return

    # Define columns (excluding yearly_cash_flow which is a dict)
    columns = [
        "strategy",
        "strategy_display",
        "ticker",
        "start_date",
        "end_date",
        "years",
        "start_price",
        "end_price",
        "price_change_pct",
        "initial_qty",
        "final_shares",
        "final_value",
        "bank",
        "total",
        "total_return_pct",
        "annualized_return_pct",
        "volatility_alpha_pct",
        "num_transactions",
        "transactions_per_year",
        "bank_min",
        "bank_max",
        "bank_avg",
        "bank_negative_count",
        "bank_positive_count",
        "capital_utilization",
        "deployment_min_pct",
        "deployment_max_pct",
        "positive_cash_years",
        "negative_cash_years",
        "avg_yearly_cash",
        "min_yearly_cash",
        "max_yearly_cash",
        "positive_cash_ratio",
    ]

    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(results)

    print(f"\n{'='*80}")
    print(f"Results saved to: {output_path}")
    print(f"{'='*80}")


def calculate_withdrawal_impact(
    results: List[Dict[str, Any]], annual_withdrawal: float = 50000.0
) -> List[Dict[str, Any]]:
    """Calculate impact of annual withdrawals on each strategy.

    For buy-and-hold: Must sell shares to fund withdrawals
    For SD8: Uses generated cash flow, only sells if insufficient cash

    Args:
        results: List of result dicts
        annual_withdrawal: Annual withdrawal amount in dollars

    Returns:
        Updated results with withdrawal impact analysis
    """
    for r in results:
        if "error" in r:
            continue

        years = r["years"]
        yearly_cash = r.get("yearly_cash_flow", {})

        # Calculate total cash generated
        total_cash_generated = sum(yearly_cash.values())

        # Calculate withdrawal needs
        total_withdrawals_needed = annual_withdrawal * years

        # For strategies that generate cash, check if it covers withdrawals
        cash_surplus_deficit = total_cash_generated - total_withdrawals_needed

        r["annual_withdrawal"] = annual_withdrawal
        r["total_withdrawals_needed"] = total_withdrawals_needed
        r["total_cash_generated"] = total_cash_generated
        r["cash_surplus_deficit"] = cash_surplus_deficit
        r["withdrawal_coverage_pct"] = (
            (total_cash_generated / total_withdrawals_needed * 100)
            if total_withdrawals_needed > 0
            else 0.0
        )

    return results


def print_comparison_summary(results: List[Dict[str, Any]]) -> None:
    """Print formatted comparison summary.

    Args:
        results: List of result dicts
    """
    if not results:
        print("No results to summarize")
        return

    print(f"\n{'='*80}")
    print("STRATEGY COMPARISON SUMMARY")
    print(f"{'='*80}\n")

    # Find baseline (buy-and-hold)
    baseline = next((r for r in results if "buy-and-hold" in r.get("strategy", "")), None)

    # Print basic comparison table
    print(
        f"{'Strategy':<30} {'Ann. Return':<12} {'Txns/Yr':<10} {'Final Value':<15} {'Final Shares':<12}"
    )
    print(f"{'-'*30} {'-'*12} {'-'*10} {'-'*15} {'-'*12}")

    for r in results:
        if "error" in r:
            print(f"{r.get('strategy_display', r['strategy']):<30} ERROR: {r['error']}")
            continue

        strategy = r.get("strategy_display", r["strategy"])
        ann_return = f"{r['annualized_return_pct']:.2f}%"
        txns_per_year = f"{r['transactions_per_year']:.1f}"
        final_value = f"${r['total']:,.0f}"
        final_shares = f"{r['final_shares']:,}"

        print(
            f"{strategy:<30} {ann_return:<12} {txns_per_year:<10} {final_value:<15} {final_shares:<12}"
        )

    print()

    # Cash flow analysis
    print(f"\n{'='*80}")
    print("CASH FLOW ANALYSIS (For Withdrawal Planning)")
    print(f"{'='*80}\n")

    print(f"{'Strategy':<30} {'Avg Yearly':<15} {'Total Generated':<18} {'Positive Years':<15}")
    print(f"{'-'*30} {'-'*15} {'-'*18} {'-'*15}")

    for r in results:
        if "error" in r:
            continue

        strategy = r.get("strategy_display", r["strategy"])
        avg_yearly = f"${r['avg_yearly_cash']:,.0f}"
        total_generated = f"${r.get('total_cash_generated', 0.0):,.0f}"
        positive_years = (
            f"{r['positive_cash_years']}/{r['positive_cash_years'] + r['negative_cash_years']}"
        )

        print(f"{strategy:<30} {avg_yearly:<15} {total_generated:<18} {positive_years:<15}")

    print()

    # Withdrawal sustainability analysis
    print(f"\n{'='*80}")
    print("WITHDRAWAL SUSTAINABILITY (Assuming $50K/year expenses)")
    print(f"{'='*80}\n")

    print(
        f"{'Strategy':<30} {'Cash Generated':<18} {'Needed':<15} {'Coverage':<12} {'Surplus/Deficit':<18}"
    )
    print(f"{'-'*30} {'-'*18} {'-'*15} {'-'*12} {'-'*18}")

    for r in results:
        if "error" in r:
            continue

        strategy = r.get("strategy_display", r["strategy"])
        cash_gen = f"${r.get('total_cash_generated', 0.0):,.0f}"
        needed = f"${r.get('total_withdrawals_needed', 0.0):,.0f}"
        coverage = f"{r.get('withdrawal_coverage_pct', 0.0):.1f}%"
        surplus = r.get("cash_surplus_deficit", 0.0)
        surplus_str = f"${surplus:,.0f}" if surplus >= 0 else f"-${abs(surplus):,.0f}"

        print(f"{strategy:<30} {cash_gen:<18} {needed:<15} {coverage:<12} {surplus_str:<18}")

    print()

    # Key insights
    print(f"\n{'='*80}")
    print("KEY INSIGHTS FOR PORTFOLIO PLANNING")
    print(f"{'='*80}\n")

    if baseline:
        sd8_full = next((r for r in results if r.get("strategy") == "sd8"), None)
        sd8_ath = next((r for r in results if "ath-only" in r.get("strategy", "")), None)

        print("1. BUY-AND-HOLD REALITY CHECK:")
        print(f"   - Final value: ${baseline['total']:,.0f}")
        print(f"   - Cash generated: ${baseline.get('total_cash_generated', 0.0):,.0f}")
        print("   - To fund expenses, you MUST sell shares")
        print("   - This reduces your final position and compounds negatively")
        print()

        if sd8_full and "error" not in sd8_full:
            print("2. SD8 FULL (Buyback Strategy):")
            print(f"   - Final value: ${sd8_full['total']:,.0f}")
            print(f"   - Cash generated: ${sd8_full.get('total_cash_generated', 0.0):,.0f}")
            coverage = sd8_full.get("withdrawal_coverage_pct", 0.0)
            if coverage >= 100:
                print(f"   ✓ FULLY COVERS withdrawals ({coverage:.0f}%)")
                print("   ✓ No forced selling required!")
            else:
                print(f"   - Covers {coverage:.0f}% of withdrawals")
                print("   - Some share sales needed for shortfall")
            print(f"   - Annualized return: {sd8_full['annualized_return_pct']:.2f}%")
            print(
                f"   - Transactions: {sd8_full['transactions_per_year']:.1f}/year (mix LTCG/STCG)"
            )
            print()

        if sd8_ath and "error" not in sd8_ath:
            print("3. SD8 ATH-ONLY (Long-term Capital Gains Only):")
            print(f"   - Final value: ${sd8_ath['total']:,.0f}")
            print(f"   - Cash generated: ${sd8_ath.get('total_cash_generated', 0.0):,.0f}")
            coverage = sd8_ath.get("withdrawal_coverage_pct", 0.0)
            if coverage >= 100:
                print(f"   ✓ FULLY COVERS withdrawals ({coverage:.0f}%)")
                print("   ✓ No forced selling required!")
            else:
                print(f"   - Covers {coverage:.0f}% of withdrawals")
                print("   - Some share sales needed for shortfall")
            print(f"   - Annualized return: {sd8_ath['annualized_return_pct']:.2f}%")
            print(f"   - Transactions: {sd8_ath['transactions_per_year']:.1f}/year (all LTCG)")
            print("   - Tax advantage: Better suited for taxable accounts")
            print()

        if sd8_full and sd8_ath and "error" not in sd8_full and "error" not in sd8_ath:
            buyback_premium = sd8_full["annualized_return_pct"] - sd8_ath["annualized_return_pct"]
            print("4. BUYBACK PREMIUM (SD8 Full vs ATH-Only):")
            print(f"   - Extra annualized return: {buyback_premium:.2f}%")
            print("   - This is from embracing downside volatility")
            print("   - Best utilized in tax-advantaged accounts (401k, IRA)")
            print()

        print("5. THE BOTTOM LINE:")
        print("   - In strong bull markets, buy-and-hold has highest UNREALIZED gains")
        print("   - But you cannot spend unrealized gains!")
        print("   - SD8 strategies sacrifice some upside to generate SPENDABLE cash")
        print("   - The real comparison: sustainable income vs. forced share sales")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Comprehensive strategy comparison for portfolio planning"
    )
    parser.add_argument("ticker", help="Stock ticker symbol")
    parser.add_argument("start", help="Start date (YYYY-MM-DD or MM/DD/YYYY)")
    parser.add_argument("end", help="End date (YYYY-MM-DD or MM/DD/YYYY)")
    parser.add_argument(
        "--output",
        default="output/strategy_comparison.csv",
        help="Output CSV file path (default: output/strategy_comparison.csv)",
    )
    parser.add_argument(
        "--qty",
        type=int,
        default=10000,
        help="Initial share quantity (default: 10000)",
    )

    args = parser.parse_args()

    # Parse dates
    try:
        start_date = parse_date(args.start)
        end_date = parse_date(args.end)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Run comparison
    results = run_comparison(
        ticker=args.ticker,
        start_date=start_date,
        end_date=end_date,
        initial_qty=args.qty,
    )

    # Calculate withdrawal impact
    results = calculate_withdrawal_impact(results, annual_withdrawal=50000.0)

    # Save results
    save_results_to_csv(results, args.output)

    # Print summary
    print_comparison_summary(results)


if __name__ == "__main__":
    main()
