"""Risk gate. Unknown checks never imply permission to trade."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional
from .validation import optional_bool


class RiskDecision(Enum):
    PASS = "Pass"
    REDUCE_SIZE = "Reduce Size"
    WATCH_ONLY = "Watch Only"
    WAIT_CONFIRMATION = "Wait Confirmation"
    WAIT = "Wait"
    VETO = "Veto"


@dataclass
class RiskCheckItem:
    name: str
    status: Optional[bool]
    detail: str
    severity: str


@dataclass
class RiskGovernorScore:
    decision: RiskDecision
    reasoning: List[str]
    suggested_action: str
    risk_warnings: List[str]
    triggered_conditions: List[RiskCheckItem]
    checks: List[RiskCheckItem] = field(default_factory=list)
    missing_checks: List[str] = field(default_factory=list)


class RiskGovernorScorer:
    # True always means passed, including fields whose names describe risks.
    ITEMS = {
        "liquidity": ("critical", "liquidity_detail", "流动性不足"),
        "volatility": ("critical", "volatility_detail", "波动过大"),
        "evidence_quality": ("high", "evidence_detail", "证据质量太弱"),
        "social_crowding": ("medium", "crowding_detail", "社媒热度过度拥挤"),
        "earnings_risk": ("high", "earnings_detail", "财报风险过高"),
        "regulatory_uncertainty": ("critical", "regulatory_detail", "重大监管不确定"),
        "price_location": ("medium", "price_detail", "价格远离均值"),
        "stop_loss_distance": ("critical", "stop_detail", "止损距离过大"),
        "position_exposure": ("high", "position_detail", "仓位暴露过高"),
        "correlation": ("high", "correlation_detail", "相关资产集中度过高"),
    }

    def __init__(self):
        self.risk_items = list(self.ITEMS)

    def check(self, liquidity=None, volatility=None, evidence_quality=None,
              social_crowding=None, earnings_risk=None, regulatory_uncertainty=None,
              price_location=None, stop_loss_distance=None, position_exposure=None,
              correlation=None, **details):
        values = locals()
        for key in details:
            if key not in {item[1] for item in self.ITEMS.values()}:
                raise TypeError(f"Unknown risk detail: {key}")
            if not isinstance(details[key], str):
                raise TypeError(f"{key} must be a string")
        checks, triggered, missing = [], [], []
        for name, (severity, detail_key, failure) in self.ITEMS.items():
            value = optional_bool(name, values[name])
            detail = details.get(detail_key, "检查通过" if value is True else failure)
            if value is None:
                missing.append(name)
                detail = f"{name} 检查结果未知"
            item = RiskCheckItem(name, value, detail, severity if value is False else "low")
            checks.append(item)
            if value is False:
                triggered.append(item)
        decision = self._make_decision(triggered, missing)
        reasoning = [f"{item.detail} - {item.severity.upper()}" for item in triggered]
        reasoning.extend(f"{name} 未完成检查" for name in missing)
        actions = {
            RiskDecision.PASS: "全部检查通过，可交由用户评估执行计划",
            RiskDecision.REDUCE_SIZE: "降低仓位后重新检查，尚未允许执行",
            RiskDecision.WATCH_ONLY: "只观察，不交易，等待证据改善",
            RiskDecision.WAIT_CONFIRMATION: "必要检查未知，补全后重新判断",
            RiskDecision.WAIT: "等待条件改善后重新判断",
            RiskDecision.VETO: "一票否决，禁止交易",
        }
        warnings = [item.detail for item in triggered if item.severity in ("critical", "high")]
        return RiskGovernorScore(decision, reasoning, actions[decision], warnings,
                                 triggered, checks, missing)

    def _make_decision(self, triggered, missing=None):
        """Dominance: veto > weak evidence > wait > unknown > reduce > pass."""
        names = {item.name for item in triggered}
        if names & {"liquidity", "volatility", "stop_loss_distance", "regulatory_uncertainty"}:
            return RiskDecision.VETO
        if "evidence_quality" in names:
            return RiskDecision.WATCH_ONLY
        if names & {"earnings_risk", "price_location"}:
            return RiskDecision.WAIT
        if missing:
            return RiskDecision.WAIT_CONFIRMATION
        if names & {"social_crowding", "position_exposure", "correlation"}:
            return RiskDecision.REDUCE_SIZE
        return RiskDecision.PASS if not triggered else RiskDecision.WAIT_CONFIRMATION
