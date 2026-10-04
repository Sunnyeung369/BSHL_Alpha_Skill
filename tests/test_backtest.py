import dataclasses
from datetime import date, datetime, timedelta, timezone
import unittest

from bshl.market import Bar, Dataset
from bshl.backtest import BacktestConfig, TradeSignal, run_backtest


UTC = timezone.utc
DAYS = [date(2025, 1, 2), date(2025, 1, 3), date(2025, 1, 6), date(2025, 1, 7)]


def fixture():
    bars = tuple(Bar(datetime(day.year, day.month, day.day, 21, tzinfo=UTC),
        100, 105, 95, 100, 10000, datetime(day.year, day.month, day.day, 21, tzinfo=UTC),
        session_open=datetime(day.year, day.month, day.day, 14, 30, tzinfo=UTC)) for day in DAYS)
    return Dataset(symbol="TEST", source_url="https://example.org/synthetic-fixture",
        data_mode="mock", is_mock=True, bars=bars, session_dates=tuple(DAYS),
        retrieved_at=datetime(2025, 1, 8, tzinfo=UTC))


def config(**kwargs):
    return BacktestConfig(train_end=DAYS[1], test_start=DAYS[2],
        commission_bps=0, slippage_bps=0, spread_bps=0, **kwargs)


def first_signal(snapshot):
    return TradeSignal(90, 120, "fixture") if len(snapshot.bars) == 1 else None


class BacktestTests(unittest.TestCase):
    def test_signal_fills_next_open_and_levels_stay_frozen(self):
        result = run_backtest(fixture(), config(), first_signal)
        trade = result["trades"][0]
        self.assertEqual(trade["entry_at"], fixture().bars[1].session_open.isoformat())
        self.assertEqual((trade["stop"], trade["target"], trade["units"]), (90, 120, 100))

    def test_next_bar_close_does_not_choose_position_size(self):
        original = fixture()
        varied = dataclasses.replace(original, bars=(original.bars[0],
            dataclasses.replace(original.bars[1], high=115, close=110), *original.bars[2:]))
        first = run_backtest(original, config(), first_signal)["trades"][0]
        second = run_backtest(varied, config(), first_signal)["trades"][0]
        self.assertEqual(first["units"], second["units"])
        self.assertEqual(first["entry_price"], second["entry_price"])

    def test_publication_after_next_open_delays_the_fill(self):
        dataset = fixture()
        delayed = dataclasses.replace(dataset.bars[0], available_at=dataset.bars[1].session_open + timedelta(minutes=30))
        dataset = dataclasses.replace(dataset, bars=(delayed, *dataset.bars[1:]))
        result = run_backtest(dataset, config(), first_signal)
        self.assertEqual(result["trades"][0]["entry_at"], dataset.bars[2].session_open.isoformat())

    def test_both_levels_touched_uses_stop(self):
        dataset = fixture()
        conflict = dataclasses.replace(dataset.bars[1], high=125, low=85)
        dataset = dataclasses.replace(dataset, bars=(dataset.bars[0], conflict, *dataset.bars[2:]))
        trade = run_backtest(dataset, config(), first_signal)["trades"][0]
        self.assertEqual(trade["exit_price"], 90)
        self.assertEqual(trade["exit_reason"], "stop_conservative_intrabar")
        self.assertEqual(trade["r_after_costs"], -1)

    def test_gap_stop_uses_open_price(self):
        dataset = fixture()
        gap = dataclasses.replace(dataset.bars[2], open=80, high=95, low=75, close=90)
        dataset = dataclasses.replace(dataset, bars=(*dataset.bars[:2], gap, dataset.bars[3]))
        trade = run_backtest(dataset, config(), first_signal)["trades"][0]
        self.assertEqual(trade["exit_reason"], "gap_stop")
        self.assertEqual(trade["exit_price"], 80)

    def test_bilateral_costs_and_benchmark_share_cost_assumptions(self):
        setup = BacktestConfig(train_end=DAYS[1], test_start=DAYS[2],
            commission_bps=10, slippage_bps=10, spread_bps=10)
        result = run_backtest(fixture(), setup, first_signal)
        trade = result["trades"][0]
        self.assertGreater(trade["entry_fee"], 0)
        self.assertGreater(trade["exit_fee"], 0)
        self.assertLess(result["return_after_costs"], 0)
        self.assertLess(result["benchmark"]["return_after_costs"], 0)

    def test_only_known_volume_caps_size(self):
        dataset = fixture()
        tiny = dataclasses.replace(dataset.bars[0], volume=50)
        dataset = dataclasses.replace(dataset, bars=(tiny, *dataset.bars[1:]))
        result = run_backtest(dataset, config(), first_signal)
        self.assertEqual(result["trade_count"], 0)
        self.assertEqual(result["skipped"][0]["reason"], "cash_risk_or_known_volume_insufficient")

    def test_unfinished_end_session_does_not_use_previous_close_to_exit(self):
        end = fixture().bars[1].session_open + timedelta(hours=2)
        result = run_backtest(fixture(), config(end_date=end), first_signal)
        self.assertEqual(result["valuation_status"], "unknown")
        self.assertIsNone(result["final_value"])
        self.assertIsNone(result["return_after_costs"])
        self.assertIsNotNone(result["open_position"])

    def test_unavailable_end_price_remains_unknown(self):
        dataset = fixture()
        last = dataclasses.replace(dataset.bars[-1], available_at=dataset.bars[-1].timestamp + timedelta(days=1))
        dataset = dataclasses.replace(dataset, bars=(*dataset.bars[:-1], last))
        result = run_backtest(dataset, config(end_date=last.timestamp), first_signal)
        self.assertIsNone(result["final_value"])
        self.assertEqual(result["valuation_status"], "unknown")

    def test_callback_receives_immutable_visible_history(self):
        def callback(snapshot):
            self.assertTrue(all(bar.available_at <= snapshot.as_of for bar in snapshot.bars))
            self.assertIsInstance(snapshot.bars, tuple)
            with self.assertRaises(dataclasses.FrozenInstanceError):
                snapshot.as_of = datetime.now(UTC)
            self.assertFalse(hasattr(snapshot, "dataset"))
            return None
        run_backtest(fixture(), config(), callback)

    def test_future_mutation_does_not_change_cutoff_report(self):
        dataset = fixture()
        changed = dataclasses.replace(dataset, bars=(*dataset.bars[:2],
            dataclasses.replace(dataset.bars[2], high=999, close=999), dataset.bars[3]))
        setup = config(end_date=DAYS[1])
        self.assertEqual(run_backtest(dataset, setup, first_signal), run_backtest(changed, setup, first_signal))

    def test_repeatability_mock_label_and_independent_splits(self):
        first = run_backtest(fixture(), config(), first_signal)
        self.assertEqual(first, run_backtest(fixture(), config(), first_signal))
        self.assertTrue(first["is_mock"])
        self.assertFalse(first["performance_validated"])
        self.assertEqual(first["evidence_status"], "synthetic_simulation")
        self.assertIn("in_sample", first)
        self.assertIn("out_of_sample", first)
        self.assertEqual(first["in_sample"]["trades"][0]["exit_reason"], "window_end_close")

    def test_explicit_session_open_required_and_non_cash_profile_rejected(self):
        dataset = fixture()
        missing = dataclasses.replace(dataset, bars=(dataclasses.replace(dataset.bars[0], session_open=None), *dataset.bars[1:]))
        with self.assertRaisesRegex(ValueError, "session_open"):
            run_backtest(missing, config())
        with self.assertRaises(ValueError):
            run_backtest(dataclasses.replace(dataset, market="CRYPTO", asset_type="CRYPTO"), config())

    def test_invalid_split_and_levels_rejected(self):
        with self.assertRaises(ValueError):
            BacktestConfig(train_end=DAYS[2], test_start=DAYS[1])
        with self.assertRaises(ValueError):
            run_backtest(fixture(), config(), lambda snapshot: TradeSignal(110, 120))

    def test_gap_exit_is_known_at_open_before_daily_close(self):
        dataset = fixture()
        gap = dataclasses.replace(dataset.bars[2], open=80, high=95, low=75, close=90)
        dataset = dataclasses.replace(dataset, bars=(*dataset.bars[:2], gap, dataset.bars[3]))
        result = run_backtest(dataset, config(end_date=gap.session_open), first_signal)
        self.assertEqual(result["trades"][0]["exit_at"], gap.session_open.isoformat())
        self.assertIsNone(result["open_position"])
        self.assertIsNotNone(result["final_value"])

    def test_empty_holdout_has_no_return_claim(self):
        result = run_backtest(fixture(), config(end_date=DAYS[1]), first_signal)
        self.assertEqual(result["out_of_sample"]["valuation_status"], "empty_window")
        self.assertIsNone(result["out_of_sample"]["return_after_costs"])

    def test_numeric_strings_and_boolean_signal_levels_rejected(self):
        for value in (True, "100", float("inf")):
            with self.assertRaises(ValueError):
                config(initial_capital=value)
        with self.assertRaises(ValueError):
            run_backtest(fixture(), config(), lambda snapshot: TradeSignal(True, 120))

    def test_delayed_final_publication_marks_without_backdated_liquidation(self):
        dataset = fixture()
        last = dataclasses.replace(dataset.bars[-1], available_at=dataset.bars[-1].timestamp + timedelta(hours=1))
        result = run_backtest(dataclasses.replace(dataset, bars=(*dataset.bars[:-1], last)), config(), first_signal)
        self.assertEqual(result["end_valuation_method"], "mark_to_market_without_retroactive_exit")
        self.assertIsNotNone(result["open_position"])
        self.assertEqual(result["trade_count"], 0)
        self.assertIsNotNone(result["final_value"])

    def test_trade_metrics_account_for_exposure_costs_and_small_sample(self):
        dataset = fixture()
        conflict = dataclasses.replace(dataset.bars[1], high=125, low=85)
        result = run_backtest(dataclasses.replace(dataset, bars=(dataset.bars[0], conflict, *dataset.bars[2:])), config(), first_signal)
        self.assertEqual(result["average_loss_after_costs"], -1000)
        self.assertIsNone(result["average_win_after_costs"])
        self.assertEqual(result["exposure_seconds"], 6.5 * 3600)
        self.assertAlmostEqual(result["turnover_notional_over_initial_capital"], .19)
        self.assertEqual(result["sample_evidence"], "insufficient")
        self.assertEqual(len(result["failed_trade_samples"]), 1)


if __name__ == "__main__":
    unittest.main()
