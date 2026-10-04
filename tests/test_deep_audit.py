"""Adversarial public-input cases discovered during the six-batch audit."""
import copy
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import replace
import io
import json
from pathlib import Path
import tempfile
import unittest

from bshl.engine import build_card
from bshl.cli import main
from bshl.backtest import BacktestConfig, run_backtest
from datetime import date, timedelta
from bshl.market import load_dataset, validate_dataset
from bshl.workspace import Workspace, canonical, digest, validate_card
from scoring.position_risk_score import PositionRiskScorer

ASSETS = Path(__file__).resolve().parents[1] / "bshl/assets"


def ready_fixture():
    # Explicitly exercises imported research semantics, not a real asset.
    dataset = load_dataset(ASSETS / "breakout.csv", ASSETS / "breakout.metadata.json")
    context = json.loads((ASSETS / "demo.context.json").read_text())
    dataset = replace(dataset, is_mock=False, data_mode="csv", exchange="NYSE")
    return dataset, build_card(dataset, context)


class CardAuditTests(unittest.TestCase):
    def test_missing_or_late_declared_session_blocks_otherwise_ready_card(self):
        dataset, good = ready_fixture()
        context = good["context"]
        missing_day = dataset.bars[-2].timestamp.date().isoformat()
        late = replace(dataset.bars[-2], available_at=dataset.bars[-1].available_at + timedelta(days=1))
        for bars in (dataset.bars[:-2] + dataset.bars[-1:], dataset.bars[:-2] + (late, dataset.bars[-1])):
            result = build_card(replace(dataset, bars=bars), context, dataset.bars[-1].available_at)
            self.assertNotEqual(result["final_status"], "Trade Ready")
            self.assertIn("declared_sessions_missing_or_unavailable", result["blockers"])
            self.assertIn(missing_day, result["technical_structure"]["metrics"]["missing_session_dates"])

    def test_simulation_rejects_missing_calendar_or_internal_daily_bar(self):
        dataset, _ = ready_fixture()
        config = BacktestConfig(train_end=date(2025, 4, 30), test_start=date(2025, 5, 1))
        for changed in (replace(dataset, session_dates=()),
                        replace(dataset, bars=dataset.bars[:-2] + dataset.bars[-1:])):
            with self.assertRaisesRegex(ValueError, "calendar|missing declared sessions"):
                run_backtest(changed, config)

    def test_missing_future_session_does_not_change_prior_cutoff_simulation(self):
        dataset, _ = ready_fixture()
        cutoff = dataset.bars[-3].timestamp
        config = BacktestConfig(train_end=date(2025, 4, 30), test_start=date(2025, 5, 1), end_date=cutoff)
        original = run_backtest(dataset, config)
        changed = replace(dataset, bars=dataset.bars[:-2] + dataset.bars[-1:])
        self.assertEqual(run_backtest(changed, config), original)

    def test_untouched_imported_card_is_accepted(self):
        _, card = ready_fixture()
        self.assertEqual(card["final_status"], "Trade Ready")
        self.assertEqual(validate_card(card), card)

    def test_conflicting_mock_mode_cannot_be_approved(self):
        _, card = ready_fixture()
        card["data_mode"] = "mock"
        with self.assertRaises(ValueError):
            validate_card(card)

    def test_context_changes_cannot_reuse_computed_evidence_or_risk(self):
        for field in ("evidence", "risk"):
            _, card = ready_fixture()
            if field == "evidence":
                card["context"]["evidence"][0]["available_at"] = "2026-01-01T00:00:00Z"
            else:
                card["context"]["risk_checks"]["regulatory_uncertainty"] = False
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_card(card)

    def test_inconsistent_stop_source_scores_and_price_rejected(self):
        for section, key, value in (("context", "stop_loss_price", 1),
                                    ("trade_readiness", "total", 100),
                                    ("alpha_thesis", "total", 99),
                                    ("source", "url", "file:///private")):
            _, card = ready_fixture()
            self.assertNotEqual(card[section].get(key), value)
            card[section][key] = value
            with self.subTest(section=section, key=key), self.assertRaises(ValueError):
                validate_card(card)
        _, card = ready_fixture()
        card["technical_structure"]["metrics"]["price"] += 1
        with self.assertRaises(ValueError):
            validate_card(card)

    def test_stale_imported_card_cannot_reuse_readiness(self):
        _, card = ready_fixture()
        card["as_of"] = "2025-06-01T20:00:00+00:00"
        with self.assertRaises(ValueError):
            validate_card(card)

    def test_dataset_strings_are_rejected_before_date_operations(self):
        dataset, _ = ready_fixture()
        bar = replace(dataset.bars[-1], timestamp=dataset.bars[-1].timestamp.isoformat())
        with self.assertRaises(ValueError):
            validate_dataset(replace(dataset, bars=dataset.bars[:-1] + (bar,)))

    def test_sector_cannot_exceed_total_portfolio_exposure(self):
        with self.assertRaises(ValueError):
            PositionRiskScorer().score(single_position_size=0, sector_concentration=.2,
                total_exposure=.1, leverage_ratio=1, correlation_risk=10,
                liquidity_risk=10, stop_loss_fraction=.05)

    def test_mock_csv_card_keeps_canonical_mock_labels(self):
        dataset, _ = ready_fixture()
        context = json.loads((ASSETS / "demo.context.json").read_text())
        card = build_card(replace(dataset, is_mock=True), context)
        self.assertEqual(card["data_mode"], "mock")
        self.assertEqual(card["final_status"], "Research Only")
        self.assertEqual(validate_card(card), card)

    def test_old_ready_card_requires_rebuilding_without_destroying_history(self):
        _, card = ready_fixture()
        card["rule_version"] = "readiness-0.6.2"
        with self.assertRaisesRegex(ValueError, "Rebuild"):
            validate_card(card)
        card["final_status"] = "Research Only"
        self.assertEqual(validate_card(card), card)

    def test_cli_accepts_windows_bom_and_rejects_duplicate_context_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "context.json"
            original = (ASSETS / "demo.context.json").read_text()
            path.write_text(original, encoding="utf-8-sig")
            args = ["analyze", "--csv", str(ASSETS / "breakout.csv"),
                    "--metadata", str(ASSETS / "breakout.metadata.json"), "--context", str(path),
                    "--output", str(Path(directory) / "good")]
            with redirect_stdout(io.StringIO()):
                self.assertEqual(main(args), 0)
            path.write_text('{"stop_loss_price": null, "stop_loss_price": 109}')
            args[-1] = str(Path(directory) / "bad")
            with redirect_stderr(io.StringIO()):
                self.assertEqual(main(args), 2)
            self.assertFalse(Path(args[-1]).exists())


class RecoveryAuditTests(unittest.TestCase):
    def test_resealed_current_approval_cannot_outlive_support(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory) / "approval.sqlite3")
            dataset, card = ready_fixture()
            context = copy.deepcopy(card["context"])
            context["evidence"][0]["expires_at"] = "2025-05-24T00:00:00Z"
            card = build_card(dataset, context)
            workspace.save(card)
            workspace.decide(card["analysis_id"], "approve_plan", "2025-05-23T21:00:00Z")
            bundle = workspace.export()
            row = bundle["tables"]["decisions"][0]
            payload = json.loads(row["payload"])
            payload["at"] = "2025-05-25T00:00:00+00:00"
            row["payload"] = canonical(payload)
            row["id"] = digest({"snapshot": row["snapshot_id"], **payload})
            bundle["checksum"] = digest(bundle["tables"])
            target = Path(directory) / "expired-approval.sqlite3"
            with self.assertRaises(ValueError):
                Workspace.restore(bundle, target)
            self.assertFalse(target.exists())

    def test_resealed_change_reason_must_match_original_cards(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory) / "changes.sqlite3")
            dataset, card = ready_fixture()
            workspace.save(card, watch=True)
            context = copy.deepcopy(card["context"])
            context.pop("stop_loss_price")
            workspace.save(build_card(dataset, context))
            bundle = workspace.export()
            row = bundle["tables"]["changes"][0]
            payload = json.loads(row["payload"])
            payload["reasons"] = ["prior_stop_invalidation_hit"]
            row["payload"], row["id"] = canonical(payload), digest(payload)
            bundle["checksum"] = digest(bundle["tables"])
            target = Path(directory) / "false-invalidation.sqlite3"
            with self.assertRaises(ValueError):
                Workspace.restore(bundle, target)
            self.assertFalse(target.exists())

    def test_calendar_urls_cannot_store_credentials_or_whitespace(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory) / "events.sqlite3")
            for url in ("https://user:password@example.org/source", "https://example.org/a b"):
                with self.subTest(url=url), self.assertRaises(ValueError):
                    workspace.schedule("DEMO", "Review", "2025-05-25T00:00:00Z", url)
            self.assertEqual(workspace.export()["tables"]["calendar"], [])

    def test_approval_requires_fresh_market_and_still_available_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = Workspace(Path(directory) / "approval.sqlite3")
            dataset, card = ready_fixture()
            context = copy.deepcopy(card["context"])
            context["evidence"][0]["expires_at"] = "2025-05-24T00:00:00Z"
            card = build_card(dataset, context)
            workspace.save(card)
            workspace.decide(card["analysis_id"], "approve_plan", "2025-05-23T21:00:00Z")
            for stamp in ("2025-05-24T00:00:00Z", "2025-06-01T00:00:00Z"):
                with self.subTest(stamp=stamp), self.assertRaises(ValueError):
                    workspace.decide(card["analysis_id"], "approve_plan", stamp)
            self.assertEqual(len(workspace.export()["tables"]["decisions"]), 1)

    def test_legacy_history_restores_but_cannot_be_newly_approved(self):
        with tempfile.TemporaryDirectory() as directory:
            workspace = self.prepare(directory)
            bundle = workspace.export()
            row = bundle["tables"]["snapshots"][0]
            old = json.loads(row["payload"])
            old["rule_version"] = "readiness-0.6.2"
            old["technical_structure"]["metrics"].pop("latest_bar_timestamp")
            old["technical_structure"]["metrics"].pop("latest_bar_volume")
            row["payload"], row["digest"] = canonical(old), digest(old)
            bundle["checksum"] = digest(bundle["tables"])
            restored = Workspace.restore(bundle, Path(directory) / "history.sqlite3")
            self.assertEqual(restored.snapshot(old["analysis_id"]), old)
            with self.assertRaisesRegex(ValueError, "Rebuild"):
                restored.decide(old["analysis_id"], "approve_plan", "2025-05-26T00:00:00Z")

    def prepare(self, directory):
        workspace = Workspace(Path(directory) / "source.sqlite3")
        _, card = ready_fixture()
        workspace.save(card, watch=True)
        review = workspace.review(card["analysis_id"], "unknown", "2025-05-25T00:00:00Z")
        candidate = workspace.propose({"rule_id": "structure.volume", "review_ids": [review], "comparison": {}})
        workspace.approve_candidate(candidate, "approve_for_holdout", "2025-05-26T00:00:00Z", "New holdout only")
        return workspace

    def test_resealed_candidate_approval_cannot_predate_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.prepare(directory).export()
            row = bundle["tables"]["candidate_decisions"][0]
            payload = json.loads(row["payload"])
            payload["at"] = "2025-01-01T00:00:00+00:00"
            row["payload"] = canonical(payload)
            row["id"] = digest({"candidate": row["candidate_id"], **payload})
            bundle["checksum"] = digest(bundle["tables"])
            target = Path(directory) / "invalid.sqlite3"
            with self.assertRaises(ValueError):
                Workspace.restore(bundle, target)
            self.assertFalse(target.exists())

    def test_resealed_candidate_sample_count_is_recomputed(self):
        with tempfile.TemporaryDirectory() as directory:
            bundle = self.prepare(directory).export()
            row = bundle["tables"]["candidates"][0]
            payload = json.loads(row["payload"])
            payload["unique_decision_count"] = 9999
            payload["evidence_status"] = "requires_independent_holdout"
            row["payload"] = canonical(payload)
            row["id"] = digest(payload)
            for decision in bundle["tables"]["candidate_decisions"]:
                decision["candidate_id"] = row["id"]
                decision["id"] = digest({"candidate": row["id"], **json.loads(decision["payload"])})
            bundle["checksum"] = digest(bundle["tables"])
            target = Path(directory) / "inflated.sqlite3"
            with self.assertRaises(ValueError):
                Workspace.restore(bundle, target)
            self.assertFalse(target.exists())


if __name__ == "__main__":
    unittest.main()
