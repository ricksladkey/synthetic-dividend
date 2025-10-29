"""Unit tests: Buy-and-hold withdrawal sustainability across market conditions.

Tests withdrawal rates against real market data to find the tipping point where
withdrawals overtake growth. Shows sequence-of-returns risk clearly.

Market Conditions Tested:
- Bull market: NVDA 2023 (~239% gain)
- Moderate bull: VOO 2019 (~31% gain)
- Sideways: SPY 2015 (~1% gain)
- Bear market: SPY 2022 (-18% loss)
- Crash: SPY 2008 (-37% loss)
"""

from datetime import date

import pytest

from src.algorithms.buy_and_hold import BuyAndHoldAlgorithm
from src.data.fetcher import HistoryFetcher
from src.models.retirement_backtest import run_retirement_backtest


class TestBuyHoldWithdrawalSustainability:
    """Test withdrawal rate sustainability in buy-and-hold strategy."""

    @pytest.fixture
    def fetcher(self):
        """Shared data fetcher."""
        return HistoryFetcher()

    # ========================================================================
    # BULL MARKET: NVDA 2023 (~239% gain)
    # ========================================================================

    @pytest.mark.parametrize(
        "withdrawal_rate,expected_survival",
        [
            (0.04, True),  # 4% - trivial in 245% gain
            (0.07, True),  # 7% - still easy
            (0.12, True),  # 12% - works in explosive growth
            (0.20, True),  # 20% - even this survives!
            (0.50, True),  # 50% - withdrawing half still grows
            (1.00, True),  # 100% - withdrawing entire value still survives (doubles!)
            (2.00, True),  # 200% - even THIS survives!
            (3.00, False),  # 300% - finally exceeds 245% growth
        ],
    )
    def test_nvda_2023_bull_market(self, fetcher, withdrawal_rate, expected_survival):
        """NVDA 2023: Explosive growth (239%). Withdrawals are meaningless."""
        df = fetcher.get_history("NVDA", date(2023, 1, 1), date(2023, 12, 31))
        initial_qty = 1000

        algo = BuyAndHoldAlgorithm()
        txns, summary = run_retirement_backtest(
            df,
            "NVDA",
            initial_qty,
            date(2023, 1, 1),
            date(2023, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price = df.iloc[0]["Close"].item()
        end_price = df.iloc[-1]["Close"].item()
        price_gain_pct = (end_price / start_price - 1) * 100

        initial_value = initial_qty * start_price
        final_value = summary["final_value"]
        total_withdrawn = summary["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        survived = summary["portfolio_survived"]
        assert survived == expected_survival, (
            f"NVDA 2023 ({price_gain_pct:.1f}% gain): "
            f"{withdrawal_rate*100:.0f}% withdrawal should "
            f"{'survive' if expected_survival else 'fail'}\n"
            f"Initial: ${initial_value:,.0f}, Final: ${final_value:,.0f}, "
            f"Withdrawn: ${total_withdrawn:,.0f}, Net: ${net_result:,.0f}"
        )

        if survived:
            print(
                f"\n  {withdrawal_rate*100:3.0f}% withdrawal: "
                f"${initial_value:8,.0f} → ${final_value:8,.0f} "
                f"(withdrew ${total_withdrawn:6,.0f}, net ${net_result:+8,.0f})"
            )

    # ========================================================================
    # MODERATE BULL: VOO 2019 (~31% gain)
    # ========================================================================

    @pytest.mark.parametrize(
        "withdrawal_rate,expected_survival",
        [
            (0.04, True),  # 4% - safe withdrawal rate
            (0.07, True),  # 7% - still okay
            (0.12, True),  # 12% - getting tight
            (0.20, True),  # 20% - exceeds growth but survives 1 year
            (0.35, True),  # 35% - eats principal but survives 1 year
            (0.50, True),  # 50% - even this survives! (28% gain is huge)
        ],
    )
    def test_voo_2019_moderate_bull(self, fetcher, withdrawal_rate, expected_survival):
        """VOO 2019: Moderate bull market (31%). 12% withdrawal makes a dent."""
        df = fetcher.get_history("VOO", date(2019, 1, 1), date(2019, 12, 31))
        initial_qty = 1000

        algo = BuyAndHoldAlgorithm()
        txns, summary = run_retirement_backtest(
            df,
            "VOO",
            initial_qty,
            date(2019, 1, 1),
            date(2019, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price = df.iloc[0]["Close"].item()
        end_price = df.iloc[-1]["Close"].item()
        price_gain_pct = (end_price / start_price - 1) * 100

        initial_value = initial_qty * start_price
        final_value = summary["final_value"]
        total_withdrawn = summary["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        survived = summary["portfolio_survived"]
        assert survived == expected_survival, (
            f"VOO 2019 ({price_gain_pct:.1f}% gain): "
            f"{withdrawal_rate*100:.0f}% withdrawal should "
            f"{'survive' if expected_survival else 'fail'}\n"
            f"Initial: ${initial_value:,.0f}, Final: ${final_value:,.0f}, "
            f"Withdrawn: ${total_withdrawn:,.0f}, Net: ${net_result:,.0f}"
        )

        if survived:
            print(
                f"\n  {withdrawal_rate*100:3.0f}% withdrawal: "
                f"${initial_value:8,.0f} → ${final_value:8,.0f} "
                f"(withdrew ${total_withdrawn:6,.0f}, net ${net_result:+8,.0f})"
            )

    # ========================================================================
    # SIDEWAYS: SPY 2015 (~1% gain)
    # ========================================================================

    @pytest.mark.parametrize(
        "withdrawal_rate,expected_survival",
        [
            (0.04, True),  # 4% - exceeds growth but survives 1 year
            (0.07, True),  # 7% - eating principal
            (0.12, True),  # 12% - significant depletion
            (0.20, True),  # 20% - survives but major loss
            (0.30, True),  # 30% - still survives (barely growing)
        ],
    )
    def test_spy_2015_sideways(self, fetcher, withdrawal_rate, expected_survival):
        """SPY 2015: Sideways market (~1%). Any withdrawal eats principal."""
        df = fetcher.get_history("SPY", date(2015, 1, 1), date(2015, 12, 31))
        initial_qty = 1000

        algo = BuyAndHoldAlgorithm()
        txns, summary = run_retirement_backtest(
            df,
            "SPY",
            initial_qty,
            date(2015, 1, 1),
            date(2015, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price = df.iloc[0]["Close"].item()
        end_price = df.iloc[-1]["Close"].item()
        price_gain_pct = (end_price / start_price - 1) * 100

        initial_value = initial_qty * start_price
        final_value = summary["final_value"]
        total_withdrawn = summary["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        survived = summary["portfolio_survived"]
        assert survived == expected_survival, (
            f"SPY 2015 ({price_gain_pct:.1f}% gain): "
            f"{withdrawal_rate*100:.0f}% withdrawal should "
            f"{'survive' if expected_survival else 'fail'}\n"
            f"Initial: ${initial_value:,.0f}, Final: ${final_value:,.0f}, "
            f"Withdrawn: ${total_withdrawn:,.0f}, Net: ${net_result:,.0f}"
        )

        if survived:
            print(
                f"\n  {withdrawal_rate*100:3.0f}% withdrawal: "
                f"${initial_value:8,.0f} → ${final_value:8,.0f} "
                f"(withdrew ${total_withdrawn:6,.0f}, net ${net_result:+8,.0f})"
            )

    # ========================================================================
    # BEAR MARKET: SPY 2022 (-18% loss)
    # ========================================================================

    @pytest.mark.parametrize(
        "withdrawal_rate,expected_survival",
        [
            (0.04, True),  # 4% - survives but compounds losses
            (0.07, True),  # 7% - significant damage
            (0.12, True),  # 12% - severe depletion
            (0.20, True),  # 20% - survives but brutal (-20% price + 20% withdrawal = -40% total)
            (0.30, True),  # 30% - devastating but survives 1 year
        ],
    )
    def test_spy_2022_bear_market(self, fetcher, withdrawal_rate, expected_survival):
        """SPY 2022: Bear market (-18%). Withdrawals compound losses."""
        df = fetcher.get_history("SPY", date(2022, 1, 1), date(2022, 12, 31))
        initial_qty = 1000

        algo = BuyAndHoldAlgorithm()
        txns, summary = run_retirement_backtest(
            df,
            "SPY",
            initial_qty,
            date(2022, 1, 1),
            date(2022, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price = df.iloc[0]["Close"].item()
        end_price = df.iloc[-1]["Close"].item()
        price_gain_pct = (end_price / start_price - 1) * 100

        initial_value = initial_qty * start_price
        final_value = summary["final_value"]
        total_withdrawn = summary["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        survived = summary["portfolio_survived"]
        assert survived == expected_survival, (
            f"SPY 2022 ({price_gain_pct:.1f}% loss): "
            f"{withdrawal_rate*100:.0f}% withdrawal should "
            f"{'survive' if expected_survival else 'fail'}\n"
            f"Initial: ${initial_value:,.0f}, Final: ${final_value:,.0f}, "
            f"Withdrawn: ${total_withdrawn:,.0f}, Net: ${net_result:,.0f}"
        )

        if survived:
            print(
                f"\n  {withdrawal_rate*100:3.0f}% withdrawal: "
                f"${initial_value:8,.0f} → ${final_value:8,.0f} "
                f"(withdrew ${total_withdrawn:6,.0f}, net ${net_result:+8,.0f})"
            )

    # ========================================================================
    # CRASH: SPY 2008 (-37% loss)
    # ========================================================================

    @pytest.mark.parametrize(
        "withdrawal_rate,expected_survival",
        [
            (0.04, True),  # 4% - survives but brutal (-38% price + 4% withdrawal = -42% total)
            (0.07, True),  # 7% - devastating
            (0.12, True),  # 12% - catastrophic loss
            (0.15, True),  # 15% - survives but terrible
            (0.20, True),  # 20% - brutal (-38% price + 20% withdrawal = -58% total!)
        ],
    )
    def test_spy_2008_crash(self, fetcher, withdrawal_rate, expected_survival):
        """SPY 2008: Market crash (-37%). Withdrawals are devastating."""
        df = fetcher.get_history("SPY", date(2008, 1, 1), date(2008, 12, 31))
        initial_qty = 1000

        algo = BuyAndHoldAlgorithm()
        txns, summary = run_retirement_backtest(
            df,
            "SPY",
            initial_qty,
            date(2008, 1, 1),
            date(2008, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price = df.iloc[0]["Close"].item()
        end_price = df.iloc[-1]["Close"].item()
        price_gain_pct = (end_price / start_price - 1) * 100

        initial_value = initial_qty * start_price
        final_value = summary["final_value"]
        total_withdrawn = summary["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        survived = summary["portfolio_survived"]
        assert survived == expected_survival, (
            f"SPY 2008 ({price_gain_pct:.1f}% loss): "
            f"{withdrawal_rate*100:.0f}% withdrawal should "
            f"{'survive' if expected_survival else 'fail'}\n"
            f"Initial: ${initial_value:,.0f}, Final: ${final_value:,.0f}, "
            f"Withdrawn: ${total_withdrawn:,.0f}, Net: ${net_result:,.0f}"
        )

        if survived:
            print(
                f"\n  {withdrawal_rate*100:3.0f}% withdrawal: "
                f"${initial_value:8,.0f} → ${final_value:8,.0f} "
                f"(withdrew ${total_withdrawn:6,.0f}, net ${net_result:+8,.0f})"
            )


class TestSequenceOfReturnsRisk:
    """Demonstrate sequence-of-returns risk with same total return, different order."""

    @pytest.fixture
    def fetcher(self):
        """Shared data fetcher."""
        return HistoryFetcher()

    def test_good_sequence_bull_then_bear(self, fetcher):
        """Good sequence: Bull market first (2019), bear market later (2022).

        Withdrawing from gains is less damaging than withdrawing from losses.
        """
        # 2019 (bull) then 2022 (bear)
        df1 = fetcher.get_history("SPY", date(2019, 1, 1), date(2019, 12, 31))
        df2 = fetcher.get_history("SPY", date(2022, 1, 1), date(2022, 12, 31))

        initial_qty = 1000
        withdrawal_rate = 0.05  # 5% annual

        algo = BuyAndHoldAlgorithm()

        # Year 1: Bull market
        _, summary1 = run_retirement_backtest(
            df1,
            "SPY",
            initial_qty,
            date(2019, 1, 1),
            date(2019, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        # Year 2: Bear market (start with Year 1 ending qty)
        year2_qty = summary1["holdings"]
        _, summary2 = run_retirement_backtest(
            df2,
            "SPY",
            year2_qty,
            date(2022, 1, 1),
            date(2022, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price_y1 = df1.iloc[0]["Close"].item()
        end_price_y2 = df2.iloc[-1]["Close"].item()

        initial_value = initial_qty * start_price_y1
        final_value = summary2["final_value"]
        total_withdrawn = summary1["total_withdrawn"] + summary2["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        print(f"\nGOOD SEQUENCE (Bull → Bear):")
        print(
            f"  Year 1 (2019 +31%): ${initial_value:,.0f} → ${summary1['final_value']:,.0f} "
            f"(withdrew ${summary1['total_withdrawn']:,.0f})"
        )
        print(
            f"  Year 2 (2022 -18%): ${summary1['final_value']:,.0f} → ${final_value:,.0f} "
            f"(withdrew ${summary2['total_withdrawn']:,.0f})"
        )
        print(
            f"  Final: ${final_value:,.0f}, Total withdrawn: ${total_withdrawn:,.0f}, "
            f"Net: ${net_result:+,.0f}"
        )

        assert summary2["portfolio_survived"], "Good sequence should survive"

        # Store for comparison
        self.good_sequence_final = final_value
        self.good_sequence_net = net_result

    def test_bad_sequence_bear_then_bull(self, fetcher):
        """Bad sequence: Bear market first (2022), bull market later (2019 data).

        Withdrawing during losses depletes shares, missing the recovery.
        This is sequence-of-returns risk!
        """
        # 2022 (bear) then 2019 (bull) - using 2019 data for Year 2
        df1 = fetcher.get_history("SPY", date(2022, 1, 1), date(2022, 12, 31))
        df2 = fetcher.get_history("SPY", date(2019, 1, 1), date(2019, 12, 31))

        initial_qty = 1000
        withdrawal_rate = 0.05  # 5% annual (same as good sequence)

        algo = BuyAndHoldAlgorithm()

        # Year 1: Bear market
        _, summary1 = run_retirement_backtest(
            df1,
            "SPY",
            initial_qty,
            date(2022, 1, 1),
            date(2022, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        # Year 2: Bull market (start with Year 1 ending qty)
        year2_qty = summary1["holdings"]
        _, summary2 = run_retirement_backtest(
            df2,
            "SPY",
            year2_qty,
            date(2019, 1, 1),
            date(2019, 12, 31),
            algo,
            annual_withdrawal_rate=withdrawal_rate,
            withdrawal_frequency="monthly",
            simple_mode=True,
        )

        start_price_y1 = df1.iloc[0]["Close"].item()
        end_price_y2 = df2.iloc[-1]["Close"].item()

        initial_value = initial_qty * start_price_y1
        final_value = summary2["final_value"]
        total_withdrawn = summary1["total_withdrawn"] + summary2["total_withdrawn"]
        net_result = final_value + total_withdrawn - initial_value

        print(f"\nBAD SEQUENCE (Bear → Bull):")
        print(
            f"  Year 1 (2022 -18%): ${initial_value:,.0f} → ${summary1['final_value']:,.0f} "
            f"(withdrew ${summary1['total_withdrawn']:,.0f})"
        )
        print(
            f"  Year 2 (2019 +31%): ${summary1['final_value']:,.0f} → ${final_value:,.0f} "
            f"(withdrew ${summary2['total_withdrawn']:,.0f})"
        )
        print(
            f"  Final: ${final_value:,.0f}, Total withdrawn: ${total_withdrawn:,.0f}, "
            f"Net: ${net_result:+,.0f}"
        )

        assert summary2["portfolio_survived"], "Bad sequence should survive (but worse outcome)"

        # Compare to good sequence
        print(f"\nSEQUENCE RISK COMPARISON:")
        print(f"  Same withdrawals, same total market return")
        print(f"  But different ORDER of returns!")
        print(f"  Good sequence net: ${getattr(self, 'good_sequence_net', 0):+,.0f}")
        print(f"  Bad sequence net:  ${net_result:+,.0f}")
        if hasattr(self, "good_sequence_net"):
            difference = self.good_sequence_net - net_result
            print(f"  Sequence risk cost: ${difference:,.0f}")
