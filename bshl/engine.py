"""Point-in-time research cards. No order placement or return predictions."""

from dataclasses import asdict
from hashlib import sha256
import json
from urllib.parse import urlparse

from scoring import (AlphaThesisScorer, MarketPricingScorer, TradeReadinessScorer,
                     RiskGovernorScorer, BSHLAlphaScorer, RiskDecision)
from scoring.risk_governor_score import RiskCheckItem
from scoring.validation import number, optional_bool
from .market import as_of_slice, parse_timestamp, validate_dataset
from .serialization import to_jsonable
from .structure import analyze_structure


RULE_VERSION = "readiness-0.6.4"
SCHEMA_VERSION = "1.0"
STRONG_SOURCE_TYPES = {"filing", "transcript", "company_release", "industry_report"}
READY_STRUCTURES = {"Confirmed Breakout", "Pullback Entry Zone"}


def _url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return (parsed.scheme in ("https", "http") and bool(parsed.hostname)
            and parsed.username is None and parsed.password is None and not any(ch.isspace() for ch in value))


def _score(scorer, supplied, name):
    if supplied is None:
        return None
    if not isinstance(supplied, dict):
        raise TypeError(f"{name} must be an object")
    if set(supplied) != set(scorer.weights):
        raise ValueError(f"{name} must contain exactly {sorted(scorer.weights)}")
    return scorer.score(**supplied)


def _evidence_at(evidence, decision_time):
    """Keep the original index and explain availability, without verifying a URL."""
    if not isinstance(evidence, list):
        raise TypeError("evidence must be a list")
    audit, strong_count, kill_count = [], 0, 0
    seen_ids = set()
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise TypeError(f"evidence[{index}] must be an object")
        if "id" in item and (not isinstance(item["id"], str) or not item["id"].strip()):
            raise ValueError(f"evidence[{index}].id must be a nonempty string")
        identity = item.get("id", f"evidence-{index + 1}")
        if identity in seen_ids:
            raise ValueError("Duplicate evidence id; version each distinct evidence record")
        seen_ids.add(identity)
        optional_bool(f"evidence[{index}].kill_switch", item.get("kill_switch"))
        reasons = []
        published = item.get("published_at")
        available = item.get("available_at")
        if published is None or available is None:
            reasons.append("source_time_missing")
            temporal = False
        else:
            published, available = parse_timestamp(published), parse_timestamp(available)
            if available < published:
                raise ValueError(f"evidence[{index}].available_at precedes published_at")
            temporal = published <= decision_time and available <= decision_time
            if not temporal:
                reasons.append("evidence_not_available_at_decision")
        if item.get("expires_at") is not None and parse_timestamp(item["expires_at"]) <= decision_time:
            temporal = False
            reasons.append("evidence_expired")
        source_ok = _url(item.get("source_url"))
        claim_ok = isinstance(item.get("claim"), str) and bool(item["claim"].strip())
        if not source_ok:
            reasons.append("source_url_missing_or_invalid")
        if not claim_ok:
            reasons.append("claim_missing")
        available_valid = temporal and source_ok and claim_ok
        strong = (available_valid and item.get("evidence_strength") == "strong"
                  and item.get("source_type") in STRONG_SOURCE_TYPES
                  and item.get("supports_or_refutes") == "supports")
        kill = available_valid and item.get("kill_switch") is True
        strong_count += int(strong)
        kill_count += int(kill)
        audit.append({"index": index, "id": item.get("id", f"evidence-{index + 1}"),
                      "available": available_valid, "eligible_strong_support": strong,
                      "kill_switch_active": kill, "reasons": reasons})
    return {"audit": audit, "strong_support_count": strong_count,
            "active_kill_switch_count": kill_count,
            "source_verification": "user_supplied_not_independently_verified"}


def _trade_score(structure, stop_defined, rr):
    """Transparent heuristic points from measured structure; no invented research."""
    metrics = structure["metrics"]
    parent = metrics.get("parent_cycle")
    confirmed = (structure["state"] in READY_STRUCTURES
                 and metrics.get("parent_week_confirmed") is True
                 and metrics.get("session_history_complete") is True
                 and metrics.get("history_sufficient") is True)
    volume = metrics.get("volume_ratio")
    atr_percent = metrics.get("atr_percent")
    values = {
        "parent_cycle_direction": 15 if parent == "UP" else 10 if parent == "CONSOLIDATION" else 0,
        "child_cycle_structure": 15 if confirmed else 10 if structure["state"] == "Base Building" else 0,
        "breakout_confirmation": 15 if confirmed else 0,
        "pullback_quality": 10 if metrics.get("pullback_confirmed") is True else 0,
        "volume_confirmation": 10 if volume is not None and volume >= 1.2 else 5 if volume is not None and volume >= 1 else 0,
        "stop_loss_clarity": 15 if stop_defined else 0,
        "reward_risk": 15 if rr is not None and rr >= 3 else 10 if rr is not None and rr >= 2 else 0,
        "volatility_controlled": 5 if atr_percent is not None and atr_percent <= 5 else 0,
    }
    return TradeReadinessScorer().score(**values,
        closed_bar_confirmed=structure["closed_bar_confirmed"], stop_loss_defined=stop_defined)


def _risk_score(context, structure, evidence, *, market, currency, entry, stop, volume):
    """Shared measured/manual gates for generation and imported-card revalidation."""
    metrics = structure["metrics"]
    stop_defined = stop is not None and 0 < stop < entry
    supplied_risk = context.get("risk_checks", {})
    if not isinstance(supplied_risk, dict):
        raise TypeError("risk_checks must be an object")
    unknown_risk = set(supplied_risk) - set(RiskGovernorScorer.ITEMS)
    if unknown_risk:
        raise ValueError(f"Unknown risk_checks: {sorted(unknown_risk)}")
    checks = {name: optional_bool(name, supplied_risk.get(name)) for name in RiskGovernorScorer.ITEMS}
    # Measured failures can tighten a manual check; they cannot fill unknowns.
    if stop is not None and not stop_defined:
        checks["stop_loss_distance"] = False
    if stop_defined and (entry - stop) / entry > .10:
        checks["stop_loss_distance"] = False
    if metrics.get("overheated") is True:
        checks["price_location"] = False
    if metrics.get("atr_percent") is not None and metrics["atr_percent"] > 5:
        checks["volatility"] = False
    if market == "US" and currency == "USD" and volume * entry < 10_000_000:
        checks["liquidity"] = False
    if evidence["strong_support_count"] == 0:
        checks["evidence_quality"] = False
    risk = RiskGovernorScorer().check(**checks)
    if evidence["active_kill_switch_count"]:
        kill = RiskCheckItem("thesis_kill_switch", False, "Available evidence activates the thesis kill switch", "critical")
        risk.decision = RiskDecision.VETO
        risk.triggered_conditions.append(kill)
        risk.reasoning.append(kill.detail)
        risk.risk_warnings.append(kill.detail)
        risk.suggested_action = "Thesis vetoed; do not enter execution preparation"
    return risk


def build_card(dataset, context: dict, as_of=None) -> dict:
    """Build an immutable JSON snapshot from information available at as_of.

    Context may supply alpha_scores/pricing_scores (the public scorer keys),
    risk_checks (all ten bool-or-null risk keys), timestamped evidence, and
    user-selected stop_loss_price/target_price. Missing research is never scored
    as zero. A suggested structural stop is never adopted as a selected stop.
    These gates support a human research decision, not autonomous execution.
    """
    validate_dataset(dataset)
    if not isinstance(context, dict):
        raise TypeError("context must be an object")
    allowed = {"alpha_scores", "pricing_scores", "risk_checks", "stop_loss_price", "target_price", "evidence"}
    if set(context) - allowed:
        raise ValueError(f"Unknown context fields: {sorted(set(context) - allowed)}")
    context = to_jsonable(context)  # copy and reject NaN/inf before hashing
    if not dataset.bars:
        raise ValueError("Dataset contains no bars")
    decision_time = parse_timestamp(as_of) if as_of is not None else max(bar.available_at for bar in dataset.bars)
    visible = as_of_slice(dataset, decision_time)
    if not visible.bars:
        raise ValueError("No bars were available at as_of")
    structure = to_jsonable(analyze_structure(visible, decision_time))
    metrics = structure["metrics"]
    entry = metrics.get("price")
    if entry is None:
        entry = visible.bars[-1].close
    entry = number("entry_price", entry, 0)
    if entry == 0:
        raise ValueError("entry_price must be positive")
    stop = context.get("stop_loss_price")
    target = context.get("target_price")
    for name, value in (("stop_loss_price", stop), ("target_price", target)):
        if value is not None:
            number(name, value, 0)
            if value == 0:
                raise ValueError(f"{name} must be positive")
    stop_defined = stop is not None and 0 < stop < entry
    target_defined = target is not None and target > entry
    rr = (target - entry) / (entry - stop) if stop_defined and target_defined else None
    alpha = _score(AlphaThesisScorer(), context.get("alpha_scores"), "alpha_scores")
    pricing = _score(MarketPricingScorer(), context.get("pricing_scores"), "pricing_scores")
    evidence = _evidence_at(context.get("evidence", []), decision_time)
    risk = _risk_score(context, structure, evidence, market=visible.market, currency=visible.currency,
                       entry=entry, stop=stop, volume=visible.bars[-1].volume)
    trade = _trade_score(structure, stop_defined, rr)
    blockers = []
    profile_supported = (visible.market == "US" and visible.currency == "USD"
                         and visible.asset_type in {"US_STOCK", "ETF"} and visible.adjustment == "unadjusted")
    if not profile_supported:
        blockers.append("readiness_profile_unsupported")
    if not visible.is_mock and visible.exchange not in {"NYSE", "NASDAQ", "NYSE_ARCA", "CBOE"}:
        blockers.append("exchange_not_declared_or_supported")
    if (decision_time - visible.bars[-1].timestamp).total_seconds() > 4 * 86400:
        blockers.append("market_data_stale_over_4_days")
    if alpha is None:
        blockers.append("alpha_scores_missing")
    if pricing is None:
        blockers.append("pricing_scores_missing")
    if evidence["strong_support_count"] == 0:
        blockers.append("eligible_strong_evidence_missing")
    if evidence["active_kill_switch_count"]:
        blockers.append("thesis_kill_switch")
    if risk.missing_checks:
        blockers.append("risk_checks_unknown")
    if risk.decision is not RiskDecision.PASS:
        blockers.append("risk_gate_not_passed")
    if structure["closed_bar_confirmed"] is not True:
        blockers.append("closed_bar_not_confirmed")
    if structure["state"] not in READY_STRUCTURES or metrics.get("parent_week_confirmed") is not True:
        blockers.append("structure_not_confirmed")
    if metrics.get("history_sufficient") is not True:
        blockers.append("history_insufficient")
    if metrics.get("missing_session_dates"):
        blockers.append("declared_sessions_missing_or_unavailable")
    if not stop_defined:
        blockers.append("user_stop_missing_or_invalid")
    if not target_defined:
        blockers.append("user_target_missing_or_invalid")
    if rr is None or rr < 2:
        blockers.append("reward_risk_below_2_or_unknown")
    if trade.total < 85:
        blockers.append("trade_score_below_85")
    if alpha is not None and (alpha.grade.value == "D" or alpha.breakdown.evidence_quality < 10):
        blockers.append("thesis_or_evidence_score_too_low")
    if pricing is not None and pricing.grade == "D":
        blockers.append("pricing_score_too_low")
    if not _url(visible.source_url):
        blockers.append("market_source_url_missing")

    # Reuse the unified scorer's final mapping when both research layers exist.
    if risk.decision is RiskDecision.VETO:
        candidate = "Veto"
    elif alpha is None or pricing is None or evidence["strong_support_count"] == 0:
        candidate = "Research Only"
    else:
        candidate = BSHLAlphaScorer()._determine_final_status(alpha, pricing, trade, risk)
    if candidate == "Trade Ready" and blockers:
        candidate = "Watchlist"
    if not profile_supported and candidate != "Veto":
        candidate = "Research Only"
    simulation_status = candidate if visible.is_mock else None
    final_status = "Research Only" if visible.is_mock else candidate
    if visible.is_mock:
        blockers.append("mock_data_research_only")
    source = {"url": visible.source_url, "market": visible.market,
              "timeframe": visible.timeframe, "currency": visible.currency,
              "timezone": visible.timezone, "adjustment": visible.adjustment,
              "asset_type": visible.asset_type,
              "exchange": visible.exchange,
              "session_dates": [day.isoformat() for day in visible.session_dates],
              "retrieved_at": to_jsonable(visible.retrieved_at),
              "verification": "user_supplied_not_independently_verified"}
    hash_input = {"symbol": visible.symbol, "as_of": decision_time.isoformat(),
                  "bars": [to_jsonable(asdict(bar)) for bar in visible.bars],
                  "source": source, "data_mode": visible.data_mode, "is_mock": visible.is_mock,
                  "context": context, "rule_version": RULE_VERSION}
    analysis_id = sha256(json.dumps(hash_input, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()
    return to_jsonable({"schema_version": SCHEMA_VERSION, "rule_version": RULE_VERSION,
        "analysis_id": analysis_id, "symbol": visible.symbol, "as_of": decision_time,
        "data_mode": "mock" if visible.is_mock else visible.data_mode, "is_mock": visible.is_mock, "source": source,
        "technical_structure": structure, "alpha_thesis": alpha, "market_pricing": pricing,
        "trade_readiness": trade, "risk_governor": risk, "evidence": evidence,
        "trade_plan": {"entry_price": entry, "stop_loss_price": stop, "target_price": target,
                       "stop_loss_defined": stop_defined, "target_defined": target_defined,
                       "reward_risk_ratio": rr, "stop_source": "user" if stop is not None else "absent"},
        "final_status": final_status, "simulation_status": simulation_status,
        "blockers": blockers, "context": context,
        "score_interpretation": "Versioned heuristic points; not calibrated return probabilities"})
