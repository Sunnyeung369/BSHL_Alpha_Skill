import copy
from contextlib import redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from bshl.cli import main
from bshl.engine import build_card
from bshl.market import load_dataset
from bshl.portfolio import size_plan
from bshl.workspace import Workspace, digest

ASSETS = Path(__file__).resolve().parents[1] / "bshl/assets"


def card(context_change=None, as_of=None):
    dataset = load_dataset(ASSETS / "breakout.csv", ASSETS / "breakout.metadata.json")
    context = json.loads((ASSETS / "demo.context.json").read_text())
    context.update(context_change or {})
    return build_card(dataset, context, as_of)


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.path = Path(self.temp.name) / "work.sqlite3"
        self.workspace = Workspace(self.path)
        self.card = card()

    def tearDown(self):
        self.temp.cleanup()

    def test_save_restart_and_collision_preserve_original(self):
        self.workspace.save(self.card, watch=True, conditions=["Review after earnings"])
        self.workspace.save(self.card, watch=True)
        self.assertEqual(Workspace(self.path).snapshot(self.card["analysis_id"]), self.card)
        collision = copy.deepcopy(self.card)
        collision["context"]["target_price"] += 1
        with self.assertRaises(ValueError):
            self.workspace.save(collision)
        self.assertEqual(len(self.workspace.export()["tables"]["snapshots"]), 1)

    def test_database_protects_immutable_snapshot(self):
        self.workspace.save(self.card)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.workspace.connect() as db:
                db.execute("UPDATE snapshots SET payload='{}'")
        self.assertEqual(self.workspace.snapshot(self.card["analysis_id"]), self.card)

    def test_watchlist_reassessment_reports_reasons(self):
        self.workspace.save(self.card, watch=True)
        changed = card({"stop_loss_price": None})
        result = self.workspace.save(changed)
        self.assertIn("blockers_changed", result["changes"])
        status = self.workspace.status("2025-05-24T00:00:00Z")
        self.assertEqual(status["watchlist"][0]["snapshot_id"], changed["analysis_id"])
        self.assertFalse(status["automatic_monitoring"])
        self.assertEqual(status["changes"][0]["before"], self.card["analysis_id"])

    def test_stale_reassessment_is_transactionally_rejected(self):
        self.workspace.save(self.card, watch=True)
        older = card(as_of="2025-05-22T20:00:00Z")
        with self.assertRaises(ValueError):
            self.workspace.save(older)
        self.assertEqual(len(self.workspace.export()["tables"]["snapshots"]), 1)

    def test_decision_does_not_promote_or_trade_mock(self):
        self.workspace.save(self.card)
        with self.assertRaises(ValueError):
            self.workspace.decide(self.card["analysis_id"], "approve_plan", "2025-05-24T00:00:00Z")
        record = self.workspace.decide(self.card["analysis_id"], "wait", "2025-05-24T00:00:00Z")
        self.assertEqual(record, self.workspace.decide(self.card["analysis_id"], "wait", "2025-05-24T00:00:00Z"))
        self.assertEqual(self.workspace.snapshot(self.card["analysis_id"]), self.card)

    def test_review_requires_visible_time_and_signed_returns(self):
        self.workspace.save(self.card)
        for outcome, at, r in (("profit", "2025-05-01T00:00:00Z", 1),
                               ("profit", "2025-05-24T00:00:00Z", -1),
                               ("loss", "2025-05-24T00:00:00Z", 1),
                               ("no_trade", "2025-05-24T00:00:00Z", 1)):
            with self.assertRaises(ValueError):
                self.workspace.review(self.card["analysis_id"], outcome, at, realized_r=r)
        record = self.workspace.review(self.card["analysis_id"], "no_trade", "2025-05-24T00:00:00Z", note="Missed rally is not proof that risk gates failed")
        self.assertEqual(record, self.workspace.review(self.card["analysis_id"], "no_trade", "2025-05-24T00:00:00Z", note="Missed rally is not proof that risk gates failed"))

    def test_export_restore_round_trip_preserves_all_records(self):
        self.workspace.save(self.card, watch=True, conditions=["Invalidation at selected stop"])
        self.workspace.decide(self.card["analysis_id"], "wait", "2025-05-24T00:00:00Z")
        review = self.workspace.review(self.card["analysis_id"], "unknown", "2025-05-24T00:00:00Z")
        self.workspace.schedule("DEMO", "Fictional earnings date", "2025-06-01T12:00:00Z", "https://example.invalid/fixture")
        candidate = self.workspace.propose({"rule_id": "structure.breakout_volume", "comparison": {"sample_count": 1, "evidence_status": "insufficient"}, "review_ids": [review]})
        self.workspace.approve_candidate(candidate, "approve_for_holdout", "2025-05-25T00:00:00Z", "Needs new data; do not deploy")
        bundle = self.workspace.export()
        restored = Workspace.restore(bundle, Path(self.temp.name) / "restored.sqlite3")
        self.assertEqual(restored.export(), bundle)
        with self.assertRaises(FileExistsError):
            Workspace.restore(bundle, restored.path)
        self.assertEqual(restored.export(), bundle)

    def test_corrupt_or_broken_reference_restore_leaves_no_target(self):
        self.workspace.save(self.card, watch=True)
        bundle = self.workspace.export()
        target = Path(self.temp.name) / "bad.sqlite3"
        bundle["tables"]["snapshots"][0]["payload"] = "{}"
        with self.assertRaises(ValueError):
            Workspace.restore(bundle, target)
        self.assertFalse(target.exists())
        bundle = self.workspace.export()
        bundle["tables"]["watchlist"][0]["snapshot_id"] = "unknown"
        bundle["checksum"] = digest(bundle["tables"])
        with self.assertRaises(sqlite3.IntegrityError):
            Workspace.restore(bundle, target)
        self.assertFalse(target.exists())

    def test_hard_gate_candidate_and_missing_reviews_rejected(self):
        for rule_id in ("risk.veto", "hard.stop", "RISK_VETO_OVERRIDE"):
            with self.assertRaises(ValueError):
                self.workspace.propose({"rule_id": rule_id, "comparison": {}, "review_ids": ["unknown"]})
        with self.assertRaises(ValueError):
            self.workspace.propose({"rule_id": "structure.volume", "comparison": {}, "review_ids": ["unknown"]})

    def test_candidate_counts_decisions_and_preserves_holdout_boundary(self):
        self.workspace.save(self.card)
        review = self.workspace.review(self.card["analysis_id"], "unknown", "2025-05-24T00:00:00Z")
        candidate = self.workspace.propose({"rule_id": "structure.volume", "comparison": {"sample_count": 9999}, "review_ids": [review, review]})
        payload = json.loads(self.workspace.export()["tables"]["candidates"][0]["payload"])
        self.assertEqual(payload["unique_decision_count"], 1)
        self.assertEqual(payload["evidence_status"], "insufficient")
        with self.assertRaises(ValueError):
            self.workspace.approve_candidate(candidate, "approve_for_holdout", "2025-05-23T00:00:00Z", "Too early")

    def test_forged_export_cannot_record_mock_approval(self):
        self.workspace.save(self.card)
        self.workspace.decide(self.card["analysis_id"], "wait", "2025-05-24T00:00:00Z")
        bundle = self.workspace.export()
        row = bundle["tables"]["decisions"][0]
        payload = json.loads(row["payload"])
        payload["choice"] = "approve_plan"
        row["payload"] = json.dumps(payload)
        row["id"] = digest({"snapshot": row["snapshot_id"], **payload})
        bundle["checksum"] = digest(bundle["tables"])
        with self.assertRaises(ValueError):
            Workspace.restore(bundle, Path(self.temp.name) / "forged.sqlite3")

    def test_calendar_requires_source_and_filters_future_due_dates(self):
        self.workspace.schedule("DEMO", "Earnings", "2025-06-01T12:00:00Z", "https://example.invalid/fixture")
        self.assertEqual(self.workspace.status("2025-05-24T00:00:00Z")["events_due_for_review"], [])
        self.assertEqual(len(self.workspace.status("2025-06-02T00:00:00Z")["events_due_for_review"]), 1)
        with self.assertRaises(ValueError):
            self.workspace.schedule("DEMO", "Unknown", "2025-06-01T12:00:00Z", "missing")

    def test_cli_full_round_trip(self):
        source = Path(self.temp.name) / "card.json"
        source.write_text(json.dumps(self.card))
        bundle = Path(self.temp.name) / "export.json"
        target = Path(self.temp.name) / "cli-restored.sqlite3"
        with redirect_stdout(io.StringIO()):
            self.assertEqual(main(["journal", "--db", str(self.path), "save", "--card", str(source), "--watch"]), 0)
            self.assertEqual(main(["journal", "--db", str(self.path), "review", "--id", self.card["analysis_id"], "--outcome", "no_trade", "--at", "2025-05-24T00:00:00Z"]), 0)
            self.assertEqual(main(["journal", "--db", str(self.path), "export", "--output", str(bundle)]), 0)
            self.assertEqual(main(["journal", "restore", "--input", str(bundle), "--target", str(target)]), 0)
        self.assertEqual(Workspace(target).export(), self.workspace.export())

    def test_sizing_is_gated_and_currency_checked(self):
        account = dict(currency="USD", single_position_size=0, sector_concentration=0, total_exposure=0,
                       leverage_ratio=1, correlation_risk=10, liquidity_risk=10, total_capital=100000)
        result = size_plan(self.card, account)
        self.assertEqual(result["permitted_research_increment"], 0)
        self.assertEqual(result["whole_share_cap"], 0)
        with self.assertRaises(ValueError):
            size_plan(self.card, account | {"currency": "HKD"})
