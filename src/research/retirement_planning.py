"""Retirement Planning Research Experiment

Research Question:
    If the last 10 years were representative of the "new economy," how much can
    you sustainably withdraw from a volatility-harvesting portfolio?

Hypothesis:
    Volatility harvesting (SD8) enables higher sustainable withdrawal rates than
    buy-and-hold because mean reversion replenishes capital while you withdraw.

Test Design:
    - Portfolio: Single-asset or multi-asset allocation
    - Period: Last 10 years (or user-specified)
    - Strategies: Buy-Hold, ATH-Only, Full SD8
    - Withdrawal: 5% initial, adjusted monthly by CPI
    - Metrics: Portfolio survival, final value, total withdrawn, purchasing power

Assets to test:
    - Growth assets: NVDA, PLTR (exceed market consistently)
    - Volatile assets: BTC, ETH, MSTR (imminent 80% crash routinely predicted)
    - Market proxy: VOO (baseline reference return)

Special case: MSTR "unrealized volatility alpha"
    - Bought at $540 peak, now ~$270 (50% drawdown)
    - How much volatility alpha could SD8 have captured?
    - Test: Backtest from peak, measure vs buy-and-hold drawdown
"""

from datetime import date
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from src.algorithms.factory import build_algo_from_name
from src.data.fetcher import HistoryFetcher
from src.models.backtest import run_algorithm_backtest
from src.models.retirement_backtest import run_retirement_backtest

# Experiment parameters
INITIAL_INVESTMENT = 1_000_000  # $1M portfolio
ANNUAL_WITHDRAWAL_RATE = 0.05  # 5% per year
WITHDRAWAL_FREQUENCY = "monthly"  # Monthly withdrawals
CPI_ADJUST = True  # Adjust withdrawals for inflation

# Test period: Last 10 years
END_DATE = date(2024, 12, 31)
START_DATE = date(2020, 1, 1)  # 5-year backtest (faster for testing)

# Assets to test (reduced set for speed)
ASSETS = {"growth": ["NVDA"], "volatile": ["BTC-USD", "MSTR"], "baseline": ["VOO"]}

# Strategies to test
STRATEGIES = {
    "buy-hold": "buy-and-hold",
    "ath-only": "sd-ath-only-9.05,50.0",
    "full-sd8": "sd-9.05,50.0",
}

# Output directory
OUTPUT_DIR = Path("experiments/retirement_planning")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def run_single_asset_retirement_test(
    ticker: str,
    start_date: date,
    end_date: date,
    initial_investment: float,
    annual_withdrawal_rate: float,
) -> Dict[str, Dict[str, Any]]:
    """Test retirement sustainability for single asset across all strategies.

    Args:
        ticker: Asset symbol
        start_date: Start of retirement period
        end_date: End of retirement period
        initial_investment: Starting portfolio value
        annual_withdrawal_rate: Annual withdrawal as percentage of initial value

    Returns:
        Dict of {strategy_name: summary_dict}
    """
    # Fetch price data
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start_date, end_date)

    if df.empty:
        raise ValueError(f"No data available for {ticker}")

    # Calculate initial quantity
    first_price = df.iloc[0]["Close"].item()
    initial_qty = int(initial_investment / first_price)

    results = {}

    for strategy_name, algo_name in STRATEGIES.items():
        print(f"  Testing {strategy_name}...")

        # Build algorithm
        algo = build_algo_from_name(algo_name)

        # Run retirement backtest
        transactions, summary = run_retirement_backtest(
            df,
            ticker,
            initial_qty,
            start_date,
            end_date,
            algo,
            annual_withdrawal_rate=annual_withdrawal_rate,
            withdrawal_frequency=WITHDRAWAL_FREQUENCY,
            cpi_adjust=CPI_ADJUST,
            simple_mode=True,
        )

        results[strategy_name] = summary

        # Print quick summary
        survived = "OK" if summary["portfolio_survived"] else "FAIL"
        print(
            f"    {survived} Final: ${summary['final_value']:,.0f}, Withdrawn: ${summary['total_withdrawn']:,.0f}"
        )

    return results


def run_mstr_unrealized_alpha_analysis(
    peak_date: date, peak_price: float, end_date: date, initial_investment: float
) -> Dict[str, Any]:
    """Analyze unrealized volatility alpha for MSTR from peak.

    Scenario: You bought MSTR at $540 peak. How much volatility alpha could
    SD8 have captured compared to buy-and-hold during the drawdown?

    Args:
        peak_date: Date of ATH purchase
        peak_price: Price at ATH (e.g., $540)
        end_date: Current date
        initial_investment: Investment amount at peak

    Returns:
        Dict with analysis results
    """
    print(f"\n[MSTR UNREALIZED ALPHA ANALYSIS]")
    print(f"Scenario: Bought at peak ${peak_price} on {peak_date}")
    print(f"Analysis period: {peak_date} to {end_date}")

    # Fetch MSTR data from peak
    fetcher = HistoryFetcher()
    df = fetcher.get_history("MSTR", peak_date, end_date)

    # Calculate shares purchased at peak
    initial_qty = int(initial_investment / peak_price)

    # Test buy-and-hold (maximum pain)
    algo_bh = build_algo_from_name("buy-and-hold")
    _, summary_bh = run_algorithm_backtest(
        df, "MSTR", initial_qty, peak_date, end_date, algo_bh, simple_mode=True
    )

    # Test full SD8 (volatility harvesting during drawdown)
    algo_sd8 = build_algo_from_name("sd-9.05,50.0")
    _, summary_sd8 = run_algorithm_backtest(
        df, "MSTR", initial_qty, peak_date, end_date, algo_sd8, simple_mode=True
    )

    # Calculate unrealized alpha
    bh_final = summary_bh.get("end_value", summary_bh.get("total", initial_investment))
    sd8_final = summary_sd8.get("end_value", summary_sd8.get("total", initial_investment))

    bh_drawdown = (bh_final - initial_investment) / initial_investment
    sd8_drawdown = (sd8_final - initial_investment) / initial_investment
    unrealized_alpha = sd8_drawdown - bh_drawdown

    results = {
        "peak_date": peak_date,
        "peak_price": peak_price,
        "end_date": end_date,
        "initial_investment": initial_investment,
        "initial_qty": initial_qty,
        "buy_hold": {
            "final_value": bh_final,
            "drawdown_pct": bh_drawdown * 100,
            "total_return_pct": summary_bh.get("total_return", bh_drawdown * 100),
        },
        "full_sd8": {
            "final_value": sd8_final,
            "drawdown_pct": sd8_drawdown * 100,
            "total_return_pct": summary_sd8.get("total_return", sd8_drawdown * 100),
            "volatility_alpha_pct": summary_sd8.get("volatility_alpha_pct", 0),
        },
        "unrealized_alpha_pct": unrealized_alpha * 100,
        "alpha_value": sd8_final - bh_final,
    }

    # Print results
    print(f"\nBuy-and-Hold:")
    print(f"  Final Value: ${bh_final:,.0f}")
    print(f"  Drawdown: {bh_drawdown*100:.2f}%")

    print(f"\nFull SD8:")
    print(f"  Final Value: ${sd8_final:,.0f}")
    print(f"  Drawdown: {sd8_drawdown*100:.2f}%")

    print(f"\nUnrealized Volatility Alpha:")
    print(f"  Alpha: {unrealized_alpha*100:.2f}%")
    print(f"  Value: ${results['alpha_value']:,.0f}")
    print(
        f"  Interpretation: SD8 {'mitigated' if unrealized_alpha > 0 else 'worsened'} the drawdown by {abs(unrealized_alpha)*100:.2f}%"
    )

    return results


def run_retirement_experiment() -> Dict[str, Any]:
    """Run full retirement planning experiment.

    Tests all assets with all strategies to determine:
    1. Which assets sustain 5% withdrawals over 10 years
    2. How much volatility harvesting helps vs buy-and-hold
    3. Whether MSTR could have benefited from SD8 during drawdown

    Returns:
        Dict with complete results
    """
    print("=" * 80)
    print("RETIREMENT PLANNING EXPERIMENT")
    print("=" * 80)
    print(f"\nPeriod: {START_DATE} to {END_DATE}")
    print(f"Initial Investment: ${INITIAL_INVESTMENT:,.0f}")
    print(f"Annual Withdrawal: {ANNUAL_WITHDRAWAL_RATE*100}% ({WITHDRAWAL_FREQUENCY})")
    print(f"CPI Adjustment: {'Yes' if CPI_ADJUST else 'No'}")
    print("=" * 80)

    all_results = {}

    # Test each asset category
    for category, tickers in ASSETS.items():
        print(f"\n[{category.upper()} ASSETS]")

        for ticker in tickers:
            print(f"\n{ticker}:")

            try:
                results = run_single_asset_retirement_test(
                    ticker, START_DATE, END_DATE, INITIAL_INVESTMENT, ANNUAL_WITHDRAWAL_RATE
                )
                all_results[ticker] = results

            except Exception as e:
                print(f"  ERROR: {e}")
                all_results[ticker] = {"error": str(e)}

    # Special analysis: MSTR unrealized alpha from peak
    print("\n" + "=" * 80)
    mstr_results = run_mstr_unrealized_alpha_analysis(
        peak_date=date(2024, 11, 21),  # MSTR recent peak (adjust as needed)
        peak_price=540.0,
        end_date=END_DATE,
        initial_investment=INITIAL_INVESTMENT,
    )
    all_results["MSTR_unrealized_alpha"] = mstr_results

    return all_results


def save_results(results: Dict[str, Any], output_dir: Path):
    """Save experiment results to markdown and CSV.

    Args:
        results: Experiment results dict
        output_dir: Directory to save outputs
    """
    # Create summary markdown
    md_path = output_dir / "SUMMARY.md"

    with open(md_path, "w", encoding="utf-8") as f:
        f.write("# Retirement Planning Experiment Results\n\n")
        f.write(f"**Date**: {date.today()}\n")
        f.write(f"**Period**: {START_DATE} to {END_DATE}\n")
        f.write(f"**Initial Investment**: ${INITIAL_INVESTMENT:,.0f}\n")
        f.write(f"**Annual Withdrawal**: {ANNUAL_WITHDRAWAL_RATE*100}%\n")
        f.write(f"**Withdrawal Frequency**: {WITHDRAWAL_FREQUENCY}\n")
        f.write(f"**CPI Adjusted**: {CPI_ADJUST}\n\n")

        f.write("## Results by Asset\n\n")

        for ticker, data in results.items():
            if ticker == "MSTR_unrealized_alpha":
                continue

            if "error" in data:
                f.write(f"### {ticker}\n\n")
                f.write(f"**Error**: {data['error']}\n\n")
                continue

            f.write(f"### {ticker}\n\n")
            f.write(
                "| Strategy | Final Value | Total Withdrawn | Survived | Final Purchasing Power |\n"
            )
            f.write(
                "|----------|-------------|-----------------|----------|------------------------|\n"
            )

            for strategy_name in ["buy-hold", "ath-only", "full-sd8"]:
                if strategy_name not in data:
                    continue

                summary = data[strategy_name]
                survived = "OK" if summary.get("portfolio_survived", False) else "FAIL"

                f.write(f"| {strategy_name} | ")
                f.write(f"${summary.get('final_value', 0):,.0f} | ")
                f.write(f"${summary.get('total_withdrawn', 0):,.0f} | ")
                f.write(f"{survived} | ")
                f.write(f"${summary.get('final_purchasing_power', 0):,.0f} |\n")

            f.write("\n")

        # MSTR unrealized alpha section
        if "MSTR_unrealized_alpha" in results:
            mstr = results["MSTR_unrealized_alpha"]
            f.write("## MSTR Unrealized Volatility Alpha Analysis\n\n")
            f.write(
                f"**Scenario**: Purchased at peak ${mstr['peak_price']} on {mstr['peak_date']}\n\n"
            )
            f.write("| Metric | Buy-and-Hold | Full SD8 | Alpha |\n")
            f.write("|--------|--------------|----------|-------|\n")
            f.write(
                f"| Final Value | ${mstr['buy_hold']['final_value']:,.0f} | ${mstr['full_sd8']['final_value']:,.0f} | ${mstr['alpha_value']:,.0f} |\n"
            )
            f.write(
                f"| Drawdown | {mstr['buy_hold']['drawdown_pct']:.2f}% | {mstr['full_sd8']['drawdown_pct']:.2f}% | {mstr['unrealized_alpha_pct']:.2f}% |\n"
            )
            f.write("\n")

    print(f"\n✓ Results saved to {md_path}")

    # Create CSV for detailed analysis
    csv_data = []
    for ticker, data in results.items():
        if ticker == "MSTR_unrealized_alpha" or "error" in data:
            continue

        for strategy_name, summary in data.items():
            csv_data.append(
                {
                    "Ticker": ticker,
                    "Strategy": strategy_name,
                    "FinalValue": summary.get("final_value", 0),
                    "TotalWithdrawn": summary.get("total_withdrawn", 0),
                    "Survived": summary.get("portfolio_survived", False),
                    "FinalPurchasingPower": summary.get("final_purchasing_power", 0),
                }
            )

    csv_path = output_dir / "results.csv"
    pd.DataFrame(csv_data).to_csv(csv_path, index=False)
    print(f"✓ Detailed data saved to {csv_path}")


def main():
    """Run retirement planning experiment and save results."""
    results = run_retirement_experiment()
    save_results(results, OUTPUT_DIR)

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"\nResults saved to: {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
