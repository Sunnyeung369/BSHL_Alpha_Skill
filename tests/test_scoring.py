"""Regression cases for original import, invalid input and unsafe readiness bugs."""

import itertools
import unittest

from scoring import (AlphaThesisScorer, MarketPricingScorer, TradeReadinessScorer,
                     RiskGovernorScorer, PositionRiskScorer, BSHLAlphaScorer,
                     BSHLAlphaResult, BSHEAlphaScorer, CompleteScore,
                     TradeStatus, RiskDecision)


ALPHA = dict(demand_inflection=15, supply_chain_bottleneck=15,
             company_benefit_certainty=15, evidence_quality=15, catalyst_timing=10,
             valuation_mismatch=10, competition=10, contradiction_clarity=10)
PRICING = dict(sector_trend=15, relative_strength=15, capital_inflow=15,
               crowding=15, valuation_digestion=15, risk_appetite=15, catalyst_priced=10)
TRADE = dict(parent_cycle_direction=15, child_cycle_structure=15,
             breakout_confirmation=15, pullback_quality=10, volume_confirmation=10,
             stop_loss_clarity=15, reward_risk=15, volatility_controlled=5)
CONFIRMED = dict(closed_bar_confirmed=True, stop_loss_defined=True)
RISK = dict.fromkeys(RiskGovernorScorer.ITEMS, True)


class ScoringInputTests(unittest.TestCase):
    def test_public_api_and_compatibility_aliases(self):
        self.assertIs(BSHLAlphaScorer, BSHEAlphaScorer)
        self.assertIs(BSHLAlphaResult, CompleteScore)

    def test_all_score_fields_reject_invalid_numbers(self):
        for scorer, valid in ((AlphaThesisScorer(), ALPHA),
                              (MarketPricingScorer(), PRICING),
                              (TradeReadinessScorer(), TRADE)):
            for name in valid:
                for bad in (True, "10", None, -1, float("nan"), float("inf"),
                            -float("inf"), scorer.weights[name] + 1):
                    with self.subTest(scorer=type(scorer).__name__, name=name, bad=bad):
                        with self.assertRaises((ValueError, TypeError)):
                            scorer.score(**(valid | {name: bad}))

    def test_valid_score_boundaries(self):
        for scorer, valid in ((AlphaThesisScorer(), ALPHA),
                              (MarketPricingScorer(), PRICING),
                              (TradeReadinessScorer(), TRADE)):
            self.assertEqual(scorer.score(**valid).total, 100)
            self.assertEqual(scorer.score(**dict.fromkeys(valid, 0)).total, 0)


class RiskGateTests(unittest.TestCase):
    def setUp(self):
        self.scorer = RiskGovernorScorer()

    def test_empty_and_each_missing_check_never_pass(self):
        empty = self.scorer.check()
        self.assertEqual(empty.decision, RiskDecision.WAIT_CONFIRMATION)
        self.assertEqual(len(empty.missing_checks), 10)
        self.assertEqual(len(empty.checks), 10)
        for name in RISK:
            with self.subTest(name=name):
                self.assertEqual(self.scorer.check(**(RISK | {name: None})).decision,
                                 RiskDecision.WAIT_CONFIRMATION)

    def test_truthy_strings_and_numbers_are_not_booleans(self):
        for bad in ("False", "True", 0, 1, [], {}):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError):
                    self.scorer.check(**(RISK | {"liquidity": bad}))

    def test_every_boolean_combination_obeys_veto_and_pass_rules(self):
        names = list(RISK)
        for values in itertools.product((True, False), repeat=len(names)):
            checks = dict(zip(names, values))
            result = self.scorer.check(**checks)
            if not all(checks[name] for name in ("liquidity", "volatility", "stop_loss_distance", "regulatory_uncertainty")):
                self.assertEqual(result.decision, RiskDecision.VETO)
            elif all(values):
                self.assertEqual(result.decision, RiskDecision.PASS)
            else:
                self.assertNotEqual(result.decision, RiskDecision.PASS)

    def test_wait_dominates_crowding_reduce(self):
        result = self.scorer.check(**(RISK | {"social_crowding": False, "earnings_risk": False}))
        self.assertEqual(result.decision, RiskDecision.WAIT)

    def test_unknown_dominates_reduce_but_known_veto_still_wins(self):
        self.assertEqual(self.scorer.check(**(RISK | {"social_crowding": False, "correlation": None})).decision,
                         RiskDecision.WAIT_CONFIRMATION)
        self.assertEqual(self.scorer.check(liquidity=False).decision, RiskDecision.VETO)

    def test_unknown_details_rejected(self):
        with self.assertRaises(TypeError):
            self.scorer.check(**RISK, accidental_flag=True)


class TradeGateTests(unittest.TestCase):
    def setUp(self):
        self.scorer = TradeReadinessScorer()

    def test_full_scores_need_explicit_required_confirmations(self):
        self.assertEqual(self.scorer.score(**TRADE).status, TradeStatus.WAIT)
        for name in CONFIRMED:
            for value in (None, False):
                with self.subTest(name=name, value=value):
                    result = self.scorer.score(**TRADE, **(CONFIRMED | {name: value}))
                    self.assertNotEqual(result.status, TradeStatus.TRADE_READY)
        self.assertEqual(self.scorer.score(**TRADE, **CONFIRMED).status, TradeStatus.TRADE_READY)

    def test_zero_stop_and_breakout_cannot_be_compensated(self):
        no_stop = self.scorer.score(**(TRADE | {"stop_loss_clarity": 0}), **CONFIRMED)
        self.assertEqual(no_stop.total, 85)
        self.assertEqual(no_stop.status, TradeStatus.NO_TRADE)
        no_breakout = self.scorer.score(**(TRADE | {"breakout_confirmation": 0}), **CONFIRMED)
        self.assertEqual(no_breakout.total, 85)
        self.assertEqual(no_breakout.status, TradeStatus.WAIT)

    def test_confirmation_flags_must_be_bool(self):
        for name in CONFIRMED:
            with self.assertRaises(TypeError):
                self.scorer.score(**TRADE, **(CONFIRMED | {name: "True"}))


class CombinedScoreTests(unittest.TestCase):
    def setUp(self):
        self.scorer = BSHLAlphaScorer()
        self.alpha = AlphaThesisScorer().score(**ALPHA)
        self.pricing = MarketPricingScorer().score(**PRICING)
        self.trade = TradeReadinessScorer().score(**TRADE, **CONFIRMED)

    def status(self, risk, alpha=None, pricing=None, trade=None):
        return self.scorer._determine_final_status(alpha or self.alpha, pricing or self.pricing,
                                                 trade or self.trade, risk)

    def test_all_risk_decisions_have_safe_final_mapping(self):
        triggers = {RiskDecision.PASS: {}, RiskDecision.VETO: {"liquidity": False},
                    RiskDecision.WATCH_ONLY: {"evidence_quality": False},
                    RiskDecision.WAIT: {"earnings_risk": False},
                    RiskDecision.REDUCE_SIZE: {"correlation": False},
                    RiskDecision.WAIT_CONFIRMATION: {"correlation": None}}
        expected = {RiskDecision.PASS: "Trade Ready", RiskDecision.VETO: "Veto",
                    RiskDecision.WATCH_ONLY: "Research Only", RiskDecision.WAIT: "Wait Pullback",
                    RiskDecision.REDUCE_SIZE: "Watchlist", RiskDecision.WAIT_CONFIRMATION: "Watchlist"}
        for decision, changes in triggers.items():
            with self.subTest(decision=decision):
                risk = RiskGovernorScorer().check(**(RISK | changes))
                self.assertEqual(risk.decision, decision)
                self.assertEqual(self.status(risk), expected[decision])

    def test_low_thesis_or_weak_evidence_blocks_trade_ready(self):
        risk = RiskGovernorScorer().check(**RISK)
        zero = AlphaThesisScorer().score(**dict.fromkeys(ALPHA, 0))
        self.assertEqual(self.status(risk, alpha=zero), "Research Only")
        weak = AlphaThesisScorer().score(**(ALPHA | {"evidence_quality": 9}))
        self.assertEqual(self.status(risk, alpha=weak), "Research Only")

    def test_low_pricing_caps_status_at_watchlist(self):
        zero = MarketPricingScorer().score(**dict.fromkeys(PRICING, 0))
        self.assertEqual(self.status(RiskGovernorScorer().check(**RISK), pricing=zero), "Watchlist")

    def test_no_trade_maps_to_documented_final_avoid(self):
        no_stop = TradeReadinessScorer().score(**(TRADE | {"stop_loss_clarity": 0}), **CONFIRMED)
        self.assertEqual(self.status(RiskGovernorScorer().check(**RISK), trade=no_stop), "Avoid")

    def test_complete_public_entry_runs_without_import_bypass(self):
        risk_names = {"liquidity": "liquidity", "volatility": "volatility_ok", "evidence_quality": "evidence_ok",
                      "social_crowding": "social_ok", "earnings_risk": "earnings_ok",
                      "regulatory_uncertainty": "regulatory_ok", "price_location": "price_ok",
                      "stop_loss_distance": "stop_ok", "position_exposure": "position_ok", "correlation": "correlation_ok"}
        result = self.scorer.score_complete(ticker="DEMO", date="2026-10-03", **ALPHA, **PRICING,
                                           **TRADE, **CONFIRMED, **{risk_names[k]: v for k, v in RISK.items()})
        self.assertIsInstance(result, BSHLAlphaResult)
        self.assertEqual(result.final_status, "Trade Ready")


class PositionSizingTests(unittest.TestCase):
    def setUp(self):
        self.scorer = PositionRiskScorer()
        self.empty = dict(single_position_size=0, sector_concentration=0, total_exposure=0,
                          leverage_ratio=1, correlation_risk=10, liquidity_risk=10, total_capital=100000)

    def test_full_score_not_exposure_subscore_controls_cap(self):
        result = self.scorer.score(**self.empty, stop_loss_fraction=0.05)
        self.assertEqual(result.total, 100)
        self.assertEqual(result.recommended_max_size, 5000)
        self.assertEqual(result.recommended_additional_size, 5000)

    def test_unknown_stop_never_creates_new_position(self):
        result = self.scorer.score(**self.empty)
        self.assertEqual(result.recommended_max_size, 0)
        self.assertEqual(result.recommended_additional_size, 0)

    def test_stop_distance_and_risk_budget_limit_size(self):
        result = self.scorer.score(**self.empty, stop_loss_fraction=0.5)
        self.assertEqual(result.recommended_max_size, 2000)
        reduced = self.scorer.score(**self.empty, stop_loss_fraction=0.5, risk_budget_fraction=0.005)
        self.assertEqual(reduced.recommended_max_size, 1000)

    def test_remaining_exposure_and_existing_position_are_deducted(self):
        result = self.scorer.score(**(self.empty | dict(single_position_size=0.02,
                                                       sector_concentration=0.24, total_exposure=0.79)),
                                   current_position_size=2000, stop_loss_fraction=0.05)
        self.assertAlmostEqual(result.recommended_additional_size, 1000)
        self.assertAlmostEqual(result.recommended_max_size, 3000)

    def test_full_sector_has_no_room_for_addition(self):
        result = self.scorer.score(**(self.empty | dict(sector_concentration=0.25, total_exposure=0.25)),
                                   stop_loss_fraction=0.05)
        self.assertEqual(result.recommended_additional_size, 0)

    def test_liquidity_cap_and_leverage_block_new_allocation(self):
        result = self.scorer.score(**self.empty, stop_loss_fraction=0.05, liquidity_capital_limit=300)
        self.assertEqual(result.recommended_max_size, 300)
        leveraged = self.scorer.score(**(self.empty | {"leverage_ratio": 1.2}), stop_loss_fraction=0.05)
        self.assertEqual(leveraged.recommended_additional_size, 0)

    def test_negative_and_invalid_inputs_rejected(self):
        for name in self.empty:
            for bad in (True, -1, float("nan"), float("inf")):
                with self.subTest(name=name, bad=bad):
                    with self.assertRaises((ValueError, TypeError)):
                        self.scorer.score(**(self.empty | {name: bad}))
        for field in ("stop_loss_fraction", "current_position_size", "risk_budget_fraction", "liquidity_capital_limit"):
            with self.assertRaises((ValueError, TypeError)):
                self.scorer.score(**self.empty, **{field: -1})
        with self.assertRaises(ValueError):
            self.scorer.score(**self.empty, stop_loss_fraction=0)

    def test_exposures_must_include_existing_position(self):
        with self.assertRaises(ValueError):
            self.scorer.score(**(self.empty | {"single_position_size": 0.02}), stop_loss_fraction=0.05)

    def test_explicit_position_amount_must_agree_with_percentage(self):
        with self.assertRaises(ValueError):
            self.scorer.score(**(self.empty | dict(sector_concentration=0.1, total_exposure=0.1)),
                              current_position_size=2000, stop_loss_fraction=0.05)


if __name__ == "__main__":
    unittest.main()
