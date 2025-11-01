"""Generate comprehensive volatility alpha table across multiple assets and timeframes.

Collects data for:
- Multiple tickers (NVDA, MSTR, BTC, ETH, PLTR, GLD)
- Multiple timeframes (1, 2, 3 years)
- Auto-suggested SD parameter based on volatility
- Buyback count and volatility alpha

Output: CSV table with all metrics
"""

import csv
import math
from datetime import date, timedelta
from typing import Dict, Optional

from src.data.fetcher import HistoryFetcher
from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest


def calculate_annualized_volatility(df) -> float:
    """Calculate annualized volatility from daily returns."""
    if df is None or df.empty or "Close" not in df.columns:
        return 0.0

    returns = df["Close"].pct_change().dropna()
    if len(returns) < 2:
        return 0.0

    daily_vol = float(returns.std())
    annualized_vol = daily_vol * math.sqrt(252)
    return float(annualized_vol)


def suggest_sd_parameter(volatility: float) -> int:
    """Suggest SD parameter based on volatility."""
    vol_pct = volatility * 100

    if vol_pct >= 50:
        return 6
    elif vol_pct >= 30:
        return 8
    elif vol_pct >= 20:
        return 10
    elif vol_pct >= 10:
        return 16
    else:
        return 20


def calculate_trigger_pct(sd_n: int) -> float:
    """Calculate trigger percentage from SD parameter."""
    return (math.pow(2, 1.0 / sd_n) - 1) * 100


def collect_volatility_alpha_data(
    ticker: str,
    start_date: date,
    end_date: date,
) -> Optional[Dict]:
    """Collect volatility alpha data for a single ticker and timeframe.

    Returns:
        Dict with ticker, dates, algo, buy count, volatility alpha
    """
    fetcher = HistoryFetcher()

    # Fetch data
    print(f"  Fetching {ticker} from {start_date} to {end_date}...")
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        print(f"    ❌ No data for {ticker}")
        return None

    # Calculate volatility and suggest SD
    volatility = calculate_annualized_volatility(df)
    sd_n = suggest_sd_parameter(volatility)
    trigger_pct = calculate_trigger_pct(sd_n)
    trigger_decimal = trigger_pct / 100.0

    print(f"    Volatility: {volatility*100:.2f}% -> SD{sd_n} ({trigger_pct:.2f}%)")

    # Run full strategy
    algo_full = SyntheticDividendAlgorithm(
        rebalance_size=trigger_decimal,  # e.g., 0.0905 for 9.05%
        profit_sharing=0.5,  # 50% profit sharing
        buyback_enabled=True,
    )

    transactions_full, summary_full = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=100,
        start_date=start_date,
        end_date=end_date,
        algo=algo_full,
        simple_mode=True,
    )

    # Run ATH-only strategy
    algo_ath = SyntheticDividendAlgorithm(
        rebalance_size=trigger_decimal, profit_sharing=0.5, buyback_enabled=False
    )

    transactions_ath, summary_ath = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=100,
        start_date=start_date,
        end_date=end_date,
        algo=algo_ath,
        simple_mode=True,
    )

    # Calculate metrics
    vol_alpha = (summary_full["total_return"] - summary_ath["total_return"]) * 100

    # Count buy rebalances (BUY transactions in full strategy)
    buy_count = sum(
        1 for tx in transactions_full if tx.action == "BUY" and "BUYBACK" not in tx.notes.upper()
    )

    print(
        f"    [OK] Full: {summary_full['total_return']*100:.2f}%, ATH-only: {summary_ath['total_return']*100:.2f}%"
    )
    print(f"    [OK] Volatility Alpha: {vol_alpha:+.2f}%, Buy rebalances: {buy_count}")

    return {
        "ticker": ticker,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "years": (end_date - start_date).days / 365.25,
        "algo": f"SD{sd_n}",
        "trigger_pct": f"{trigger_pct:.2f}",
        "volatility_pct": f"{volatility*100:.2f}",
        "buy_rebalances": buy_count,
        "full_return_pct": f'{summary_full["total_return"]*100:.2f}',
        "ath_return_pct": f'{summary_ath["total_return"]*100:.2f}',
        "volatility_alpha_pct": f"{vol_alpha:.2f}",
    }


def main():
    """Generate volatility alpha table for multiple assets and timeframes."""

    # Define tickers
    tickers = ["NVDA", "MSTR", "BTC-USD", "ETH-USD", "PLTR", "GLD"]

    # Define end date (today)
    end_date = date(2025, 10, 26)

    # Define timeframes (1, 2, 3 years back from end_date)
    timeframes = [
        (1, end_date - timedelta(days=365)),
        (2, end_date - timedelta(days=730)),
        (3, end_date - timedelta(days=1095)),
    ]

    results = []

    print("=" * 80)
    print("VOLATILITY ALPHA TABLE GENERATION")
    print("=" * 80)
    print()

    for ticker in tickers:
        print(f"\n{ticker}:")
        print("-" * 40)

        for years, start_date in timeframes:
            result = collect_volatility_alpha_data(ticker, start_date, end_date)
            if result:
                results.append(result)

    # Write to CSV
    output_file = "volatility_alpha_table.csv"

    if results:
        fieldnames = [
            "ticker",
            "start_date",
            "end_date",
            "years",
            "algo",
            "trigger_pct",
            "volatility_pct",
            "buy_rebalances",
            "full_return_pct",
            "ath_return_pct",
            "volatility_alpha_pct",
        ]

        with open(output_file, "w", newline="") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(results)

        print("\n" + "=" * 80)
        print(f"[OK] Results written to {output_file}")
        print(f"   Total rows: {len(results)}")
        print("=" * 80)

        # Print summary table
        print("\nSUMMARY TABLE:")
        print("-" * 120)
        print(
            f"{'Ticker':<8} {'Years':<6} {'Algo':<6} {'Volatility':<12} {'Buys':<6} {'Full Ret':<10} {'ATH Ret':<10} {'Vol Alpha':<10}"
        )
        print("-" * 120)
        for r in results:
            print(
                f"{r['ticker']:<8} {r['years']:<6.1f} {r['algo']:<6} {r['volatility_pct']+'%':<12} "
                f"{r['buy_rebalances']:<6} {r['full_return_pct']+'%':<10} "
                f"{r['ath_return_pct']+'%':<10} {r['volatility_alpha_pct']+'%':<10}"
            )
        print("-" * 120)
    else:
        print("\n❌ No results collected")


if __name__ == "__main__":
    main()
