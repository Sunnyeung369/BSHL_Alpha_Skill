"""
BSHL Alpha Skill - Risk Governor Score Calculator

风控总闸评分器，不做总分计算，只做否决判断。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class RiskDecision(Enum):
    """风控决策"""
    PASS = "Pass"
    REDUCE_SIZE = "Reduce Size"
    WATCH_ONLY = "Watch Only"
    WAIT_CONFIRMATION = "Wait Confirmation"
    WAIT = "Wait"
    VETO = "Veto"


@dataclass
class RiskCheckItem:
    """风险检查项"""
    name: str
    status: bool  # True=通过, False=不通过
    detail: str
    severity: str  # critical, high, medium, low


@dataclass
class RiskGovernorScore:
    """风控评分结果"""
    decision: RiskDecision
    reasoning: List[str]
    suggested_action: str
    risk_warnings: List[str]
    triggered_conditions: List[RiskCheckItem]


class RiskGovernorScorer:
    """风控总闸评分器"""

    def __init__(self):
        # 风险检查项定义
        self.risk_items = [
            "liquidity",
            "volatility",
            "evidence_quality",
            "social_crowding",
            "earnings_risk",
            "regulatory_uncertainty",
            "price_location",
            "stop_loss_distance",
            "position_exposure",
            "correlation",
        ]

    def check(
        self,
        liquidity: Optional[bool] = None,
        volatility: Optional[bool] = None,
        evidence_quality: Optional[bool] = None,
        social_crowding: Optional[bool] = None,
        earnings_risk: Optional[bool] = None,
        regulatory_uncertainty: Optional[bool] = None,
        price_location: Optional[bool] = None,
        stop_loss_distance: Optional[bool] = None,
        position_exposure: Optional[bool] = None,
        correlation: Optional[bool] = None,
        **details: str,
    ) -> RiskGovernorScore:
        """
        风控检查

        Args:
            liquidity: 流动性是否充足
            volatility: 波动是否可控
            evidence_quality: 证据质量是否足够
            social_crowding: 社媒热度是否过度拥挤
            earnings_risk: 财报前风险是否过高
            regulatory_uncertainty: 是否有重大监管不确定
            price_location: 价格位置是否合理
            stop_loss_distance: 止损距离是否合理
            position_exposure: 仓位暴露是否合理
            correlation: 相关性是否过高
            **details: 各检查项的详细说明

        Returns:
            RiskGovernorScore: 风控检查结果
        """

        # 构建检查项
        checks = []
        triggered = []

        # 流动性检查
        if liquidity is not None:
            check = RiskCheckItem(
                name="liquidity",
                status=liquidity,
                detail=details.get("liquidity_detail", "流动性充足" if liquidity else "流动性不足"),
                severity="critical" if not liquidity else "low",
            )
            checks.append(check)
            if not liquidity:
                triggered.append(check)

        # 波动检查
        if volatility is not None:
            check = RiskCheckItem(
                name="volatility",
                status=volatility,
                detail=details.get("volatility_detail", "波动可控" if volatility else "波动过大"),
                severity="critical" if not volatility else "low",
            )
            checks.append(check)
            if not volatility:
                triggered.append(check)

        # 证据质量检查
        if evidence_quality is not None:
            check = RiskCheckItem(
                name="evidence_quality",
                status=evidence_quality,
                detail=details.get("evidence_detail", "证据质量足够" if evidence_quality else "证据质量太弱"),
                severity="high" if not evidence_quality else "low",
            )
            checks.append(check)
            if not evidence_quality:
                triggered.append(check)

        # 社媒热度检查
        if social_crowding is not None:
            check = RiskCheckItem(
                name="social_crowding",
                status=social_crowding,
                detail=details.get("crowding_detail", "热度适中" if social_crowding else "社媒热度过度拥挤"),
                severity="medium" if not social_crowding else "low",
            )
            checks.append(check)
            if not social_crowding:
                triggered.append(check)

        # 财报风险检查
        if earnings_risk is not None:
            check = RiskCheckItem(
                name="earnings_risk",
                status=earnings_risk,
                detail=details.get("earnings_detail", "财报风险可控" if earnings_risk else "财报前风险过高"),
                severity="high" if not earnings_risk else "low",
            )
            checks.append(check)
            if not earnings_risk:
                triggered.append(check)

        # 监管不确定检查
        if regulatory_uncertainty is not None:
            check = RiskCheckItem(
                name="regulatory_uncertainty",
                status=regulatory_uncertainty,
                detail=details.get("regulatory_detail", "监管确定" if regulatory_uncertainty else "重大监管不确定"),
                severity="critical" if not regulatory_uncertainty else "low",
            )
            checks.append(check)
            if not regulatory_uncertainty:
                triggered.append(check)

        # 价格位置检查
        if price_location is not None:
            check = RiskCheckItem(
                name="price_location",
                status=price_location,
                detail=details.get("price_detail", "价格位置合理" if price_location else "个股已远离均值"),
                severity="medium" if not price_location else "low",
            )
            checks.append(check)
            if not price_location:
                triggered.append(check)

        # 止损距离检查
        if stop_loss_distance is not None:
            check = RiskCheckItem(
                name="stop_loss_distance",
                status=stop_loss_distance,
                detail=details.get("stop_detail", "止损距离合理" if stop_loss_distance else "止损距离过大"),
                severity="critical" if not stop_loss_distance else "low",
            )
            checks.append(check)
            if not stop_loss_distance:
                triggered.append(check)

        # 仓位暴露检查
        if position_exposure is not None:
            check = RiskCheckItem(
                name="position_exposure",
                status=position_exposure,
                detail=details.get("position_detail", "仓位暴露合理" if position_exposure else "仓位暴露过高"),
                severity="high" if not position_exposure else "low",
            )
            checks.append(check)
            if not position_exposure:
                triggered.append(check)

        # 相关性检查
        if correlation is not None:
            check = RiskCheckItem(
                name="correlation",
                status=correlation,
                detail=details.get("correlation_detail", "相关性合理" if correlation else "相关资产集中度过高"),
                severity="high" if not correlation else "low",
            )
            checks.append(check)
            if not correlation:
                triggered.append(check)

        # 做出决策
        decision = self._make_decision(triggered)
        reasoning = self._generate_reasoning(triggered)
        suggested_action = self._generate_suggested_action(decision, triggered)
        risk_warnings = self._generate_risk_warnings(triggered)

        return RiskGovernorScore(
            decision=decision,
            reasoning=reasoning,
            suggested_action=suggested_action,
            risk_warnings=risk_warnings,
            triggered_conditions=triggered,
        )

    def _make_decision(self, triggered: List[RiskCheckItem]) -> RiskDecision:
        """做出风控决策"""
        # 检查是否有 Critical 级别的触发条件
        critical_triggered = any(t.severity == "critical" for t in triggered)

        # 检查具体触发条件
        triggered_names = {t.name for t in triggered}

        # 一票否决条件
        veto_conditions = {"liquidity", "volatility", "stop_loss_distance", "regulatory_uncertainty"}
        if veto_conditions.intersection(triggered_names):
            return RiskDecision.VETO

        # 证据质量太弱
        if "evidence_quality" in triggered_names:
            return RiskDecision.WATCH_ONLY

        # 社媒过度拥挤
        if "social_crowding" in triggered_names:
            return RiskDecision.REDUCE_SIZE

        # 财报前风险过高
        if "earnings_risk" in triggered_names:
            return RiskDecision.WAIT

        # 仓位或相关性问题
        if "position_exposure" in triggered_names or "correlation" in triggered_names:
            return RiskDecision.REDUCE_SIZE

        # 价格位置问题
        if "price_location" in triggered_names:
            return RiskDecision.WAIT

        # 无触发条件
        if not triggered:
            return RiskDecision.PASS

        # 默认等待确认
        return RiskDecision.WAIT_CONFIRMATION

    def _generate_reasoning(self, triggered: List[RiskCheckItem]) -> List[str]:
        """生成决策推理"""
        reasoning = []

        for item in triggered:
            reasoning.append(f"{item.detail} - {item.severity.upper()}")

        return reasoning

    def _generate_suggested_action(self, decision: RiskDecision, triggered: List[RiskCheckItem]) -> str:
        """生成建议动作"""
        if decision == RiskDecision.PASS:
            return "通过风控检查，可按计划执行"
        elif decision == RiskDecision.REDUCE_SIZE:
            return "降低仓位，控制在建议范围内"
        elif decision == RiskDecision.WATCH_ONLY:
            return "只观察，不交易，等待证据改善"
        elif decision == RiskDecision.WAIT_CONFIRMATION:
            return "等待进一步确认再决定"
        elif decision == RiskDecision.WAIT:
            return "等待更好的入场时机"
        else:  # VETO
            return "一票否决，禁止交易"

    def _generate_risk_warnings(self, triggered: List[RiskCheckItem]) -> List[str]:
        """生成风险警告"""
        warnings = []
        for item in triggered:
            if item.severity in ["critical", "high"]:
                warnings.append(f"⚠️ {item.detail}")
        return warnings


def main():
    """示例用法"""
    scorer = RiskGovernorScorer()

    # 示例 1: 通过
    print("=== 示例 1: 通过 ===")
    result = scorer.check(
        liquidity=True,
        volatility=True,
        evidence_quality=True,
        stop_loss_distance=True,
    )
    print(f"决策: {result.decision.value}")
    print(f"建议: {result.suggested_action}")

    # 示例 2: 流动性不足导致否决
    print("\n=== 示例 2: 流动性否决 ===")
    result = scorer.check(
        liquidity=False,
        volatility=True,
        evidence_quality=True,
        stop_loss_distance=True,
        liquidity_detail="日成交额仅 $5M，流动性不足",
    )
    print(f"决策: {result.decision.value}")
    print(f"建议: {result.suggested_action}")
    print(f"推理: {result.reasoning}")

    # 示例 3: 拥挤度高，降级
    print("\n=== 示例 3: 拥挤降级 ===")
    result = scorer.check(
        liquidity=True,
        volatility=True,
        evidence_quality=True,
        social_crowding=False,
        stop_loss_distance=True,
        crowding_detail="社媒讨论量激增 5 倍，过度拥挤",
    )
    print(f"决策: {result.decision.value}")
    print(f"建议: {result.suggested_action}")
    print(f"警告: {result.risk_warnings}")


if __name__ == "__main__":
    main()
