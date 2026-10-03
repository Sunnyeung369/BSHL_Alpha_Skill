"""
BSHL Alpha Skill - Trade Readiness Score Calculator

计算交易准备评分，评估现在能否进入交易准备。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from .validation import optional_bool, score_values


class TradeStatus(Enum):
    """交易准备状态"""
    TRADE_READY = "Trade Ready"
    WATCH_CLOSELY = "Watch Closely"
    WAIT = "Wait"
    NO_TRADE = "No Trade"


@dataclass
class TradeScoreBreakdown:
    """交易评分明细"""
    parent_cycle_direction: float = 0.0   # 母周期方向 (15)
    child_cycle_structure: float = 0.0    # 子周期结构 (15)
    breakout_confirmation: float = 0.0     # 突破确认 (15)
    pullback_quality: float = 0.0         # 回踩质量 (10)
    volume_confirmation: float = 0.0       # 成交量确认 (10)
    stop_loss_clarity: float = 0.0        # 止损清晰度 (15)
    reward_risk: float = 0.0               # 盈亏比 (15)
    volatility_controlled: float = 0.0     # 波动可控 (5)


@dataclass
class TradeReadinessScore:
    """交易准备评分"""
    total: float
    status: TradeStatus
    breakdown: TradeScoreBreakdown
    reasoning: List[str]
    action: str
    closed_bar_confirmed: Optional[bool] = None
    stop_loss_defined: Optional[bool] = None


class TradeReadinessScorer:
    """交易准备评分器"""

    def __init__(self):
        self.weights = {
            "parent_cycle_direction": 15,
            "child_cycle_structure": 15,
            "breakout_confirmation": 15,
            "pullback_quality": 10,
            "volume_confirmation": 10,
            "stop_loss_clarity": 15,
            "reward_risk": 15,
            "volatility_controlled": 5,
        }

    def score(
        self,
        parent_cycle_direction: float,
        child_cycle_structure: float,
        breakout_confirmation: float,
        pullback_quality: float,
        volume_confirmation: float,
        stop_loss_clarity: float,
        reward_risk: float,
        volatility_controlled: float,
        closed_bar_confirmed: Optional[bool] = None,
        stop_loss_defined: Optional[bool] = None,
    ) -> TradeReadinessScore:
        """
        计算交易准备评分

        Args:
            parent_cycle_direction: 母周期方向评分 (0-15)
            child_cycle_structure: 子周期结构评分 (0-15)
            breakout_confirmation: 突破确认评分 (0-15)
            pullback_quality: 回踩质量评分 (0-10)
            volume_confirmation: 成交量确认评分 (0-10)
            stop_loss_clarity: 止损清晰度评分 (0-15)
            reward_risk: 盈亏比评分 (0-15)
            volatility_controlled: 波动可控评分 (0-5)

        Returns:
            TradeReadinessScore: 完整评分结果
        """

        score_values(locals(), self.weights)
        optional_bool("closed_bar_confirmed", closed_bar_confirmed)
        optional_bool("stop_loss_defined", stop_loss_defined)
        # 计算总分
        total = (
            parent_cycle_direction +
            child_cycle_structure +
            breakout_confirmation +
            pullback_quality +
            volume_confirmation +
            stop_loss_clarity +
            reward_risk +
            volatility_controlled
        )

        # 确定状态
        if stop_loss_clarity < 10 or stop_loss_defined is False:
            status = TradeStatus.NO_TRADE
        elif closed_bar_confirmed is not True or stop_loss_defined is not True:
            status = TradeStatus.WAIT
        elif breakout_confirmation < 13:
            status = TradeStatus.WAIT
        elif total >= 85:
            status = TradeStatus.TRADE_READY
        elif total >= 70:
            status = TradeStatus.WATCH_CLOSELY
        elif total >= 55:
            status = TradeStatus.WAIT
        else:
            status = TradeStatus.NO_TRADE

        # 构建明细
        breakdown = TradeScoreBreakdown(
            parent_cycle_direction=parent_cycle_direction,
            child_cycle_structure=child_cycle_structure,
            breakout_confirmation=breakout_confirmation,
            pullback_quality=pullback_quality,
            volume_confirmation=volume_confirmation,
            stop_loss_clarity=stop_loss_clarity,
            reward_risk=reward_risk,
            volatility_controlled=volatility_controlled,
        )

        # 生成推理和行动建议
        reasoning = self._generate_reasoning(breakdown)
        if closed_bar_confirmed is not True:
            reasoning.append("收盘确认缺失或尚未完成，不升级交易准备")
        if stop_loss_defined is not True:
            reasoning.append("实际止损位尚未确认，不进入执行准备")
        action = self._generate_action(status, breakdown)

        return TradeReadinessScore(
            total=total,
            status=status,
            breakdown=breakdown,
            reasoning=reasoning,
            action=action,
            closed_bar_confirmed=closed_bar_confirmed,
            stop_loss_defined=stop_loss_defined,
        )

    def _generate_reasoning(self, breakdown: TradeScoreBreakdown) -> List[str]:
        """生成评分推理"""
        reasoning = []

        # 母周期方向
        if breakdown.parent_cycle_direction >= 13:
            reasoning.append("母周期明确上涨 - 顺势交易")
        elif breakdown.parent_cycle_direction >= 10:
            reasoning.append("母周期震荡 - 谨慎交易")
        else:
            reasoning.append("母周期下跌 - 避免交易")

        # 子周期结构
        if breakdown.child_cycle_structure >= 13:
            reasoning.append("子周期位置理想 - 入场时机好")
        elif breakdown.child_cycle_structure >= 10:
            reasoning.append("子周期位置一般 - 可等待更好时机")
        else:
            reasoning.append("子周期位置不利 - 不建议入场")

        # 突破确认
        if breakdown.breakout_confirmation >= 13:
            reasoning.append("突破已确认 - 可跟随")
        elif breakdown.breakout_confirmation >= 10:
            reasoning.append("突破待确认 - 观察验证")
        else:
            reasoning.append("无有效突破 - 不交易")

        # 回踩质量
        if breakdown.pullback_quality >= 8:
            reasoning.append("回踩健康 - 入场时机佳")
        elif breakdown.pullback_quality >= 5:
            reasoning.append("回踩质量一般 - 可考虑")
        else:
            reasoning.append("无回踩或回踩破位 - 不交易")

        # 成交量确认
        if breakdown.volume_confirmation >= 8:
            reasoning.append("成交量确认 - 资金支持强")
        elif breakdown.volume_confirmation >= 5:
            reasoning.append("成交量一般 - 资金支持中等")
        else:
            reasoning.append("成交量不足 - 缺少资金支持")

        # 止损清晰度
        if breakdown.stop_loss_clarity >= 13:
            reasoning.append("止损位清晰 - 风险可控")
        elif breakdown.stop_loss_clarity >= 10:
            reasoning.append("止损位较清晰 - 风险较可控")
        else:
            reasoning.append("止损位模糊 - 风险不可控")

        # 盈亏比
        if breakdown.reward_risk >= 13:
            reasoning.append("盈亏比优秀 - 风险收益比佳")
        elif breakdown.reward_risk >= 10:
            reasoning.append("盈亏比良好 - 风险收益比合理")
        else:
            reasoning.append("盈亏比不佳 - 风险大于收益")

        # 波动可控
        if breakdown.volatility_controlled >= 4:
            reasoning.append("波动可控 - 适合交易")
        else:
            reasoning.append("波动过大 - 不适合交易")

        return reasoning

    def _generate_action(self, status: TradeStatus, breakdown: TradeScoreBreakdown) -> str:
        """生成行动建议"""
        if status == TradeStatus.TRADE_READY:
            return "具备交易准备 - 可进入执行准备，设定具体入场计划"
        elif status == TradeStatus.WATCH_CLOSELY:
            return "密切观察 - 等待结构确认后进入交易准备"
        elif status == TradeStatus.WAIT:
            if breakdown.child_cycle_structure < 10:
                return "等待 - 当前结构不利，等待回踩确认"
            elif breakdown.breakout_confirmation < 10:
                return "等待 - 等待突破确认"
            else:
                return "等待 - 等待更好的交易时机"
        else:
            return "不交易 - 当前不适合交易，继续观察"


def main():
    """示例用法"""
    scorer = TradeReadinessScorer()

    # 示例评分
    score = scorer.score(
        parent_cycle_direction=14,
        child_cycle_structure=8,
        breakout_confirmation=12,
        pullback_quality=5,
        volume_confirmation=8,
        stop_loss_clarity=12,
        reward_risk=5,
        volatility_controlled=5,
    )

    print(f"总分: {score.total}")
    print(f"状态: {score.status.value}")
    print(f"行动: {score.action}")
    print("\n明细:")
    for key, value in score.breakdown.__dict__.items():
        print(f"  {key}: {value}")
    print("\n推理:")
    for reason in score.reasoning:
        print(f"  - {reason}")


if __name__ == "__main__":
    main()
