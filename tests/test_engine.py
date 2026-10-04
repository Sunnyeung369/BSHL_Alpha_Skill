import copy
from dataclasses import replace
import json
from pathlib import Path
import unittest

from bshl.engine import build_card
from bshl.market import load_dataset

ROOT = Path(__file__).resolve().parents[1]


def fixture(scenario="breakout"):
    assets = ROOT / "bshl/assets"
    return (load_dataset(assets / (scenario + ".csv"), assets / (scenario + ".metadata.json")),
            json.loads((assets / "demo.context.json").read_text(encoding="utf-8")))


class EngineTests(unittest.TestCase):
    def test_deterministic_mock_breakout_has_separate_simulation_state(self):
        dataset, context = fixture()
        card = build_card(dataset, context)
        self.assertEqual(card, build_card(dataset, context))
        self.assertEqual(card["technical_structure"]["state"], "Confirmed Breakout")
        self.assertEqual(card["simulation_status"], "Trade Ready")
        self.assertEqual(card["final_status"], "Research Only")
        self.assertIn("mock_data_research_only", card["blockers"])

    def test_no_selected_stop_is_never_filled_by_suggested_stop(self):
        dataset, context = fixture()
        context.pop("stop_loss_price")
        card = build_card(dataset, context)
        self.assertIsNotNone(card["technical_structure"]["suggested_stop"])
        self.assertIsNone(card["trade_plan"]["stop_loss_price"])
        self.assertNotEqual(card["simulation_status"], "Trade Ready")

    def test_measured_overheat_and_distant_stop_tighten_manual_risk(self):
        dataset, context = fixture("overheated")
        card = build_card(dataset, context)
        checks = {item["name"]: item["status"] for item in card["risk_governor"]["checks"]}
        self.assertFalse(checks["price_location"])
        self.assertFalse(checks["stop_loss_distance"])
        self.assertNotEqual(card["simulation_status"], "Trade Ready")

    def test_unknown_risk_and_missing_scores_remain_blocked(self):
        dataset, context = fixture()
        context["risk_checks"].pop("correlation")
        card = build_card(dataset, context)
        self.assertIn("correlation", card["risk_governor"]["missing_checks"])
        self.assertNotEqual(card["simulation_status"], "Trade Ready")
        context.pop("alpha_scores")
        self.assertEqual(build_card(dataset, context)["simulation_status"], "Research Only")

    def test_future_and_expired_evidence_cannot_support_or_veto_decision(self):
        dataset, context = fixture()
        evidence = context["evidence"][0]
        evidence.update(published_at="2026-01-01T00:00:00Z", available_at="2026-01-01T00:00:00Z", kill_switch=True)
        card = build_card(dataset, context)
        self.assertEqual(card["evidence"]["strong_support_count"], 0)
        self.assertEqual(card["evidence"]["active_kill_switch_count"], 0)
        self.assertEqual(card["simulation_status"], "Research Only")
        evidence.update(published_at="2025-01-01T00:00:00Z", available_at="2025-01-01T00:00:00Z", expires_at="2025-02-01T00:00:00Z")
        self.assertFalse(build_card(dataset, context)["evidence"]["audit"][0]["available"])

    def test_available_kill_switch_overrides_all_scores(self):
        dataset, context = fixture()
        context["evidence"][0]["kill_switch"] = True
        card = build_card(dataset, context)
        self.assertEqual(card["simulation_status"], "Veto")
        self.assertEqual(card["risk_governor"]["decision"], "Veto")

    def test_strict_context_values_and_evidence_times(self):
        dataset, context = fixture()
        for invalid in (True, "121", float("nan"), float("inf"), 0):
            changed = copy.deepcopy(context)
            changed["stop_loss_price"] = invalid
            with self.assertRaises((ValueError, TypeError)):
                build_card(dataset, changed)
        context["evidence"][0]["available_at"] = "2024-01-01T00:00:00Z"
        with self.assertRaises(ValueError):
            build_card(dataset, context)

    def test_duplicate_evidence_identity_rejected(self):
        dataset, context = fixture()
        context["evidence"].append(copy.deepcopy(context["evidence"][0]))
        with self.assertRaises(ValueError):
            build_card(dataset, context)

    def test_future_bar_change_does_not_repaint_visible_structure(self):
        dataset, context = fixture()
        cutoff = dataset.bars[-2].available_at
        changed = replace(dataset, bars=(*dataset.bars[:-1], replace(dataset.bars[-1], high=1000, close=999)))
        self.assertEqual(build_card(dataset, context, cutoff), build_card(changed, context, cutoff))

    def test_schema_accepts_output_and_rejects_tampered_readiness(self):
        try:
            from jsonschema import Draft7Validator, FormatChecker
        except ImportError:
            self.skipTest("Install .[dev] for schema acceptance")
        validator = Draft7Validator(json.loads((ROOT / "schemas/research_card.schema.json").read_text()), format_checker=FormatChecker())
        dataset, context = fixture()
        mock = build_card(dataset, context)
        validator.validate(mock)
        # Exercises the non-mock code path; this fixture is not live market evidence.
        ready = build_card(replace(dataset, is_mock=False, data_mode="csv", exchange="NYSE"), context)
        self.assertEqual(ready["final_status"], "Trade Ready")
        validator.validate(ready)
        for section, key, value in (("risk_governor", "decision", "Wait"),
                                    ("trade_plan", "stop_loss_price", None),
                                    ("trade_readiness", "closed_bar_confirmed", False)):
            changed = copy.deepcopy(ready)
            changed[section][key] = value
            self.assertTrue(list(validator.iter_errors(changed)))
        changed = copy.deepcopy(mock)
        changed["final_status"] = "Trade Ready"
        self.assertTrue(list(validator.iter_errors(changed)))
        changed = copy.deepcopy(ready)
        changed["risk_governor"]["checks"] = [changed["risk_governor"]["checks"][0]] * 10
        self.assertTrue(list(validator.iter_errors(changed)))

    def test_pullback_rebound_produces_pullback_entry_zone(self):
        dataset, context = fixture("pullback")
        card = build_card(dataset, context)
        self.assertEqual(card["technical_structure"]["state"], "Pullback Entry Zone")
        self.assertTrue(card["technical_structure"]["metrics"]["pullback_confirmed"])
        self.assertEqual(card["simulation_status"], "Trade Ready")
        self.assertEqual(card["final_status"], "Research Only")
        self.assertIn("mock_data_research_only", card["blockers"])
        # Deterministic: recomputing produces the same analysis_id.
        self.assertEqual(card, build_card(dataset, context))

    def test_breakdown_cannot_become_trade_ready(self):
        dataset, context = fixture("breakdown")
        card = build_card(dataset, context)
        self.assertEqual(card["technical_structure"]["state"], "Breakdown")
        self.assertTrue(card["technical_structure"]["metrics"]["breakdown"])
        self.assertEqual(card["final_status"], "Research Only")
        self.assertNotEqual(card["simulation_status"], "Trade Ready")
        self.assertIn("structure_not_confirmed", card["blockers"])
        self.assertIn("mock_data_research_only", card["blockers"])
        # Even with non-mock data, Breakdown state blocks Trade Ready.
        live = replace(dataset, is_mock=False, data_mode="csv", exchange="NYSE")
        live_card = build_card(live, context)
        self.assertNotEqual(live_card["final_status"], "Trade Ready")
        self.assertIn("structure_not_confirmed", live_card["blockers"])
