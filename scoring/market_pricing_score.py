"""
BSHL Alpha Skill - Market Pricing Score Calculator

计算市场定价评分，评估市场是否已经定价。
"""

from typing import Dict, List
from dataclasses import dataclass
from enum import Enum
from .validation import score_values


@dataclass
class PricingScoreBreakdown:
    """定价评分明细"""
    sector_trend: float = 0.0          # 板块趋势 (15)
    relative_strength: float = 0.0      # 相对强弱 (15)
    capital_inflow: float = 0.0         # 资金流入 (15)
    crowding: float = 0.0               # 拥挤度 (15)
    valuation_digestion: float = 0.0    # 估值消化 (15)
    risk_appetite: float = 0.0          # 风险偏好 (15)
    catalyst_priced: float = 0.0        # 催化未定价 (10)


@dataclass
class MarketPricingScore:
    """市场定价评分"""
    total: float
    grade: str
    breakdown: PricingScoreBreakdown
    reasoning: List[str]
    implication: str


class MarketPricingScorer:
    """市场定价评分器"""

    def __init__(self):
        self.weights = {
            "sector_trend": 15,
            "relative_strength": 15,
            "capital_inflow": 15,
            "crowding": 15,
            "valuation_digestion": 15,
            "risk_appetite": 15,
            "catalyst_priced": 10,
        }

    def score(
        self,
        sector_trend: float,
        relative_strength: float,
        capital_inflow: float,
        crowding: float,
        valuation_digestion: float,
        risk_appetite: float,
        catalyst_priced: float,
    ) -> MarketPricingScore:
        """
        计算市场定价评分

        Args:
            sector_trend: 板块趋势评分 (0-15)
            relative_strength: 相对强弱评分 (0-15)
            capital_inflow: 资金流入评分 (0-15)
            crowding: 拥挤度评分 (0-15，越高越不拥挤)
            valuation_digestion: 估值消化评分 (0-15)
            risk_appetite: 风险偏好评分 (0-15)
            catalyst_priced: 催化未定价评分 (0-10)

        Returns:
            MarketPricingScore: 完整评分结果
        """

        score_values(locals(), self.weights)
        # 计算总分
        total = (
            sector_trend +
            relative_strength +
            capital_inflow +
            crowding +
            valuation_digestion +
            risk_appetite +
            catalyst_priced
        )

        # 确定等级
        if total >= 85:
            grade = "A"
        elif total >= 70:
            grade = "B"
        elif total >= 55:
            grade = "C"
        else:
            grade = "D"

        # 构建明细
        breakdown = PricingScoreBreakdown(
            sector_trend=sector_trend,
            relative_strength=relative_strength,
            capital_inflow=capital_inflow,
            crowding=crowding,
            valuation_digestion=valuation_digestion,
            risk_appetite=risk_appetite,
            catalyst_priced=catalyst_priced,
        )

        # 生成推理和市场含义
        reasoning = self._generate_reasoning(breakdown)
        implication = self._generate_implication(total, breakdown)

        return MarketPricingScore(
            total=total,
            grade=grade,
            breakdown=breakdown,
            reasoning=reasoning,
            implication=implication,
        )

    def _generate_reasoning(self, breakdown: PricingScoreBreakdown) -> List[str]:
        """生成评分推理"""
        reasoning = []

        # 板块趋势
        if breakdown.sector_trend >= 13:
            reasoning.append("板块强势 - 跑赢大盘")
        elif breakdown.sector_trend >= 10:
            reasoning.append("板块跟随大盘 - 表现中性")
        else:
            reasoning.append("板块弱势 - 跑输大盘")

        # 相对强弱
        if breakdown.relative_strength >= 13:
            reasoning.append("相对强度高 - 继续强势")
        elif breakdown.relative_strength >= 10:
            reasoning.append("相对强度中等 - 走势中性")
        else:
            reasoning.append("相对强度低 - 走势疲弱")

        # 资金流入
        if breakdown.capital_inflow >= 13:
            reasoning.append("资金持续流入 - 买盘强")
        elif breakdown.capital_inflow >= 10:
            reasoning.append("资金流入放缓 - 买盘中性")
        else:
            reasoning.append("资金流出或持平 - 买盘弱")

        # 拥挤度 (注意：这里评分高表示不拥挤)
        if breakdown.crowding >= 13:
            reasoning.append("拥挤度低 - 有上升空间")
        elif breakdown.crowding >= 10:
            reasoning.append("拥挤度适中 - 关注热度变化")
        else:
            reasoning.append("拥挤度高 - 警惕回调风险")

        # 估值消化
        if breakdown.valuation_digestion >= 13:
            reasoning.append("估值充分消化 - 估值合理")
        elif breakdown.valuation_digestion >= 10:
            reasoning.append("估值部分消化 - 估值略高")
        else:
            reasoning.append("估值未消化 - 估值过高")

        # 风险偏好
        if breakdown.risk_appetite >= 13:
            reasoning.append("市场 Risk On - 风险偏好高")
        elif breakdown.risk_appetite >= 10:
            reasoning.append("市场风险中性 - 风险偏好中性")
        else:
            reasoning.append("市场 Risk Off - 风险偏好低")

        # 催化未定价
        if breakdown.catalyst_priced >= 8:
            reasoning.append("催化剂未定价 - 有上涨空间")
        elif breakdown.catalyst_priced >= 5:
            reasoning.append("催化剂部分定价 - 上涨空间有限")
        else:
            reasoning.append("催化剂已定价 - 上涨空间小")

        return reasoning

    def _generate_implication(self, total: float, breakdown: PricingScoreBreakdown) -> str:
        """生成市场含义"""
        if total >= 85:
            if breakdown.crowding >= 13:
                return "市场定价合理，拥挤度低，赔率高 - 优先配置"
            else:
                return "市场定价合理，但拥挤度高 - 谨慎追高"
        elif total >= 70:
            return "市场定价部分合理 - 有一定上涨空间"
        elif total >= 55:
            return "市场定价偏高 - 上涨空间有限"
        else:
            return "市场已充分定价或过度定价 - 不建议追高"


def main():
    """示例用法"""
    scorer = MarketPricingScorer()

    # 示例评分
    score = scorer.score(
        sector_trend=13,
        relative_strength=12,
        capital_inflow=10,
        crowding=8,
        valuation_digestion=7,
        risk_appetite=12,
        catalyst_priced=3,
    )

    print(f"总分: {score.total}")
    print(f"等级: {score.grade}")
    print(f"市场含义: {score.implication}")
    print("\n明细:")
    for key, value in score.breakdown.__dict__.items():
        print(f"  {key}: {value}")
    print("\n推理:")
    for reason in score.reasoning:
        print(f"  - {reason}")


if __name__ == "__main__":
    main()
