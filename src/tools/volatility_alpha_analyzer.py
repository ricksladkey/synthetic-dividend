"""Volatility Alpha Analyzer - Auto-suggest SD parameters and compare strategies.

This tool:
1. Fetches historical price data
2. Calculates annualized volatility
3. Suggests optimal SD parameter based on volatility
4. Compares full strategy vs ATH-only
5. Reports volatility alpha
6. Optionally plots price chart with buy/sell markers
"""

import math
import re
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.data.fetcher import HistoryFetcher
from src.models.backtest import SyntheticDividendAlgorithm, run_algorithm_backtest


def calculate_annualized_volatility(df: pd.DataFrame) -> float:
    """Calculate annualized volatility from daily price returns.

    Args:
        df: DataFrame with 'Close' prices

    Returns:
        Annualized volatility as decimal (e.g., 0.25 = 25%)
    """
    if df is None or df.empty or "Close" not in df.columns:
        return 0.0

    # Calculate daily returns
    returns = df["Close"].pct_change().dropna()

    if len(returns) < 2:
        return 0.0

    # Daily volatility (standard deviation of returns)
    daily_vol = float(returns.std())

    # Annualize: multiply by sqrt(252) trading days
    annualized_vol = daily_vol * math.sqrt(252)

    return float(annualized_vol)


def suggest_sd_parameter(volatility: float) -> Tuple[int, float, str]:
    """Suggest optimal SD parameter based on asset volatility.

    Heuristic:
    - Very high vol (>50%): SD4-SD6 (wider triggers, 18.92% - 12.25%)
    - High vol (30-50%): SD6-SD8 (12.25% - 9.05%)
    - Medium vol (20-30%): SD8-SD12 (9.05% - 5.95%)
    - Low vol (10-20%): SD12-SD16 (5.95% - 4.47%)
    - Very low vol (<10%): SD16-SD24 (4.47% - 2.93%)

    Args:
        volatility: Annualized volatility as decimal (e.g., 0.30 = 30%)

    Returns:
        Tuple of (sd_n, trigger_pct, reasoning)
    """
    vol_pct = volatility * 100

    if vol_pct >= 50:
        return (6, 12.25, f"Very high volatility ({vol_pct:.1f}%) → SD6 (12.25% trigger)")
    elif vol_pct >= 30:
        return (8, 9.05, f"High volatility ({vol_pct:.1f}%) → SD8 (9.05% trigger)")
    elif vol_pct >= 20:
        return (10, 7.18, f"Medium volatility ({vol_pct:.1f}%) → SD10 (7.18% trigger)")
    elif vol_pct >= 10:
        return (16, 4.47, f"Low volatility ({vol_pct:.1f}%) → SD16 (4.47% trigger)")
    else:
        return (20, 3.53, f"Very low volatility ({vol_pct:.1f}%) → SD20 (3.53% trigger)")


def calculate_minimum_alpha_per_cycle(trigger_pct: float) -> float:
    """Calculate theoretical minimum volatility alpha per buyback-resell cycle.

    Formula: Alpha ≈ (trigger%)² / 2

    This is the lower bound profit from each buyback cycle, assuming:
    - Price drops by exactly trigger%, then returns to original price
    - No gaps or price discontinuities (actual alpha usually higher)

    Args:
        trigger_pct: Rebalance trigger as percentage (e.g., 9.05 for SD8)

    Returns:
        Minimum alpha per cycle as decimal (e.g., 0.0041 = 0.41%)
    """
    trigger_decimal = trigger_pct / 100.0
    return (trigger_decimal**2) / 2.0


def _parse_transaction_line(line: str) -> Optional[Dict[str, Any]]:
    """Parse transaction log line to extract date, action, and price.

    Args:
        line: Transaction log line (e.g., "2024-01-15 SELL 10.5 shares @ 150.25")

    Returns:
        Dict with date, action, price or None if unparseable
    """
    parts = line.split()
    if not parts:
        return None

    date_str = parts[0]
    action = parts[1].upper() if len(parts) > 1 else None

    # Extract price after '@'
    price = None
    m = re.search(r"@\s*([0-9,.]+)", line)
    if m:
        try:
            price = float(m.group(1).replace(",", ""))
        except Exception:
            pass

    return {"date": date_str, "action": action, "price": price}


def plot_volatility_alpha_chart(
    df: pd.DataFrame,
    ticker: str,
    transactions: List[str],
    sd_n: int,
    volatility: float,
    vol_alpha: float,
    output_file: Optional[str] = None,
) -> str:
    """Plot price chart with buy/sell markers and save to file.

    Args:
        df: Price data DataFrame with 'Close' column
        ticker: Stock ticker symbol
        transactions: List of transaction log strings
        sd_n: SD parameter used (e.g., 8 for SD8)
        volatility: Annualized volatility as decimal
        vol_alpha: Volatility alpha as percentage
        output_file: Output filename (default: {ticker}_volatility_alpha.png)

    Returns:
        Output filename
    """
    import matplotlib.pyplot as plt

    if output_file is None:
        output_file = f"{ticker}_volatility_alpha.png"

    # Ensure datetime index
    df_plot = df.copy()
    df_plot.index = pd.to_datetime(df_plot.index)

    # Get price series
    if "Close" in df_plot.columns:
        price_series = df_plot["Close"]
    elif "Adj Close" in df_plot.columns:
        price_series = df_plot["Adj Close"]
    else:
        price_series = df_plot.select_dtypes(include=["number"]).iloc[:, 0]

    # Parse transactions
    buys_x, buys_y = [], []
    sells_x, sells_y = [], []

    for line in transactions:
        parsed = _parse_transaction_line(line)
        if not parsed or not parsed.get("date"):
            continue

        try:
            dt = pd.to_datetime(parsed["date"])
        except Exception:
            continue

        price = parsed.get("price")
        # If price missing, lookup close price for that date
        if price is None:
            try:
                price = float(price_series.loc[dt])
            except Exception:
                continue

        if parsed.get("action") == "BUY":
            buys_x.append(dt)
            buys_y.append(price)
        elif parsed.get("action") == "SELL":
            sells_x.append(dt)
            sells_y.append(price)

    # Create plot
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.plot(
        price_series.index, price_series.values, label=f"{ticker} Close", color="blue", linewidth=2
    )

    if buys_x:
        ax.scatter(
            buys_x,
            buys_y,
            color="red",
            marker="o",
            s=80,
            zorder=5,
            label="BUYS",
            edgecolors="darkred",
            linewidths=1.5,
        )
    if sells_x:
        ax.scatter(
            sells_x,
            sells_y,
            color="green",
            marker="o",
            s=80,
            zorder=5,
            label="SELLS",
            edgecolors="darkgreen",
            linewidths=1.5,
        )

    # Title with key metrics
    title = f"{ticker} - SD{sd_n} Volatility Alpha Analysis\n"
    title += f"Volatility: {volatility * 100:.2f}% | Volatility Alpha: {vol_alpha:+.2f}%"
    ax.set_title(title, fontsize=14, fontweight="bold")

    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Price", fontsize=12)
    ax.legend(loc="best", fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(output_file, dpi=150)
    plt.close(fig)

    return output_file


def analyze_volatility_alpha(
    ticker: str,
    start_date: date,
    end_date: date,
    initial_qty: Optional[int] = None,
    initial_investment: Optional[float] = None,
    profit_sharing: float = 50.0,
    auto_suggest: bool = True,
    sd_override: Optional[int] = None,
    plot: bool = False,
    plot_output: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze volatility alpha for a ticker.

    Workflow:
    1. Fetch historical data
    2. Calculate volatility
    3. Suggest SD parameter (or use override)
    4. Run full strategy
    5. Run ATH-only strategy
    6. Calculate and report volatility alpha
    7. Optionally plot price chart with trades

    Args:
        ticker: Stock symbol (e.g., "GLD", "NVDA")
        start_date: Backtest start date
        end_date: Backtest end date
        initial_qty: Number of shares to start with (optional)
        initial_investment: Dollar amount to invest (optional, default $1M)
        profit_sharing: Profit sharing percentage (0-100)
        auto_suggest: If True, auto-suggest SD parameter based on volatility
        sd_override: Override SD parameter (e.g., 8 for SD8)
        plot: If True, generate price chart with buy/sell markers
        plot_output: Output filename for plot (default: {ticker}_volatility_alpha.png)
        initial_qty: Number of shares to start with
        profit_sharing: Profit sharing percentage (0-100)
        auto_suggest: If True, auto-suggest SD parameter based on volatility
        sd_override: Override SD parameter (e.g., 8 for SD8)

    Returns:
        Dict with analysis results
    """
    fetcher = HistoryFetcher()

    print(f"\n{'=' * 80}")
    print(f"VOLATILITY ALPHA ANALYZER: {ticker}")
    print(f"{'=' * 80}\n")

    # Fetch data
    print(f"Fetching historical data for {ticker}...")
    df = fetcher.get_history(ticker, start_date, end_date)

    if df is None or df.empty:
        print(f"❌ No data available for {ticker}")
        return {}

    print(f"✓ Fetched {len(df)} days of data")

    # Calculate volatility
    volatility = calculate_annualized_volatility(df)
    print(f"\n📊 Historical Volatility: {volatility * 100:.2f}% annualized")

    # Determine SD parameter
    if auto_suggest and sd_override is None:
        sd_n, trigger_pct, reasoning = suggest_sd_parameter(volatility)
        print(f"💡 Auto-suggestion: {reasoning}")
    elif sd_override is not None:
        sd_n = sd_override
        # Calculate trigger from SD parameter: 2^(1/n) - 1
        trigger_pct = (math.pow(2, 1.0 / sd_n) - 1) * 100
        print(f"🎯 Using override: SD{sd_n} ({trigger_pct:.2f}% trigger)")
    else:
        sd_n = 8
        trigger_pct = 9.05
        print("⚙️ Using default: SD8 (9.05% trigger)")

    # Convert trigger to decimal for algorithm
    trigger_decimal = trigger_pct / 100.0

    # Run full strategy (with buybacks)
    print(f"\n{'─' * 80}")
    print(f"Running SD{sd_n} (Full Strategy - With Buybacks)...")
    print(f"{'─' * 80}")

    algo_full = SyntheticDividendAlgorithm(
        trigger_decimal * 100,  # Convert back to percentage for API
        profit_sharing,
        buyback_enabled=True,
    )

    transactions_full, summary_full = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        initial_investment=initial_investment,
        start_date=start_date,
        end_date=end_date,
        algo=algo_full,
        simple_mode=True,
    )

    print(f"Total Return: {summary_full['total_return'] * 100:.2f}%")
    print(f"Bank: ${summary_full['bank']:.2f}")
    print(f"Holdings: {summary_full['holdings']} shares")
    print(f"Transactions: {len(transactions_full)}")

    # Run ATH-only strategy (no buybacks)
    print(f"\n{'─' * 80}")
    print(f"Running SD{sd_n}-ATH-Only (No Buybacks)...")
    print(f"{'─' * 80}")

    algo_ath = SyntheticDividendAlgorithm(
        trigger_decimal * 100, profit_sharing, buyback_enabled=False
    )

    transactions_ath, summary_ath = run_algorithm_backtest(
        df=df,
        ticker=ticker,
        initial_qty=initial_qty,
        initial_investment=initial_investment,
        start_date=start_date,
        end_date=end_date,
        algo=algo_ath,
        simple_mode=True,
    )

    print(f"Total Return: {summary_ath['total_return'] * 100:.2f}%")
    print(f"Bank: ${summary_ath['bank']:.2f}")
    print(f"Holdings: {summary_ath['holdings']} shares")

    # Calculate volatility alpha
    vol_alpha = (summary_full["total_return"] - summary_ath["total_return"]) * 100

    # Count buyback transactions (BUY transactions in full strategy)
    buy_count = sum(
        1 for tx in transactions_full if tx.action == "BUY" and "BUYBACK" not in tx.notes.upper()
    )

    # Calculate theoretical minimum alpha
    min_alpha_per_cycle = calculate_minimum_alpha_per_cycle(trigger_pct)
    predicted_min_alpha = buy_count * min_alpha_per_cycle * 100  # As percentage

    print(f"\n{'=' * 80}")
    print("VOLATILITY ALPHA RESULTS")
    print(f"{'=' * 80}")
    print(f"Asset: {ticker}")
    print(f"Period: {start_date} to {end_date}")
    print(f"Historical Volatility: {volatility * 100:.2f}%")
    print(f"Strategy: SD{sd_n} ({trigger_pct:.2f}% trigger, {profit_sharing:.0f}% profit sharing)")
    print("")
    print(f"SD{sd_n} (Full) Return:      {summary_full['total_return'] * 100:>8.2f}%")
    print(f"SD{sd_n}-ATH-Only Return:    {summary_ath['total_return'] * 100:>8.2f}%")
    print(f"{'─' * 80}")
    print(f"Volatility Alpha:        {vol_alpha:>+8.2f}%")
    print("")
    print("📊 Theoretical Analysis:")
    print(f"   Buyback cycles: {buy_count}")
    print(f"   Min alpha/cycle: {min_alpha_per_cycle * 100:.3f}% (formula: trigger²/2)")
    print(f"   Predicted min alpha: {predicted_min_alpha:.2f}%")
    print(f"   Actual vs predicted: {vol_alpha:.2f}% vs {predicted_min_alpha:.2f}%")
    if vol_alpha > predicted_min_alpha:
        bonus = vol_alpha - predicted_min_alpha
        print(f"   ✨ Bonus alpha from gaps: +{bonus:.2f}% (actual exceeds minimum)")
    print("")

    if vol_alpha > 0.5:
        print(f"✅ Strong positive alpha! Buybacks added {vol_alpha:.2f}% extra return.")
    elif vol_alpha > 0.1:
        print(f"✓ Positive alpha. Buybacks added {vol_alpha:.2f}% extra return.")
    elif vol_alpha > -0.1:
        print("➡️ Neutral. Minimal difference between strategies.")
    else:
        print(f"⚠️ Negative alpha. Smooth trend - buybacks cost {abs(vol_alpha):.2f}%.")

    print(f"{'=' * 80}\n")

    # Generate plot if requested
    if plot:
        print("📊 Generating price chart with trade markers...")
        output_file = plot_volatility_alpha_chart(
            df=df,
            ticker=ticker,
                        transactions=[tx.to_string() for tx in transactions_full],
            sd_n=sd_n,
            volatility=volatility,
            vol_alpha=vol_alpha,
            output_file=plot_output,
        )
        print(f"✓ Chart saved to: {output_file}\n")

    # Return results
    return {
        "ticker": ticker,
        "volatility": volatility,
        "sd_parameter": sd_n,
        "trigger_pct": trigger_pct,
        "full_return": summary_full["total_return"],
        "ath_return": summary_ath["total_return"],
        "volatility_alpha": vol_alpha / 100,  # As decimal
        "full_summary": summary_full,
        "ath_summary": summary_ath,
    }


def main():
    """CLI entry point for volatility alpha analysis."""
    import argparse
    from datetime import datetime

    def parse_date_str(date_str: str) -> date:
        """Parse date string in multiple formats."""
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
        raise ValueError(f"Could not parse date: {date_str}")

    parser = argparse.ArgumentParser(
        description="Analyze volatility alpha and auto-suggest SD parameters"
    )
    parser.add_argument("ticker", help="Stock ticker symbol (e.g., GLD, NVDA)")
    parser.add_argument("start_date", help="Start date (YYYY-MM-DD or MM/DD/YYYY)")
    parser.add_argument("end_date", help="End date (YYYY-MM-DD or MM/DD/YYYY)")

    # Initial position: prefer --investment, fallback to --qty
    position_group = parser.add_mutually_exclusive_group()
    position_group.add_argument(
        "--investment",
        type=float,
        default=1_000_000.0,
        help="Investment amount in dollars (default: $1,000,000)",
    )
    position_group.add_argument(
        "--qty",
        type=int,
        help="Number of shares (alternative to --investment)",
    )

    parser.add_argument(
        "--profit-sharing",
        type=float,
        default=50.0,
        help="Profit sharing percentage (default: 50.0)",
    )
    parser.add_argument("--sd", type=int, help="Override SD parameter (e.g., 8 for SD8)")
    parser.add_argument(
        "--no-auto",
        action="store_true",
        help="Disable auto-suggestion (use default SD8)",
    )
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Generate price chart with buy/sell markers",
    )
    parser.add_argument(
        "--plot-output",
        type=str,
        help="Output filename for plot (default: {ticker}_volatility_alpha.png)",
    )

    args = parser.parse_args()

    # Parse dates
    start_date = parse_date_str(args.start_date)
    end_date = parse_date_str(args.end_date)

    # Determine initial position
    initial_qty = args.qty if args.qty else None
    initial_investment = args.investment if initial_qty is None else None

    # Run analysis
    analyze_volatility_alpha(
        ticker=args.ticker,
        start_date=start_date,
        end_date=end_date,
        initial_qty=initial_qty,
        initial_investment=initial_investment,
        profit_sharing=args.profit_sharing,
        auto_suggest=not args.no_auto,
        sd_override=args.sd,
        plot=args.plot,
        plot_output=args.plot_output,
    )


if __name__ == "__main__":
    main()
