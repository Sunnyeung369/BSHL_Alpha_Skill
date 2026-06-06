"""
BSHL Alpha Skill - Alpha Thesis Score Calculator

计算投研假设评分，评估逻辑是否成立。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class Grade(Enum):
    """评分等级"""
    A = "A"
    B = "B"
    C = "C"
    D = "D"


@dataclass
class ScoreBreakdown:
    """评分明细"""
    demand_inflection: float = 0.0      # 需求拐点 (15)
    supply_chain_bottleneck: float = 0.0  # 供应链卡点 (15)
    company_benefit_certainty: float = 0.0  # 公司受益确定性 (15)
    evidence_quality: float = 0.0        # 证据质量 (15)
    catalyst_timing: float = 0.0         # 催化剂时间 (10)
    valuation_mismatch: float = 0.0      # 估值错配 (10)
    competition: float = 0.0              # 竞争格局 (10)
    contradiction_clarity: float = 0.0   # 反证清晰度 (10)


@dataclass
class AlphaThesisScore:
    """投研假设评分"""
    total: float
    grade: Grade
    breakdown: ScoreBreakdown
    reasoning: List[str]


class AlphaThesisScorer:
    """投研假设评分器"""

    def __init__(self):
        self.weights = {
            "demand_inflection": 15,
            "supply_chain_bottleneck": 15,
            "company_benefit_certainty": 15,
            "evidence_quality": 15,
            "catalyst_timing": 10,
            "valuation_mismatch": 10,
            "competition": 10,
            "contradiction_clarity": 10,
        }

    def score(
        self,
        demand_inflection: float,
        supply_chain_bottleneck: float,
        company_benefit_certainty: float,
        evidence_quality: float,
        catalyst_timing: float,
        valuation_mismatch: float,
        competition: float,
        contradiction_clarity: float,
    ) -> AlphaThesisScore:
        """
        计算投研假设评分

        Args:
            demand_inflection: 需求拐点评分 (0-15)
            supply_chain_bottleneck: 供应链卡点评分 (0-15)
            company_benefit_certainty: 公司受益确定性评分 (0-15)
            evidence_quality: 证据质量评分 (0-15)
            catalyst_timing: 催化剂时间评分 (0-10)
            valuation_mismatch: 估值错配评分 (0-10)
            competition: 竞争格局评分 (0-10)
            contradiction_clarity: 反证清晰度评分 (0-10)

        Returns:
            AlphaThesisScore: 完整评分结果
        """

        # 计算总分
        total = (
            demand_inflection +
            supply_chain_bottleneck +
            company_benefit_certainty +
            evidence_quality +
            catalyst_timing +
            valuation_mismatch +
            competition +
            contradiction_clarity
        )

        # 确定等级
        if total >= 85:
            grade = Grade.A
        elif total >= 70:
            grade = Grade.B
        elif total >= 55:
            grade = Grade.C
        else:
            grade = Grade.D

        # 构建明细
        breakdown = ScoreBreakdown(
            demand_inflection=demand_inflection,
            supply_chain_bottleneck=supply_chain_bottleneck,
            company_benefit_certainty=company_benefit_certainty,
            evidence_quality=evidence_quality,
            catalyst_timing=catalyst_timing,
            valuation_mismatch=valuation_mismatch,
            competition=competition,
            contradiction_clarity=contradiction_clarity,
        )

        # 生成推理
        reasoning = self._generate_reasoning(breakdown)

        return AlphaThesisScore(
            total=total,
            grade=grade,
            breakdown=breakdown,
            reasoning=reasoning,
        )

    def _generate_reasoning(self, breakdown: ScoreBreakdown) -> List[str]:
        """生成评分推理"""
        reasoning = []

        # 需求拐点
        if breakdown.demand_inflection >= 13:
            reasoning.append("需求拐点明确 - 需求增长信号强")
        elif breakdown.demand_inflection >= 10:
            reasoning.append("需求拐点存在 - 需求增长信号中等")
        else:
            reasoning.append("需求拐点不明确 - 需求增长信号弱")

        # 供应链卡点
        if breakdown.supply_chain_bottleneck >= 13:
            reasoning.append("供应链卡点明确 - 供给受限")
        elif breakdown.supply_chain_bottleneck >= 10:
            reasoning.append("供应链存在卡点 - 供给部分受限")
        else:
            reasoning.append("供应链卡点不明确 - 供给充足")

        # 公司受益确定性
        if breakdown.company_benefit_certainty >= 13:
            reasoning.append("公司直接受益 - 受益路径清晰")
        elif breakdown.company_benefit_certainty >= 10:
            reasoning.append("公司间接受益 - 受益路径较清晰")
        else:
            reasoning.append("公司受益不确定 - 受益路径模糊")

        # 证据质量
        if breakdown.evidence_quality >= 13:
            reasoning.append("证据质量高 - 多条强证据")
        elif breakdown.evidence_quality >= 10:
            reasoning.append("证据质量中等 - 有强证据也有弱证据")
        else:
            reasoning.append("证据质量低 - 缺少强证据")

        # 催化剂时间
        if breakdown.catalyst_timing >= 8:
            reasoning.append("催化剂临近 - 时间窗口明确")
        elif breakdown.catalyst_timing >= 5:
            reasoning.append("催化剂存在 - 时间窗口较远")
        else:
            reasoning.append("催化剂不明确 - 缺少催化剂")

        # 估值错配
        if breakdown.valuation_mismatch >= 8:
            reasoning.append("估值错配明显 - 上涨空间大")
        elif breakdown.valuation_mismatch >= 5:
            reasoning.append("估值部分错配 - 有一定上涨空间")
        else:
            reasoning.append("估值已充分定价 - 上涨空间有限")

        # 竞争格局
        if breakdown.competition >= 8:
            reasoning.append("竞争格局好 - 公司地位稳固")
        elif breakdown.competition >= 5:
            reasoning.append("竞争格局中等 - 面临一定竞争")
        else:
            reasoning.append("竞争格局差 - 竞争压力大")

        # 反证清晰度
        if breakdown.contradiction_clarity >= 8:
            reasoning.append("反证清晰 - 风险点明确")
        elif breakdown.contradiction_clarity >= 5:
            reasoning.append("反证较清晰 - 主要风险点已识别")
        else:
            reasoning.append("反证不清晰 - 风险点模糊")

        return reasoning

    def score_from_dict(self, data: Dict) -> AlphaThesisScore:
        """从字典计算评分"""
        return self.score(
            demand_inflection=data.get("demand_inflection", 0),
            supply_chain_bottleneck=data.get("supply_chain_bottleneck", 0),
            company_benefit_certainty=data.get("company_benefit_certainty", 0),
            evidence_quality=data.get("evidence_quality", 0),
            catalyst_timing=data.get("catalyst_timing", 0),
            valuation_mismatch=data.get("valuation_mismatch", 0),
            competition=data.get("competition", 0),
            contradiction_clarity=data.get("contradiction_clarity", 0),
        )


def main():
    """示例用法"""
    scorer = AlphaThesisScorer()

    # 示例评分
    score = scorer.score(
        demand_inflection=14,
        supply_chain_bottleneck=13,
        company_benefit_certainty=14,
        evidence_quality=14,
        catalyst_timing=9,
        valuation_mismatch=6,
        competition=8,
        contradiction_clarity=10,
    )

    print(f"总分: {score.total}")
    print(f"等级: {score.grade.value}")
    print("\n明细:")
    for key, value in score.breakdown.__dict__.items():
        print(f"  {key}: {value}")
    print("\n推理:")
    for reason in score.reasoning:
        print(f"  - {reason}")


if __name__ == "__main__":
    main()
