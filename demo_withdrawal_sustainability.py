"""Demo: Withdrawal Rate Sustainability - Real Market Data

Shows how withdrawal rates interact with market returns using real historical data.
Key insight: 4% "safe withdrawal rate" is context-dependent!

Run: python demo_withdrawal_sustainability.py
"""

from datetime import date

from src.algorithms.buy_and_hold import BuyAndHoldAlgorithm
from src.data.fetcher import HistoryFetcher
from src.models.retirement_backtest import run_retirement_backtest


def demo_withdrawal_scenario(ticker, start_year, end_year, withdrawal_rate, description):
    """Run a single withdrawal scenario and print results."""
    start = date(start_year, 1, 1)
    end = date(end_year, 12, 31)

    fetcher = HistoryFetcher()
    df = fetcher.get_history(ticker, start, end)

    initial_qty = 1000
    algo = BuyAndHoldAlgorithm()

    _, summary = run_retirement_backtest(
        df,
        ticker,
        initial_qty,
        start,
        end,
        algo,
        annual_withdrawal_rate=withdrawal_rate,
        withdrawal_frequency="monthly",
        simple_mode=True,
    )

    start_price = df.iloc[0]["Close"].item()
    end_price = df.iloc[-1]["Close"].item()
    price_return_pct = (end_price / start_price - 1) * 100

    initial_value = initial_qty * start_price
    final_value = summary["final_value"]
    total_withdrawn = summary["total_withdrawn"]
    net_result = final_value + total_withdrawn - initial_value
    net_return_pct = (net_result / initial_value) * 100

    print(f"\n{description}")
    print(f"  Market return: {price_return_pct:+.1f}%")
    print(f"  Withdrawal rate: {withdrawal_rate*100:.0f}% annual")
    print(f"  Initial value: ${initial_value:,.0f}")
    print(f"  Final value: ${final_value:,.0f}")
    print(f"  Total withdrawn: ${total_withdrawn:,.0f}")
    print(f"  Net result: ${net_result:+,.0f} ({net_return_pct:+.1f}%)")

    return net_result


def main():
    """Demonstrate withdrawal sustainability across different market conditions."""
    print("=" * 80)
    print("WITHDRAWAL RATE SUSTAINABILITY - REAL MARKET DATA")
    print("=" * 80)
    print("\nKey Question: Is 4% a 'safe withdrawal rate'?")
    print("Answer: It depends on the market environment!\n")

    # Bull market: 4% is trivial
    print("\n" + "=" * 80)
    print("BULL MARKET: NVDA 2023")
    print("=" * 80)
    demo_withdrawal_scenario("NVDA", 2023, 2023, 0.04, "4% withdrawal in 245% bull market")
    demo_withdrawal_scenario("NVDA", 2023, 2023, 0.12, "12% withdrawal in 245% bull market")
    demo_withdrawal_scenario("NVDA", 2023, 2023, 1.00, "100% withdrawal (!) in 245% bull market")
    print("\n→ In explosive growth, even 100% annual withdrawal grows the portfolio!")

    # Moderate bull: 4% is safe, 12% makes a dent
    print("\n" + "=" * 80)
    print("MODERATE BULL: VOO 2019")
    print("=" * 80)
    demo_withdrawal_scenario("VOO", 2019, 2019, 0.04, "4% withdrawal in 29% bull market")
    demo_withdrawal_scenario("VOO", 2019, 2019, 0.12, "12% withdrawal in 29% bull market")
    print("\n→ Traditional stocks: 12% withdrawal eats ~40% of the gains")

    # Sideways: Any withdrawal eats principal
    print("\n" + "=" * 80)
    print("SIDEWAYS MARKET: SPY 2015")
    print("=" * 80)
    demo_withdrawal_scenario("SPY", 2015, 2015, 0.04, "4% withdrawal in flat market")
    demo_withdrawal_scenario("SPY", 2015, 2015, 0.12, "12% withdrawal in flat market")
    print("\n→ No growth: Every withdrawal eats principal (but you got income!)")

    # Bear market: Withdrawals compound losses
    print("\n" + "=" * 80)
    print("BEAR MARKET: SPY 2022")
    print("=" * 80)
    demo_withdrawal_scenario("SPY", 2022, 2022, 0.04, "4% withdrawal in -20% bear market")
    demo_withdrawal_scenario("SPY", 2022, 2022, 0.12, "12% withdrawal in -20% bear market")
    print("\n→ Bear market: 4% withdrawal + 20% loss = 24% total decline")

    # Crash: Devastating combination
    print("\n" + "=" * 80)
    print("MARKET CRASH: SPY 2008")
    print("=" * 80)
    demo_withdrawal_scenario("SPY", 2008, 2008, 0.04, "4% withdrawal in -38% crash")
    demo_withdrawal_scenario("SPY", 2008, 2008, 0.12, "12% withdrawal in -38% crash")
    print("\n→ Crash: Even 'safe' 4% withdrawal compounds to -42% total loss!")

    # Sequence-of-returns risk
    print("\n\n" + "=" * 80)
    print("SEQUENCE-OF-RETURNS RISK")
    print("=" * 80)
    print("\nSame total market return, same withdrawals")
    print("But different ORDER of returns = different outcomes!\n")

    # Good sequence: Bull first, bear later
    fetcher = HistoryFetcher()
    algo = BuyAndHoldAlgorithm()

    df1 = fetcher.get_history("SPY", date(2019, 1, 1), date(2019, 12, 31))
    _, s1 = run_retirement_backtest(
        df1,
        "SPY",
        1000,
        date(2019, 1, 1),
        date(2019, 12, 31),
        algo,
        0.05,
        "monthly",
        simple_mode=True,
    )

    df2 = fetcher.get_history("SPY", date(2022, 1, 1), date(2022, 12, 31))
    year2_qty = s1["holdings"]
    _, s2 = run_retirement_backtest(
        df2,
        "SPY",
        year2_qty,
        date(2022, 1, 1),
        date(2022, 12, 31),
        algo,
        0.05,
        "monthly",
        simple_mode=True,
    )

    good_net = (
        s2["final_value"]
        + s1["total_withdrawn"]
        + s2["total_withdrawn"]
        - (1000 * df1.iloc[0]["Close"].item())
    )

    print("GOOD SEQUENCE (Bull 2019 → Bear 2022):")
    print(f"  Year 1: +31% market, 5% withdrawal")
    print(f"  Year 2: -20% market, 5% withdrawal")
    print(f"  Net result: ${good_net:+,.0f}")

    # Bad sequence: Bear first, bull later
    df1 = fetcher.get_history("SPY", date(2022, 1, 1), date(2022, 12, 31))
    _, s1 = run_retirement_backtest(
        df1,
        "SPY",
        1000,
        date(2022, 1, 1),
        date(2022, 12, 31),
        algo,
        0.05,
        "monthly",
        simple_mode=True,
    )

    df2 = fetcher.get_history("SPY", date(2019, 1, 1), date(2019, 12, 31))
    year2_qty = s1["holdings"]
    _, s2 = run_retirement_backtest(
        df2,
        "SPY",
        year2_qty,
        date(2019, 1, 1),
        date(2019, 12, 31),
        algo,
        0.05,
        "monthly",
        simple_mode=True,
    )

    bad_net = (
        s2["final_value"]
        + s1["total_withdrawn"]
        + s2["total_withdrawn"]
        - (1000 * df1.iloc[0]["Close"].item())
    )

    print("\nBAD SEQUENCE (Bear 2022 → Bull 2019):")
    print(f"  Year 1: -20% market, 5% withdrawal")
    print(f"  Year 2: +31% market, 5% withdrawal")
    print(f"  Net result: ${bad_net:+,.0f}")

    print(f"\n→ SEQUENCE RISK COST: ${good_net - bad_net:,.0f}")
    print("  Same returns, same withdrawals, but order matters!")
    print("  Withdrawing during losses depletes shares, missing the recovery.")

    print("\n\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("\n1. 'Safe withdrawal rate' is context-dependent:")
    print("   - Bull market (NVDA +245%): Even 100% withdrawal grows portfolio!")
    print("   - Sideways (SPY +1%): 4% withdrawal eats principal")
    print("   - Bear market (SPY -20%): 4% withdrawal becomes -24% total loss")
    print("   - Crash (SPY -38%): 4% withdrawal becomes -42% total loss")

    print("\n2. Sequence-of-returns risk is real:")
    print("   - Same average return, different order = different outcomes")
    print("   - Withdrawing during losses is more damaging than during gains")

    print("\n3. Implications for strategy:")
    print("   - Build cash buffer BEFORE withdrawals start")
    print("   - Harvest volatility during bull markets (SD8 strategy)")
    print("   - Withdraw from cash during bear markets (preserve shares)")
    print("   - Sequence risk is why retirement planning needs dynamic strategies")

    print("\n" + "=" * 80)
    print("\nRun unit tests: python -m pytest tests/test_buyhold_withdrawal_rates.py -v")
    print("=" * 80)


if __name__ == "__main__":
    main()
