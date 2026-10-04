"""
BSHL Alpha Skill - Position Risk Score Calculator

计算仓位风险评分，评估当前仓位是否合理。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from .validation import number


class RiskLevel(Enum):
    """风险等级"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    EXTREME = "Extreme"


@dataclass
class PositionRiskBreakdown:
    """仓位风险评分明细"""
    single_position_size: float = 0.0       # 单一仓位大小 (25)
    sector_concentration: float = 0.0       # 板块集中度 (20)
    total_exposure: float = 0.0             # 总敞口 (20)
    leverage_ratio: float = 0.0              # 杠杆比例 (15)
    correlation_risk: float = 0.0           # 相关性风险 (10)
    liquidity_risk: float = 0.0             # 流动性风险 (10)


@dataclass
class PositionRiskScore:
    """仓位风险评分"""
    total: float
    risk_level: RiskLevel
    breakdown: PositionRiskBreakdown
    reasoning: List[str]
    warnings: List[str]
    recommended_max_size: float
    recommended_additional_size: float = 0.0


class PositionRiskScorer:
    """仓位风险评分器"""

    def __init__(self):
        self.weights = {
            "single_position_size": 25,
            "sector_concentration": 20,
            "total_exposure": 20,
            "leverage_ratio": 15,
            "correlation_risk": 10,
            "liquidity_risk": 10,
        }

        # 默认风险限制
        self.default_limits = {
            "max_single_position": 0.05,      # 单一标的最大 5%
            "max_sector_exposure": 0.25,       # 单一板块最大 25%
            "max_total_exposure": 0.80,        # 总敞口最大 80%
            "max_leverage": 1.0,               # 最大杠杆 1 倍
            "max_correlation": 0.7,            # 最大相关性 70%
            "min_liquidity": 10_000_000,       # 最小日成交额 $10M
        }

    def score(
        self,
        single_position_size: float,
        sector_concentration: float,
        total_exposure: float,
        leverage_ratio: float,
        correlation_risk: float,
        liquidity_risk: float,
        total_capital: float = 100000,
        current_position_size: Optional[float] = None,
        stop_loss_fraction: Optional[float] = None,
        risk_budget_fraction: float = 0.01,
        liquidity_capital_limit: Optional[float] = None,
    ) -> PositionRiskScore:
        """
        计算仓位风险评分

        Args:
            single_position_size: 单一仓位大小百分比 (0-1，如 0.05 = 5%)
            sector_concentration: 板块集中度百分比 (0-1)
            total_exposure: 总敞口百分比 (0-1)
            leverage_ratio: 杠杆比例 (1 表示无杠杆，>1 表示有杠杆)
            correlation_risk: 相关性风险评分 (0-10，10 表示无相关性风险)
            liquidity_risk: 流动性风险评分 (0-10，10 表示流动性充足)
            total_capital: 总资金
            current_position_size: 当前仓位金额，与 total_capital 同币种；默认根据百分比计算
            stop_loss_fraction: 入场价到止损价的距离比例，0.05 表示 5%；未知时不建议新增仓位
            risk_budget_fraction: 示例账户损失预算比例，默认 1%，未经收益校准
            liquidity_capital_limit: 可选持仓金额上限，与 total_capital 同币种

        Notes:
            Exposure inputs include the existing position. recommended_max_size
            is a total position cap; recommended_additional_size is an increment.
            This long-only, unlevered sizing model does not model gap losses,
            derivatives, execution costs or guaranteed stop execution.

        Returns:
            PositionRiskScore: 完整评分结果
        """

        for name, value in (("single_position_size", single_position_size),
                            ("sector_concentration", sector_concentration),
                            ("total_exposure", total_exposure)):
            number(name, value, 0, 1)
        number("leverage_ratio", leverage_ratio, 1)
        if sector_concentration > total_exposure + 1e-12:
            raise ValueError("total_exposure must include sector_concentration")
        number("correlation_risk", correlation_risk, 0, 10)
        number("liquidity_risk", liquidity_risk, 0, 10)
        number("total_capital", total_capital, 0)
        if total_capital == 0:
            raise ValueError("total_capital must be positive")
        number("risk_budget_fraction", risk_budget_fraction, 0, 1)
        if stop_loss_fraction is not None:
            number("stop_loss_fraction", stop_loss_fraction, 0, 1)
            if stop_loss_fraction == 0:
                raise ValueError("stop_loss_fraction must be positive")
        if liquidity_capital_limit is not None:
            number("liquidity_capital_limit", liquidity_capital_limit, 0)
        current = single_position_size * total_capital if current_position_size is None else number(
            "current_position_size", current_position_size, 0, total_capital)
        if abs(current - single_position_size * total_capital) > 1e-8:
            raise ValueError("current_position_size must match single_position_size * total_capital")
        if current > sector_concentration * total_capital + 1e-8 or current > total_exposure * total_capital + 1e-8:
            raise ValueError("sector_concentration and total_exposure must include current_position_size")
        # 计算单项评分
        single_score = self._score_single_position(single_position_size)
        sector_score = self._score_sector_concentration(sector_concentration)
        total_score = self._score_total_exposure(total_exposure)
        leverage_score = self._score_leverage(leverage_ratio)
        correlation_score = correlation_risk
        liquidity_score = liquidity_risk

        # 计算总分
        total = (
            single_score +
            sector_score +
            total_score +
            leverage_score +
            correlation_score +
            liquidity_score
        )

        # 确定风险等级（分数越低风险越高）
        if total >= 85:
            risk_level = RiskLevel.LOW
        elif total >= 70:
            risk_level = RiskLevel.MEDIUM
        elif total >= 55:
            risk_level = RiskLevel.HIGH
        else:
            risk_level = RiskLevel.EXTREME

        # 构建明细
        breakdown = PositionRiskBreakdown(
            single_position_size=single_score,
            sector_concentration=sector_score,
            total_exposure=total_score,
            leverage_ratio=leverage_score,
            correlation_risk=correlation_score,
            liquidity_risk=liquidity_score,
        )

        # 生成推理和警告
        reasoning = self._generate_reasoning(breakdown, single_position_size, sector_concentration, total_exposure, leverage_ratio)
        warnings = self._generate_warnings(breakdown, single_position_size, sector_concentration, total_exposure, leverage_ratio)
        recommended_max_size = self._calculate_max_position_size(total, total_capital)
        remaining_total = max(0, self.default_limits["max_total_exposure"] - total_exposure) * total_capital
        remaining_sector = max(0, self.default_limits["max_sector_exposure"] - sector_concentration) * total_capital
        recommended_max_size = min(recommended_max_size, current + remaining_total, current + remaining_sector)
        if liquidity_capital_limit is not None:
            recommended_max_size = min(recommended_max_size, liquidity_capital_limit)
        if stop_loss_fraction is None:
            recommended_max_size = min(recommended_max_size, current)
            warnings.append("止损距离未知，不建议新增仓位")
        else:
            recommended_max_size = min(recommended_max_size, total_capital * risk_budget_fraction / stop_loss_fraction)
        if leverage_ratio > 1 or correlation_risk < 5 or liquidity_risk < 5:
            recommended_max_size = min(recommended_max_size, current)
            warnings.append("杠杆、相关性或流动性限制未通过，不建议新增仓位")
        recommended_additional_size = max(0, recommended_max_size - current)

        return PositionRiskScore(
            total=total,
            risk_level=risk_level,
            breakdown=breakdown,
            reasoning=reasoning,
            warnings=warnings,
            recommended_max_size=recommended_max_size,
            recommended_additional_size=recommended_additional_size,
        )

    def _score_single_position(self, size: float) -> float:
        """评分单一仓位大小"""
        max_size = self.default_limits["max_single_position"]
        if size <= max_size * 0.5:
            return 25  # 非常安全
        elif size <= max_size:
            return 20  # 安全
        elif size <= max_size * 1.5:
            return 15  # 略大
        elif size <= max_size * 2:
            return 10  # 偏大
        else:
            return 5  # 过大

    def _score_sector_concentration(self, concentration: float) -> float:
        """评分板块集中度"""
        max_sector = self.default_limits["max_sector_exposure"]
        if concentration <= max_sector * 0.5:
            return 20  # 分散良好
        elif concentration <= max_sector:
            return 15  # 集中度适中
        elif concentration <= max_sector * 1.3:
            return 10  # 略集中
        elif concentration <= max_sector * 1.5:
            return 5  # 过度集中
        else:
            return 0  # 极度集中

    def _score_total_exposure(self, exposure: float) -> float:
        """评分总敞口"""
        max_exposure = self.default_limits["max_total_exposure"]
        if exposure <= max_exposure * 0.5:
            return 20  # 保守
        elif exposure <= max_exposure:
            return 15  # 适中
        elif exposure <= max_exposure * 1.1:
            return 10  # 激进
        elif exposure <= max_exposure * 1.2:
            return 5  # 过度激进
        else:
            return 0  # 极度风险

    def _score_leverage(self, ratio: float) -> float:
        """评分杠杆比例"""
        if ratio <= 1.0:
            return 15  # 无杠杆
        elif ratio <= 1.2:
            return 12  # 轻微杠杆
        elif ratio <= 1.5:
            return 8  # 中等杠杆
        elif ratio <= 2.0:
            return 4  # 高杠杆
        else:
            return 0  # 极高杠杆

    def _generate_reasoning(
        self,
        breakdown: PositionRiskBreakdown,
        single_position_size: float,
        sector_concentration: float,
        total_exposure: float,
        leverage_ratio: float,
    ) -> List[str]:
        """生成评分推理"""
        reasoning = []

        # 单一仓位
        if breakdown.single_position_size >= 20:
            reasoning.append(f"单一仓位 {single_position_size:.1%} - 安全")
        elif breakdown.single_position_size >= 15:
            reasoning.append(f"单一仓位 {single_position_size:.1%} - 略大但可接受")
        else:
            reasoning.append(f"单一仓位 {single_position_size:.1%} - 过大，建议减少")

        # 板块集中度
        if breakdown.sector_concentration >= 15:
            reasoning.append(f"板块集中度 {sector_concentration:.1%} - 分散良好")
        elif breakdown.sector_concentration >= 10:
            reasoning.append(f"板块集中度 {sector_concentration:.1%} - 适中")
        else:
            reasoning.append(f"板块集中度 {sector_concentration:.1%} - 过度集中")

        # 总敞口
        if breakdown.total_exposure >= 15:
            reasoning.append(f"总敞口 {total_exposure:.1%} - 合理")
        elif breakdown.total_exposure >= 10:
            reasoning.append(f"总敞口 {total_exposure:.1%} - 激进")
        else:
            reasoning.append(f"总敞口 {total_exposure:.1%} - 过度风险")

        # 杠杆
        if breakdown.leverage_ratio >= 12:
            reasoning.append("无杠杆 - 风险可控")
        elif breakdown.leverage_ratio >= 8:
            reasoning.append(f"杠杆 {leverage_ratio:.1f}x - 中等")
        else:
            reasoning.append(f"杠杆 {leverage_ratio:.1f}x - 风险过高")

        return reasoning

    def _generate_warnings(
        self,
        breakdown: PositionRiskBreakdown,
        single_position_size: float,
        sector_concentration: float,
        total_exposure: float,
        leverage_ratio: float,
    ) -> List[str]:
        """生成风险警告"""
        warnings = []

        if breakdown.single_position_size < 15:
            warnings.append(f"⚠️ 单一仓位过大 ({single_position_size:.1%})，建议拆分")

        if breakdown.sector_concentration < 10:
            warnings.append(f"⚠️ 板块过度集中 ({sector_concentration:.1%})，建议分散")

        if breakdown.total_exposure < 10:
            warnings.append(f"⚠️ 总敞口过高 ({total_exposure:.1%})，建议降低")

        if breakdown.leverage_ratio < 8:
            warnings.append(f"⚠️ 杠杆过高 ({leverage_ratio:.1f}x)，建议降低")

        if breakdown.correlation_risk < 5:
            warnings.append("⚠️ 持仓相关性过高，建议分散")

        if breakdown.liquidity_risk < 5:
            warnings.append("⚠️ 部分持仓流动性不足，注意退出风险")

        return warnings

    def _calculate_max_position_size(self, total_score: float, total_capital: float) -> float:
        """计算建议最大仓位"""
        if total_score >= 85:
            max_pct = self.default_limits["max_single_position"]
        elif total_score >= 70:
            max_pct = self.default_limits["max_single_position"] * 0.8
        elif total_score >= 55:
            max_pct = self.default_limits["max_single_position"] * 0.5
        else:
            max_pct = self.default_limits["max_single_position"] * 0.3

        return total_capital * max_pct


def main():
    """示例用法"""
    scorer = PositionRiskScorer()

    # 示例 1: 健康的仓位配置
    print("=== 示例 1: 健康配置 ===")
    score = scorer.score(
        single_position_size=0.04,      # 4%
        sector_concentration=0.20,       # 20%
        total_exposure=0.60,             # 60%
        leverage_ratio=1.0,              # 无杠杆
        correlation_risk=8,              # 相关性风险低
        liquidity_risk=9,                # 流动性好
        total_capital=100000,
    )
    print(f"总分: {score.total}")
    print(f"风险等级: {score.risk_level.value}")
    print(f"建议最大仓位: ${score.recommended_max_size:,.2f}")
    print("\n推理:")
    for reason in score.reasoning:
        print(f"  - {reason}")

    # 示例 2: 风险较高的配置
    print("\n=== 示例 2: 风险较高 ===")
    score = scorer.score(
        single_position_size=0.08,       # 8% - 过大
        sector_concentration=0.40,       # 40% - 过度集中
        total_exposure=0.90,             # 90% - 敞口过高
        leverage_ratio=1.3,              # 有杠杆
        correlation_risk=4,              # 相关性风险高
        liquidity_risk=6,               # 流动性一般
        total_capital=100000,
    )
    print(f"总分: {score.total}")
    print(f"风险等级: {score.risk_level.value}")
    print(f"建议最大仓位: ${score.recommended_max_size:,.2f}")
    print("\n警告:")
    for warning in score.warnings:
        print(f"  {warning}")


if __name__ == "__main__":
    main()
