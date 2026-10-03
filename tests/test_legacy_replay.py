"""Regression checks for audited legacy replay/history defects; no user data."""
import json
from dataclasses import replace
from datetime import date, datetime, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from replay import (PersonalEvolutionEngine, PersonalDecision, DecisionType,
    DecisionOutcome, ReplayCaseLibrary, ReplayEngine, ReplayConfig, RuleValidator,
    RuleTester, Portfolio)


def decision(identifier, rules=None):
    return PersonalDecision(identifier, datetime(2025, 1, 1, tzinfo=timezone.utc),
        "TEST", "US_STOCK", 80, 50, 80, "Pass", "Trade Ready", DecisionType.TRADE,
        "offline test", DecisionOutcome.LOSS, rules_to_adjust=rules or [])


class PersonalHistoryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name)
        self.engine = PersonalEvolutionEngine("test_user", self.path)

    def test_first_run_has_complete_insights_without_fabricated_success_rate(self):
        report = self.engine.evolve()
        self.assertEqual(report["insights"]["summary"]["total_decisions"], 0)
        self.assertIsNone(report["insights"]["summary"]["success_rate"])

    def test_unsafe_user_ids_rejected_before_storage_creation(self):
        for user_id in ("../escape", "a/b", "a\\b", "C:\\escape", "", "CON", ".."):
            with self.subTest(user_id=user_id), self.assertRaises(ValueError):
                PersonalEvolutionEngine(user_id, self.path / "must_not_exist")
        self.assertFalse((self.path / "must_not_exist").exists())

    def test_duplicate_decision_does_not_update_history_or_rule_counts(self):
        item = decision("one", ["RISK_VETO_OVERRIDE"])
        self.engine.record_decision(item)
        with self.assertRaises(ValueError):
            self.engine.record_decision(item)
        self.assertEqual(len(self.engine.decisions), 1)
        self.assertEqual(self.engine.rules["RISK_VETO_OVERRIDE"].failure_count, 1)

    def test_reloaded_dates_can_be_saved(self):
        self.engine.record_decision(decision("one", ["RISK_VETO_OVERRIDE"]))
        reloaded = PersonalEvolutionEngine("test_user", self.path)
        self.assertIsInstance(reloaded.rules["RISK_VETO_OVERRIDE"].last_applied, datetime)
        reloaded._save_rules()
        reloaded.record_decision(decision("two", ["RISK_VETO_OVERRIDE"]))
        self.assertEqual(len(PersonalEvolutionEngine("test_user", self.path).decisions), 2)

    def test_atomic_replace_failure_preserves_disk_and_rolls_back_memory(self):
        self.engine.record_decision(decision("one"))
        prior = (self.path / "state.json").read_bytes()
        with patch("replay.personal_evolution.os.replace", side_effect=OSError("blocked")):
            with self.assertRaises(OSError):
                self.engine.record_decision(decision("two", ["TIMING_PULLBACK"]))
        self.assertEqual((self.path / "state.json").read_bytes(), prior)
        self.assertEqual(len(self.engine.decisions), 1)
        self.assertEqual(self.engine.rules["TIMING_PULLBACK"].failure_count, 0)
        self.assertEqual(list(self.path.glob(".state-*.tmp")), [])

    def test_losses_cannot_disable_or_lower_hard_gates(self):
        initial = self.engine.get_adjusted_weights()
        for i in range(6):
            self.engine.record_decision(decision(str(i), list(self.engine.PROTECTED_RULES)))
        for rule_id in self.engine.PROTECTED_RULES:
            self.assertTrue(self.engine.rules[rule_id].enabled)
            self.assertEqual(self.engine.get_adjusted_weights()[rule_id], initial[rule_id])
        self.assertEqual(self.engine.candidates, [])

    def test_ordinary_rules_require_explicit_review_before_weight_change(self):
        for i in range(5):
            self.engine.record_decision(decision(str(i), ["TIMING_PULLBACK"]))
        self.assertEqual(self.engine.rules["TIMING_PULLBACK"].weight, 0.8)
        candidate = self.engine.candidates[0]
        with self.assertRaises(ValueError):
            self.engine.accept_candidate(candidate["id"], reviewer="", rationale="r",
                validation_reference="validation.json", weight=0.6)
        review = self.engine.accept_candidate(candidate["id"], reviewer="human", rationale="costs reviewed",
            validation_reference="out-of-sample/report.json", weight=0.6)
        self.assertEqual(review["status"], "accepted")
        self.assertEqual(review["before"]["weight"], 0.8)
        self.assertEqual(PersonalEvolutionEngine("test_user", self.path).rules["TIMING_PULLBACK"].weight, 0.6)

    def test_legacy_dates_migrate_and_disabled_veto_is_restored(self):
        payload = {"RISK_VETO_OVERRIDE": {"id": "RISK_VETO_OVERRIDE", "description": "veto",
            "category": "risk", "enabled": False, "last_applied": "2025-01-01T00:00:00+00:00"}}
        (self.path / "rules.json").write_text(json.dumps(payload), encoding="utf-8")
        restored = PersonalEvolutionEngine("test_user", self.path)
        self.assertTrue(restored.rules["RISK_VETO_OVERRIDE"].enabled)
        restored._save_rules()
        self.assertTrue((self.path / "state.json").exists())
        self.assertTrue((self.path / "rules.json").exists())


class LegacyReplayTests(unittest.TestCase):
    def setUp(self):
        self.library = ReplayCaseLibrary()
        self.base = self.library.get_all_cases()[0]

    def engine(self, end=date(2025, 12, 31)):
        return ReplayEngine(ReplayConfig(date(2025, 1, 1), end, ["*"], 100000), self.library)

    def test_future_outcome_cannot_value_portfolio_or_success_statistics(self):
        self.library.cases = {"future": replace(self.base, id="future",
            original_date=date(2025, 1, 1), outcome_date=date(2035, 1, 1), outcome_price=999999)}
        report = self.engine(date(2025, 1, 2)).replay()
        self.assertIsNone(report["performance"]["final_value"])
        self.assertIsNone(report["performance"]["total_return"])
        self.assertEqual(report["performance"]["valuation_status"], "unknown")
        self.assertIsNone(report["log"][0]["outcome_price"])
        self.assertIsNone(report["trades"]["success_rate"])

    def test_repeated_run_is_deterministic_and_explicitly_illustrative(self):
        engine = self.engine()
        first = engine.replay()
        self.assertEqual(first, engine.replay())
        self.assertFalse(first["performance_validated"])
        self.assertEqual(first["mode"], "legacy_case_snapshot_simulation")

    def test_latest_observed_outcome_chosen_by_outcome_date(self):
        earlier = replace(self.base, id="early", original_date=date(2025, 1, 1),
            outcome_date=date(2025, 10, 1), outcome_price=1000)
        later = replace(self.base, id="later", original_date=date(2025, 2, 1),
            outcome_date=date(2025, 4, 1), outcome_price=100)
        self.library.cases = {"early": earlier, "later": later}
        report = self.engine().replay()
        self.assertEqual(report["performance"]["valuation_dates"][self.base.symbol], "2025-10-01")

    def test_missing_price_and_invalid_capital_fail_explicitly(self):
        with self.assertRaises(ValueError):
            Portfolio(1, {"TEST": 1}, []).get_value({})
        with self.assertRaises(ValueError):
            ReplayConfig(date(2025, 1, 1), date(2025, 1, 2), ["*"], 0)

    def test_rule_matching_uses_explicit_ids_and_small_samples_are_insufficient(self):
        validator = RuleValidator(self.library)
        matched = validator.validate_rule("PRICING_CROWDED_SKIP", "pricing", lambda s: True)
        self.assertEqual(matched["cases_tested"], 1)
        self.assertEqual(matched["status"], "insufficient")
        self.assertIsNone(matched["valid"])
        self.assertEqual(validator.validate_rule("UNRELATED", "", lambda s: True)["cases_tested"], 0)

    def test_rule_callbacks_cannot_read_outcomes_or_post_hoc_titles(self):
        def no_leak(snapshot):
            for name in ("outcome", "outcome_price", "price_change_percent", "failure_reasons", "title"):
                self.assertFalse(hasattr(snapshot, name))
            return snapshot.market_pricing_score > 85
        self.assertEqual(RuleTester(self.library).test_rule(no_leak)["passed"], 1)
        with self.assertRaises(AttributeError):
            RuleTester(self.library).test_rule(lambda snapshot: snapshot.outcome_price > 0)

    def test_even_large_label_samples_do_not_prove_validity(self):
        self.library.cases = {str(i): replace(self.base, id=str(i)) for i in range(30)}
        report = RuleValidator(self.library).validate_rule("PRICING_CROWDED_SKIP", "", lambda s: True)
        self.assertEqual(report["status"], "diagnostic_only")
        self.assertIsNone(report["valid"])


if __name__ == "__main__":
    unittest.main()
