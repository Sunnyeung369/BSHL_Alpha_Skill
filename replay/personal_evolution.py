"""Local decision history with reviewed candidates, never automatic risk weakening.

state.json is atomically replaced and authoritative. Legacy decisions.jsonl and
rules.json are migration inputs. This store supports one writer process only.
"""
from copy import deepcopy
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
import json
import math
import os
from pathlib import Path
import re
import tempfile
from typing import Dict, List, Optional


class DecisionType(Enum):
    TRADE = "trade"
    SKIP = "skip"
    WATCH = "watch"
    VETO = "veto"


class DecisionOutcome(Enum):
    PROFIT = "profit"
    LOSS = "loss"
    BREAK_EVEN = "break_even"
    MISSED = "missed"
    AVOIDED = "avoided"


@dataclass
class PersonalDecision:
    id: str
    timestamp: datetime
    symbol: str
    asset_class: str
    alpha_thesis_score: float
    market_pricing_score: float
    trade_readiness_score: float
    risk_governor_decision: str
    final_status: str
    user_decision: DecisionType
    user_action: str
    outcome: DecisionOutcome
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    price_change_percent: Optional[float] = None
    user_notes: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    rules_to_adjust: List[str] = field(default_factory=list)


@dataclass
class PersonalRule:
    id: str
    description: str
    category: str
    enabled: bool = True
    weight: float = 1.0
    success_count: int = 0
    failure_count: int = 0
    last_applied: Optional[datetime] = None
    evolution_history: List[Dict] = field(default_factory=list)

    def get_success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total else 0.5

    def should_disable(self) -> bool:
        """Compatibility method: observations never disable rules."""
        return False


def _validate_user_id(user_id: str) -> None:
    reserved = {"CON", "PRN", "AUX", "NUL"} | {
        f"{prefix}{i}" for prefix in ("COM", "LPT") for i in range(1, 10)}
    if (not isinstance(user_id, str) or
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,63}", user_id) or
            user_id.upper() in reserved):
        raise ValueError("user_id must be a safe 1-64 character identifier")


class PersonalEvolutionEngine:
    PROTECTED_RULES = {"RISK_VETO_OVERRIDE", "EVIDENCE_MIN_SCORE", "STRUCTURE_CONFIRMED"}

    def __init__(self, user_id: str, data_dir: Optional[Path] = None):
        _validate_user_id(user_id)
        self.user_id = user_id
        base = (Path.home() / ".bshl").resolve()
        self.data_dir = Path(data_dir).resolve() if data_dir is not None else (base / user_id).resolve()
        if data_dir is None and self.data_dir.parent != base:
            raise ValueError("user storage escapes .bshl")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.decisions: List[PersonalDecision] = []
        self.rules: Dict[str, PersonalRule] = {}
        self.candidates: List[Dict] = []
        self._load_data()
        self._init_default_rules()

    @staticmethod
    def _parse_decision(data: Dict) -> PersonalDecision:
        values = dict(data)
        values["timestamp"] = datetime.fromisoformat(values["timestamp"])
        values["user_decision"] = DecisionType(values["user_decision"])
        values["outcome"] = DecisionOutcome(values["outcome"])
        return PersonalDecision(**values)

    def _load_data(self):
        state_file = self.data_dir / "state.json"
        if state_file.exists():
            state = json.loads(state_file.read_text(encoding="utf-8"))
            if state.get("schema_version") != 1:
                raise ValueError("unsupported personal state schema")
            decisions_data, rules_data = state["decisions"], state["rules"]
            self.candidates = state.get("candidates", [])
        else:
            decisions_file = self.data_dir / "decisions.jsonl"
            decisions_data = [json.loads(line) for line in
                decisions_file.read_text(encoding="utf-8").splitlines() if line.strip()] if decisions_file.exists() else []
            rules_file = self.data_dir / "rules.json"
            rules_data = json.loads(rules_file.read_text(encoding="utf-8")) if rules_file.exists() else {}
        seen = set()
        for values in decisions_data:
            decision = self._parse_decision(values)
            if decision.id in seen:
                raise ValueError(f"duplicate stored decision id: {decision.id}")
            seen.add(decision.id)
            self.decisions.append(decision)
        for rule_id, values in rules_data.items():
            values = dict(values)
            if values.get("last_applied"):
                values["last_applied"] = datetime.fromisoformat(values["last_applied"])
            if values.get("id") != rule_id:
                raise ValueError("rule key and id differ")
            self.rules[rule_id] = PersonalRule(**values)

    def _is_protected(self, rule: PersonalRule) -> bool:
        return rule.id in self.PROTECTED_RULES or rule.category == "risk"

    def _init_default_rules(self):
        defaults = [
            PersonalRule("EVIDENCE_MIN_SCORE", "Alpha Thesis below 70: research only", "evidence"),
            PersonalRule("PRICING_CROWDED_SKIP", "Avoid chasing crowded prices", "pricing"),
            PersonalRule("STRUCTURE_CONFIRMED", "Require closed-bar confirmation", "structure"),
            PersonalRule("RISK_VETO_OVERRIDE", "Risk veto cannot be bypassed", "risk", weight=2.0),
            PersonalRule("TIMING_PULLBACK", "Wait for a confirmed pullback", "timing", weight=0.8),
        ]
        for rule in defaults:
            self.rules.setdefault(rule.id, rule)
        for rule in self.rules.values():
            if self._is_protected(rule):
                rule.enabled = True

    @staticmethod
    def _serialize_decision(decision: PersonalDecision) -> Dict:
        result = asdict(decision)
        result["timestamp"] = decision.timestamp.isoformat()
        result["user_decision"] = decision.user_decision.value
        result["outcome"] = decision.outcome.value
        return result

    def _save_state(self):
        rules = {}
        for rule_id, rule in self.rules.items():
            values = asdict(rule)
            values["last_applied"] = rule.last_applied.isoformat() if rule.last_applied else None
            if self._is_protected(rule):
                values["enabled"] = True
            rules[rule_id] = values
        state = {"schema_version": 1, "decisions": [self._serialize_decision(d) for d in self.decisions],
                 "rules": rules, "candidates": self.candidates}
        fd, temporary = tempfile.mkstemp(prefix=".state-", suffix=".tmp", dir=self.data_dir)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(state, handle, ensure_ascii=False, indent=2, allow_nan=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.data_dir / "state.json")
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _save_rules(self):
        self._save_state()

    def record_decision(self, decision: PersonalDecision):
        if not decision.id or any(d.id == decision.id for d in self.decisions):
            raise ValueError("decision id must be nonempty and unique")
        old = deepcopy((self.decisions, self.rules, self.candidates))
        try:
            self.decisions.append(deepcopy(decision))
            for rule_id in set(decision.rules_to_adjust):
                if rule_id not in self.rules:
                    continue
                rule = self.rules[rule_id]
                rule.success_count += int(decision.outcome == DecisionOutcome.PROFIT)
                rule.failure_count += int(decision.outcome == DecisionOutcome.LOSS)
                rule.last_applied = decision.timestamp
                rule.evolution_history.append({"timestamp": decision.timestamp.isoformat(),
                    "decision_id": decision.id, "outcome": decision.outcome.value, "event": "observation"})
                total = rule.success_count + rule.failure_count
                if not self._is_protected(rule) and total >= 5 and not any(
                        c["rule_id"] == rule_id and c["status"] == "pending" for c in self.candidates):
                    self.candidates.append({"id": f"{rule_id}:{total}", "rule_id": rule_id,
                        "status": "pending", "observations": total,
                        "label_success_rate": rule.get_success_rate(),
                        "reason": "Review costs and out-of-sample evidence before accepting a change"})
            self._save_state()
        except Exception:
            self.decisions, self.rules, self.candidates = old
            raise

    def accept_candidate(self, candidate_id: str, *, reviewer: str, rationale: str,
                         validation_reference: str, weight: Optional[float] = None,
                         enabled: Optional[bool] = None) -> Dict:
        """Explicit review; the reference records evidence and is not proof."""
        if not all(isinstance(v, str) and v.strip() for v in (reviewer, rationale, validation_reference)):
            raise ValueError("reviewer, rationale and validation reference are required")
        candidate = next((c for c in self.candidates if c["id"] == candidate_id), None)
        if candidate is None or candidate["status"] != "pending":
            raise ValueError("unknown or already reviewed candidate")
        rule = self.rules[candidate["rule_id"]]
        if self._is_protected(rule):
            raise ValueError("protected gates cannot be changed by personal adaptation")
        if weight is not None and (isinstance(weight, bool) or not math.isfinite(weight) or weight <= 0):
            raise ValueError("weight must be finite and positive")
        if enabled is not None and not isinstance(enabled, bool):
            raise ValueError("enabled must be boolean")
        old = deepcopy((self.rules, self.candidates))
        try:
            before = {"weight": rule.weight, "enabled": rule.enabled}
            if weight is not None:
                rule.weight = weight
            if enabled is not None:
                rule.enabled = enabled
            candidate.update(status="accepted", reviewer=reviewer, rationale=rationale,
                validation_reference=validation_reference, reviewed_at=datetime.now(timezone.utc).isoformat(),
                before=before, after={"weight": rule.weight, "enabled": rule.enabled})
            rule.evolution_history.append(deepcopy(candidate))
            self._save_state()
        except Exception:
            self.rules, self.candidates = old
            raise
        return deepcopy(candidate)

    def get_personal_insights(self) -> Dict:
        counts = {outcome.value: sum(d.outcome == outcome for d in self.decisions) for outcome in DecisionOutcome}
        resolved = counts["profit"] + counts["loss"]
        lessons = {}
        for decision in self.decisions:
            for lesson in decision.lessons_learned:
                lessons[lesson] = lessons.get(lesson, 0) + 1
        return {"summary": {"total_decisions": len(self.decisions), **counts,
            "success_rate": counts["profit"] / resolved if resolved else None,
            "status": "insufficient" if resolved < 30 else "descriptive_only"},
            "best_symbols": [],
            "rules": {"active": sum(r.enabled for r in self.rules.values()),
                "disabled": sum(not r.enabled for r in self.rules.values()),
                "details": [{"id": r.id, "description": r.description, "success_rate": r.get_success_rate(),
                    "enabled": r.enabled, "protected": self._is_protected(r)} for r in self.rules.values()]},
            "top_lessons": sorted(lessons, key=lambda item: (-lessons[item], item))[:5]}

    def get_adjusted_weights(self) -> Dict[str, float]:
        """Only explicitly reviewed weights; no win-rate multiplier."""
        return {key: rule.weight for key, rule in self.rules.items() if rule.enabled}

    def evolve(self) -> Dict:
        return {"insights": self.get_personal_insights(),
            "suggestions": [{"type": "info", "message": "候选规则需人工审阅与样本外验证；硬风控不自动更改"}],
            "candidates": deepcopy(self.candidates), "adjusted_weights": self.get_adjusted_weights()}


_engines: Dict[str, PersonalEvolutionEngine] = {}


def get_engine(user_id: str = "default") -> PersonalEvolutionEngine:
    _validate_user_id(user_id)
    if user_id not in _engines:
        _engines[user_id] = PersonalEvolutionEngine(user_id)
    return _engines[user_id]
