"""Synthetic fixtures test temporal integrity and experimental structure rules."""

import csv
from dataclasses import FrozenInstanceError, replace
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import tempfile
import unittest

from bshl.market import Bar, CSV_COLUMNS, Dataset, as_of_slice, load_dataset, parse_timestamp, validate_dataset
from bshl.structure import (StructureConfig, analyze_structure, completed_weekly_bars,
                            confirmed_pivots, moving_average, wilder_atr)


def fixture(count=75, *, calendar=True):
    # A synthetic declared calendar, not a claim about NYSE holidays.
    day = datetime(2025, 1, 6, 16, tzinfo=timezone.utc)
    days = []
    while len(days) < count + 10:
        if day.weekday() < 5:
            days.append(day)
        day += timedelta(days=1)
    bars = tuple(Bar(stamp, 100 + index * .1, 101 + index * .1,
                     99 + index * .1, 100 + index * .1, 100,
                     stamp + timedelta(minutes=1), True, stamp.replace(hour=9))
                 for index, stamp in enumerate(days[:count]))
    return Dataset(symbol="DEMO", bars=bars, source_url="https://example.invalid/synthetic",
                   is_mock=True, retrieved_at=days[-1] + timedelta(minutes=1),
                   session_dates=tuple(stamp.date() for stamp in days) if calendar else ())


def with_pivots(dataset):
    bars = list(dataset.bars)
    bars[-11] = replace(bars[-11], low=103)
    bars[-8] = replace(bars[-8], high=108)
    return replace(dataset, bars=tuple(bars))


class DatasetTests(unittest.TestCase):
    def test_frozen_records_and_valid_snapshot(self):
        dataset = fixture()
        validate_dataset(dataset)
        with self.assertRaises(FrozenInstanceError):
            dataset.symbol = "OTHER"
        with self.assertRaises(FrozenInstanceError):
            dataset.bars[0].close = 1

    def test_strict_timezones_and_ohlcv(self):
        dataset = fixture(2)
        mutations = [replace(dataset.bars[0], timestamp=datetime(2025, 1, 6)),
                     replace(dataset.bars[0], available_at=dataset.bars[0].timestamp - timedelta(seconds=1)),
                     replace(dataset.bars[0], high=80), replace(dataset.bars[0], low=110),
                     replace(dataset.bars[0], close=float("nan")),
                     replace(dataset.bars[0], volume=-1), replace(dataset.bars[0], is_closed="true"),
                     replace(dataset.bars[0], session_open=dataset.bars[0].timestamp)]
        for invalid in mutations:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    validate_dataset(replace(dataset, bars=(invalid, dataset.bars[1])))
        with self.assertRaises(ValueError):
            parse_timestamp("2025-01-01T12:00:00")
        self.assertEqual(parse_timestamp("2025-01-01T12:00:00+08:00").hour, 4)

    def test_reject_duplicate_unsorted_and_calendar_mismatch(self):
        dataset = fixture(2)
        for bars in ((dataset.bars[0], dataset.bars[0]), tuple(reversed(dataset.bars))):
            with self.assertRaises(ValueError):
                validate_dataset(replace(dataset, bars=bars))
        with self.assertRaises(ValueError):
            validate_dataset(replace(dataset, session_dates=(dataset.session_dates[-1],)))

    def test_available_at_filters_delayed_bars(self):
        dataset = fixture(2)
        delayed = replace(dataset.bars[1], available_at=dataset.bars[1].timestamp + timedelta(days=2))
        dataset = replace(dataset, bars=(dataset.bars[0], delayed))
        self.assertEqual(len(as_of_slice(dataset, delayed.timestamp).bars), 1)
        self.assertEqual(len(as_of_slice(dataset, delayed.available_at).bars), 2)

    def write_csv(self, folder, dataset, *, add_open=False):
        csv_path, metadata_path = Path(folder) / "bars.csv", Path(folder) / "metadata.json"
        columns = list(CSV_COLUMNS) + (["session_open"] if add_open else [])
        with csv_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            for bar in dataset.bars:
                row = {key: getattr(bar, key) for key in columns}
                for key in ("timestamp", "available_at", "session_open"):
                    if key in row:
                        row[key] = row[key].isoformat()
                row["is_closed"] = "true" if bar.is_closed else "false"
                writer.writerow(row)
        metadata = {key: getattr(dataset, key) for key in
                    ("symbol", "market", "timeframe", "currency", "timezone", "adjustment", "source_url", "data_mode", "is_mock", "asset_type")}
        metadata["retrieved_at"] = dataset.retrieved_at.isoformat()
        metadata["session_dates"] = [value.isoformat() for value in dataset.session_dates]
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")
        return csv_path, metadata_path

    def test_csv_and_metadata_strict_round_trip(self):
        dataset = fixture(3)
        with tempfile.TemporaryDirectory() as folder:
            csv_path, metadata_path = self.write_csv(folder, dataset, add_open=True)
            self.assertEqual(load_dataset(csv_path, metadata_path), dataset)
            metadata = json.loads(metadata_path.read_text())
            for patch in ({"is_mock": "false"}, {"timezone": "wrong/timezone"}, {"source_url": ""},
                          {"data_mode": "live"}, {"unknown": 1}):
                metadata_path.write_text(json.dumps({**metadata, **patch}))
                with self.subTest(patch=patch):
                    with self.assertRaises(ValueError):
                        load_dataset(csv_path, metadata_path)
            metadata_path.write_text(json.dumps(metadata))
            csv_path.write_text(csv_path.read_text().replace(",true,", ",True,"))
            with self.assertRaises(ValueError):
                load_dataset(csv_path, metadata_path)

    def test_explicit_calendar_open_map(self):
        dataset = fixture(3)
        with tempfile.TemporaryDirectory() as folder:
            csv_path, metadata_path = self.write_csv(folder, dataset)
            metadata = json.loads(metadata_path.read_text())
            metadata["session_open_times"] = {bar.timestamp.date().isoformat(): bar.session_open.isoformat()
                                              for bar in dataset.bars}
            metadata_path.write_text(json.dumps(metadata))
            self.assertEqual(load_dataset(csv_path, metadata_path), dataset)
            metadata["session_open_times"][dataset.bars[0].timestamp.date().isoformat()] = dataset.bars[0].timestamp.isoformat()
            metadata_path.write_text(json.dumps(metadata))
            with self.assertRaises(ValueError):
                load_dataset(csv_path, metadata_path)


class StructureTests(unittest.TestCase):
    def test_wilder_atr_seed_and_smoothing(self):
        dataset = fixture(15)
        self.assertEqual(wilder_atr(dataset.bars[:13]), None)
        self.assertAlmostEqual(wilder_atr(dataset.bars[:14]), 2)
        changed = dataset.bars[:14] + (replace(dataset.bars[14], high=108, low=100),)
        self.assertAlmostEqual(wilder_atr(changed), (13 * 2 + 8) / 14)
        self.assertAlmostEqual(moving_average(dataset.bars, 5), sum(bar.close for bar in dataset.bars[-5:]) / 5)

    def test_confirmed_pivots_need_two_right_bars(self):
        dataset = with_pivots(fixture())
        highs, lows = confirmed_pivots(dataset.bars)
        self.assertEqual(highs[-1][1], 108)
        self.assertEqual(lows[-1][1], 103)
        last_pivot = replace(dataset.bars[-2], high=150)
        highs, _ = confirmed_pivots(dataset.bars[:-2] + (last_pivot, dataset.bars[-1]))
        self.assertNotIn(150, [value for _, value in highs])

    def test_parent_uses_only_fully_completed_declared_week(self):
        dataset = fixture()
        cutoff = dataset.bars[-2].available_at  # Thursday; Friday is declared but unavailable.
        weekly = completed_weekly_bars(as_of_slice(dataset, cutoff), cutoff)
        self.assertLess(parse_timestamp(weekly[-1]["timestamp"]), dataset.bars[-5].timestamp)
        no_calendar = analyze_structure(replace(dataset, session_dates=()))
        self.assertFalse(no_calendar["metrics"]["parent_week_confirmed"])
        self.assertEqual(no_calendar["state"], "No Trade")

    def test_missing_session_blocks_that_week(self):
        dataset = fixture()
        broken = replace(dataset, bars=dataset.bars[:-3] + dataset.bars[-2:])
        weekly = completed_weekly_bars(broken, dataset.bars[-1].available_at)
        self.assertNotEqual(weekly[-1]["timestamp"], dataset.bars[-1].timestamp.isoformat())

    def test_base_watch_breakout_pullback_breakdown_overheat(self):
        dataset = with_pivots(fixture())
        last = dataset.bars[-1]
        cases = [
            (fixture(), "Base Building"),
            (replace(dataset, bars=dataset.bars[:-1] + (replace(last, open=107.4, low=107, close=107.9, high=108.2),)), "Breakout Watch"),
            (replace(dataset, bars=dataset.bars[:-1] + (replace(last, open=108, low=107.9, close=109, high=109.5, volume=200),)), "Confirmed Breakout"),
            (replace(dataset, bars=dataset.bars[:-2] + (
                replace(dataset.bars[-2], open=108, low=107.9, close=109, high=109.5, volume=180),
                replace(last, open=108.2, low=108, close=108.8, high=109, volume=150))), "Pullback Entry Zone"),
            (replace(dataset, bars=dataset.bars[:-1] + (replace(last, open=103, low=101.8, close=102, high=103.5),)), "Breakdown"),
            (replace(dataset, bars=dataset.bars[:-1] + (replace(last, open=129, low=128, close=130, high=131, volume=200),)), "Exhaustion"),
        ]
        for snapshot, expected in cases:
            with self.subTest(expected=expected):
                result = analyze_structure(snapshot)
                self.assertEqual(result["state"], expected)
                self.assertTrue(result["metrics"]["parameters_experimental"])

    def test_partial_bar_and_insufficient_history_cannot_confirm(self):
        dataset = fixture()
        partial = replace(dataset, bars=dataset.bars[:-1] + (replace(dataset.bars[-1], is_closed=False),))
        result = analyze_structure(partial)
        self.assertFalse(result["closed_bar_confirmed"])
        self.assertFalse(result["metrics"]["breakout_confirmed"])
        self.assertEqual(result["state"], "No Trade")
        result = analyze_structure(fixture(10))
        self.assertEqual(result["state"], "No Trade")
        self.assertIsNone(result["metrics"]["ma50"])
        self.assertIsNone(result["metrics"]["atr"])

    def test_appending_future_prices_preserves_old_analysis(self):
        dataset = with_pivots(fixture())
        cutoff = dataset.bars[-1].available_at
        future_day = datetime.combine(dataset.session_dates[75], datetime.min.time(), timezone.utc).replace(hour=16)
        future = Bar(future_day, 500, 501, 499, 500, 9000, future_day + timedelta(minutes=1),
                     True, future_day.replace(hour=9))
        extended = replace(dataset, bars=dataset.bars + (future,))
        self.assertEqual(analyze_structure(dataset, cutoff), analyze_structure(extended, cutoff))

    def test_zero_volume_and_empty_data_do_not_fabricate_metrics(self):
        dataset = fixture()
        result = analyze_structure(replace(dataset, bars=tuple(replace(bar, volume=0) for bar in dataset.bars)))
        self.assertIsNone(result["metrics"]["volume_ratio"])
        self.assertFalse(result["metrics"]["breakout_confirmed"])
        result = analyze_structure(replace(dataset, bars=()))
        self.assertEqual(result["state"], "No Trade")
        self.assertIsNone(result["metrics"]["price"])

    def test_invalid_experimental_config_rejected(self):
        for config in ({"pivot_right": 0}, {"atr_period": True}, {"overheat_atr": float("inf")},
                       {"minimum_parent_weeks": 1}, {"ma_fast": 60}):
            with self.assertRaises(ValueError):
                StructureConfig(**config)


if __name__ == "__main__":
    unittest.main()
