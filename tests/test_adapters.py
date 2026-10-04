from dataclasses import replace
from pathlib import Path
import unittest
from bshl.adapters import CSVSnapshotAdapter, validated_snapshot
from bshl.engine import build_card
from test_engine import fixture

ASSETS = Path(__file__).resolve().parents[1] / "bshl/assets"


class FrozenAdapter:
    def __init__(self, dataset):
        self.dataset = dataset

    def snapshot(self, symbol, as_of):
        return self.dataset


class AdapterBoundaryTests(unittest.TestCase):
    def test_csv_requires_explicit_mock_and_slices_availability(self):
        adapter = CSVSnapshotAdapter(str(ASSETS / "breakout.csv"), str(ASSETS / "breakout.metadata.json"))
        with self.assertRaises(ValueError):
            validated_snapshot(adapter, "DEMO", "2025-05-22T20:00:00Z")
        dataset = validated_snapshot(adapter, "DEMO", "2025-05-22T20:00:00Z", allow_mock=True)
        self.assertEqual(len(dataset.bars), 99)

    def test_provider_failure_never_becomes_mock_success(self):
        class Unavailable:
            def snapshot(self, symbol, as_of):
                raise TimeoutError("provider unavailable")
        with self.assertRaises(TimeoutError):
            validated_snapshot(Unavailable(), "DEMO", "2025-05-23T20:00:00Z", allow_mock=True)

    def test_wrong_symbol_and_empty_cutoff_fail(self):
        dataset, _ = fixture()
        with self.assertRaises(ValueError):
            validated_snapshot(FrozenAdapter(dataset), "OTHER", dataset.bars[-1].available_at, allow_mock=True)
        with self.assertRaises(ValueError):
            validated_snapshot(FrozenAdapter(dataset), "DEMO", "2024-01-01T00:00:00Z", allow_mock=True)

    def test_unvalidated_market_profile_unknown_exchange_and_stale_data_block_ready(self):
        dataset, context = fixture()
        dataset = replace(dataset, data_mode="csv", is_mock=False, exchange="NYSE")
        stale = build_card(dataset, context, "2025-06-01T00:00:00Z")
        self.assertNotEqual(stale["final_status"], "Trade Ready")
        self.assertIn("market_data_stale_over_4_days", stale["blockers"])
        unknown = build_card(replace(dataset, exchange="UNKNOWN"), context)
        self.assertNotEqual(unknown["final_status"], "Trade Ready")
        unsupported = build_card(replace(dataset, market="HK", asset_type="HK_STOCK", currency="HKD"), context)
        self.assertEqual(unsupported["final_status"], "Research Only")

    def test_measured_illiquidity_and_context_typo_cannot_pass(self):
        dataset, context = fixture()
        last = replace(dataset.bars[-1], volume=1)
        illiquid = build_card(replace(dataset, bars=(*dataset.bars[:-1], last)), context)
        checks = {item["name"]: item["status"] for item in illiquid["risk_governor"]["checks"]}
        self.assertFalse(checks["liquidity"])
        with self.assertRaises(ValueError):
            build_card(dataset, context | {"stop_los_price": 120})
