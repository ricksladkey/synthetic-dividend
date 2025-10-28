"""Research Experiment: Multi-Asset Portfolio Volatility Alpha

This experiment tests whether volatility alpha scales across a diversified portfolio.

Hypothesis:
    Volatility harvesting (synthetic dividend) should generate alpha on each volatile
    asset independently. The total portfolio alpha should approximate the sum of
    individual asset alphas weighted by allocation.

Test Portfolio:
    20% NVDA  (high volatility tech)
    20% GOOG  (moderate volatility tech)
    20% PLTR  (high volatility tech)
    20% BTC-USD (extreme volatility crypto)
    20% ETH-USD (extreme volatility crypto)

Baseline:
    100% VOO (S&P 500 index)

Strategies Tested:
    1. Buy-and-Hold: Simple buy and hold each asset
    2. ATH-Only (SD8): Sell only at new all-time highs (9.05% trigger, 50% profit sharing)
    3. Full SD8: Complete volatility harvesting with buyback stack

Period: 2023-01-01 to 2024-12-31 (2 years)
Initial Investment: $1,000,000 per strategy

Metrics:
    - Total return for each strategy
    - Volatility alpha (Full SD8 vs ATH-Only)
    - Per-asset alpha contribution
    - Portfolio-level alpha vs VOO

Output:
    - Summary table comparing all strategies
    - Per-asset alpha breakdown
    - Stacked composition charts
    - Volatility alpha attribution analysis
"""

from datetime import date
from pathlib import Path
from typing import Dict

import pandas as pd

from src.algorithms.factory import build_algo_from_name
from src.data.fetcher import HistoryFetcher
from src.models.backtest import run_algorithm_backtest

# Experiment parameters
TICKERS = ["NVDA", "GOOG", "PLTR", "BTC-USD", "ETH-USD"]
ALLOCATIONS = {ticker: 0.20 for ticker in TICKERS}  # Equal weight
BASELINE_TICKER = "VOO"

START_DATE = date(2023, 1, 1)
END_DATE = date(2024, 12, 31)
INITIAL_VALUE = 1_000_000

# SD8 parameters (9.05% rebalance, 50% profit sharing)
SD_TRIGGER = 9.05
SD_PROFIT_SHARING = 50.0


def run_single_asset_backtest(
    ticker: str, strategy: str, allocation: float, start: date, end: date, initial_value: float
) -> Dict:
    """Run backtest for single asset with given strategy.

    Args:
        ticker: Asset ticker
        strategy: 'buy-hold', 'ath-only', or 'full-sd8'
        allocation: Portfolio allocation (0.0-1.0)
        start: Start date
        end: End date
        initial_value: Total portfolio value

    Returns:
        Dict with backtest results and metrics
    """
    # Fetch data
    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start, end)

    if df is None or df.empty:
        raise ValueError(f"No data for {ticker}")

    # Calculate investment for this asset
    asset_investment = initial_value * allocation

    # Determine initial quantity (buy on first day)
    first_price = df.iloc[0]["Close"].item()
    initial_qty = int(asset_investment / first_price)

    # Build algorithm based on strategy
    if strategy == "buy-hold":
        algo = build_algo_from_name("buy-and-hold")
    elif strategy == "ath-only":
        algo = build_algo_from_name(f"sd-ath-only-{SD_TRIGGER},{SD_PROFIT_SHARING}")
    elif strategy == "full-sd8":
        algo = build_algo_from_name(f"sd-{SD_TRIGGER},{SD_PROFIT_SHARING}")

    else:
        raise ValueError(f"Unknown strategy: {strategy}")

    # Run backtest
    transactions, summary = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        start_date=start,
        end_date=end,
        algo=algo,
        simple_mode=True,  # Disable costs/inflation for clean comparison
    )

    return {
        "ticker": ticker,
        "strategy": strategy,
        "allocation": allocation,
        "initial_investment": asset_investment,
        "initial_qty": initial_qty,
        "final_value": summary["total"],
        "total_return": summary["total_return"],
        "annualized_return": summary.get("annualized_return", 0),
        "final_holdings": summary["holdings"],
        "final_bank": summary["bank"],
        "transaction_count": len([t for t in transactions if t.action in ["BUY", "SELL"]]),
        "volatility_alpha": summary.get("volatility_alpha", 0),
        "summary": summary,
    }


def run_portfolio_experiment() -> Dict:
    """Run complete portfolio volatility alpha experiment.

    Returns:
        Dict with all results and analysis
    """
    print("=" * 80)
    print("PORTFOLIO VOLATILITY ALPHA EXPERIMENT")
    print("=" * 80)
    print(f"\nPeriod: {START_DATE} to {END_DATE}")
    print(f"Initial Investment: ${INITIAL_VALUE:,.0f}")
    print(f"\nPortfolio Allocation:")
    for ticker, alloc in ALLOCATIONS.items():
        print(f"  {ticker}: {alloc*100:.0f}%")
    print(f"\nBaseline: 100% {BASELINE_TICKER}")
    print(f"SD Parameters: {SD_TRIGGER}% trigger, {SD_PROFIT_SHARING}% profit sharing")
    print("=" * 80)

    # Run baseline (VOO buy-and-hold)
    print(f"\n[BASELINE] Running {BASELINE_TICKER} buy-and-hold...")
    baseline_result = run_single_asset_backtest(
        ticker=BASELINE_TICKER,
        strategy="buy-hold",
        allocation=1.0,
        start=START_DATE,
        end=END_DATE,
        initial_value=INITIAL_VALUE,
    )
    print(f"  Final Value: ${baseline_result['final_value']:,.0f}")
    print(f"  Total Return: {baseline_result['total_return']:+.2f}%")

    # Run portfolio strategies
    strategies = ["buy-hold", "ath-only", "full-sd8"]
    portfolio_results = {strat: [] for strat in strategies}

    for strategy in strategies:
        print(f"\n[PORTFOLIO: {strategy.upper()}]")

        for ticker in TICKERS:
            print(f"  Running {ticker}...", end=" ")
            result = run_single_asset_backtest(
                ticker=ticker,
                strategy=strategy,
                allocation=ALLOCATIONS[ticker],
                start=START_DATE,
                end=END_DATE,
                initial_value=INITIAL_VALUE,
            )
            portfolio_results[strategy].append(result)
            print(f"${result['final_value']:,.0f} ({result['total_return']:+.2f}%)")

    # Aggregate portfolio-level metrics
    print("\n" + "=" * 80)
    print("PORTFOLIO-LEVEL RESULTS")
    print("=" * 80)

    aggregated = {}
    for strategy in strategies:
        total_value = sum(r["final_value"] for r in portfolio_results[strategy])
        total_return = ((total_value - INITIAL_VALUE) / INITIAL_VALUE) * 100

        # Calculate annualized return
        days = (END_DATE - START_DATE).days
        years = days / 365.25
        annualized = (((total_value / INITIAL_VALUE) ** (1 / years)) - 1) * 100 if years > 0 else 0

        aggregated[strategy] = {
            "final_value": total_value,
            "total_return": total_return,
            "annualized_return": annualized,
            "asset_results": portfolio_results[strategy],
        }

        print(f"\n{strategy.upper()}:")
        print(f"  Final Value: ${total_value:,.0f}")
        print(f"  Total Return: {total_return:+.2f}%")
        print(f"  Annualized: {annualized:+.2f}%")

    # Calculate volatility alpha
    print("\n" + "=" * 80)
    print("VOLATILITY ALPHA ANALYSIS")
    print("=" * 80)

    # ATH-Only vs Buy-Hold (baseline alpha from selling at peaks)
    ath_alpha = aggregated["ath-only"]["total_return"] - aggregated["buy-hold"]["total_return"]
    print(f"\nATH-Only Alpha (vs Buy-Hold): {ath_alpha:+.2f}%")

    # Full SD8 vs ATH-Only (pure volatility alpha from buyback stack)
    vol_alpha = aggregated["full-sd8"]["total_return"] - aggregated["ath-only"]["total_return"]
    print(f"Volatility Alpha (Full SD8 vs ATH-Only): {vol_alpha:+.2f}%")

    # Full SD8 vs Buy-Hold (total enhanced alpha)
    total_alpha = aggregated["full-sd8"]["total_return"] - aggregated["buy-hold"]["total_return"]
    print(f"Total Enhanced Alpha: {total_alpha:+.2f}%")

    # Portfolio vs VOO alpha
    portfolio_vs_voo = aggregated["full-sd8"]["total_return"] - baseline_result["total_return"]
    print(f"\nPortfolio Alpha vs {BASELINE_TICKER}: {portfolio_vs_voo:+.2f}%")

    # Per-asset volatility alpha contribution
    print(f"\n{'='*80}")
    print("PER-ASSET VOLATILITY ALPHA BREAKDOWN")
    print(f"{'='*80}")
    print(
        f"\n{'Asset':<10} {'Allocation':<12} {'Buy-Hold':<15} {'ATH-Only':<15} {'Full SD8':<15} {'Vol Alpha':<12}"
    )
    print("-" * 80)

    for i, ticker in enumerate(TICKERS):
        bh = portfolio_results["buy-hold"][i]
        ath = portfolio_results["ath-only"][i]
        full = portfolio_results["full-sd8"][i]

        bh_return = bh["total_return"]
        ath_return = ath["total_return"]
        full_return = full["total_return"]
        asset_vol_alpha = full_return - ath_return

        print(
            f"{ticker:<10} {ALLOCATIONS[ticker]*100:>5.0f}%        "
            f"{bh_return:>+7.2f}%        {ath_return:>+7.2f}%        "
            f"{full_return:>+7.2f}%        {asset_vol_alpha:>+7.2f}%"
        )

    # Summary table
    print(f"\n{'='*80}")
    print("SUMMARY COMPARISON")
    print(f"{'='*80}")
    print(f"\n{'Strategy':<25} {'Final Value':<20} {'Total Return':<15} {'Ann. Return':<15}")
    print("-" * 80)
    print(
        f"{'VOO Baseline':<25} ${baseline_result['final_value']:>18,.0f} {baseline_result['total_return']:>+13.2f}% {baseline_result['annualized_return']:>+13.2f}%"
    )
    for strategy in strategies:
        name = f"Portfolio {strategy.replace('-', ' ').title()}"
        agg = aggregated[strategy]
        print(
            f"{name:<25} ${agg['final_value']:>18,.0f} {agg['total_return']:>+13.2f}% {agg['annualized_return']:>+13.2f}%"
        )

    return {
        "baseline": baseline_result,
        "portfolio_results": portfolio_results,
        "aggregated": aggregated,
        "volatility_alpha": {
            "ath_vs_buyhold": ath_alpha,
            "full_vs_ath": vol_alpha,
            "total_enhanced": total_alpha,
            "vs_voo": portfolio_vs_voo,
        },
    }


def save_results(results: Dict, output_dir: str = "experiments/portfolio_volatility_alpha") -> None:
    """Save experiment results to CSV and markdown summary.

    Args:
        results: Experiment results dict
        output_dir: Output directory path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Build summary markdown
    summary_lines = [
        "# Portfolio Volatility Alpha Experiment",
        "",
        f"**Date**: {date.today().isoformat()}",
        f"**Period**: {START_DATE} to {END_DATE}",
        f"**Initial Investment**: ${INITIAL_VALUE:,.0f}",
        "",
        "## Portfolio Allocation",
        "",
    ]

    for ticker, alloc in ALLOCATIONS.items():
        summary_lines.append(f"- {ticker}: {alloc*100:.0f}%")

    summary_lines.extend(
        [
            "",
            f"## Baseline: 100% {BASELINE_TICKER}",
            "",
            f"- Final Value: ${results['baseline']['final_value']:,.0f}",
            f"- Total Return: {results['baseline']['total_return']:+.2f}%",
            f"- Annualized: {results['baseline']['annualized_return']:+.2f}%",
            "",
            "## Portfolio Results",
            "",
            "| Strategy | Final Value | Total Return | Annualized |",
            "|----------|-------------|--------------|------------|",
        ]
    )

    for strategy in ["buy-hold", "ath-only", "full-sd8"]:
        agg = results["aggregated"][strategy]
        strategy_name = strategy.replace("-", " ").title()
        summary_lines.append(
            f"| {strategy_name} | ${agg['final_value']:,.0f} | "
            f"{agg['total_return']:+.2f}% | {agg['annualized_return']:+.2f}% |"
        )

    summary_lines.extend(
        [
            "",
            "## Volatility Alpha Analysis",
            "",
            f"- **ATH-Only Alpha** (vs Buy-Hold): {results['volatility_alpha']['ath_vs_buyhold']:+.2f}%",
            f"- **Volatility Alpha** (Full SD8 vs ATH-Only): {results['volatility_alpha']['full_vs_ath']:+.2f}%",
            f"- **Total Enhanced Alpha**: {results['volatility_alpha']['total_enhanced']:+.2f}%",
            f"- **Portfolio vs VOO Alpha**: {results['volatility_alpha']['vs_voo']:+.2f}%",
            "",
            "## Per-Asset Breakdown",
            "",
            "| Asset | Allocation | Buy-Hold | ATH-Only | Full SD8 | Vol Alpha |",
            "|-------|------------|----------|----------|----------|-----------|",
        ]
    )

    for i, ticker in enumerate(TICKERS):
        bh = results["portfolio_results"]["buy-hold"][i]
        ath = results["portfolio_results"]["ath-only"][i]
        full = results["portfolio_results"]["full-sd8"][i]
        asset_alpha = full["total_return"] - ath["total_return"]

        summary_lines.append(
            f"| {ticker} | {ALLOCATIONS[ticker]*100:.0f}% | "
            f"{bh['total_return']:+.2f}% | {ath['total_return']:+.2f}% | "
            f"{full['total_return']:+.2f}% | {asset_alpha:+.2f}% |"
        )

    # Save summary
    summary_file = output_path / "SUMMARY.md"
    summary_file.write_text("\n".join(summary_lines))
    print(f"\n✓ Summary saved to: {summary_file}")

    # Save detailed CSV
    csv_data = []
    for strategy in ["buy-hold", "ath-only", "full-sd8"]:
        for result in results["portfolio_results"][strategy]:
            csv_data.append(
                {
                    "strategy": strategy,
                    "ticker": result["ticker"],
                    "allocation": result["allocation"],
                    "initial_investment": result["initial_investment"],
                    "final_value": result["final_value"],
                    "total_return": result["total_return"],
                    "annualized_return": result["annualized_return"],
                    "transaction_count": result["transaction_count"],
                }
            )

    df = pd.DataFrame(csv_data)
    csv_file = output_path / "results.csv"
    df.to_csv(csv_file, index=False)
    print(f"✓ Detailed results saved to: {csv_file}")


def main():
    """Run portfolio volatility alpha experiment."""
    results = run_portfolio_experiment()
    save_results(results)

    print("\n" + "=" * 80)
    print("EXPERIMENT COMPLETE")
    print("=" * 80)
    print(f"\nKey Finding:")
    print(f"  Volatility Alpha: {results['volatility_alpha']['full_vs_ath']:+.2f}%")
    print(f"  Portfolio vs VOO: {results['volatility_alpha']['vs_voo']:+.2f}%")
    print(f"\nResults saved to: experiments/portfolio_volatility_alpha/")


if __name__ == "__main__":
    main()
