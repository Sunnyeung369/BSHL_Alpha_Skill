"""
BSHL Alpha Skill - 统一评分入口

提供统一的评分接口，整合所有评分模块。
"""

from dataclasses import dataclass
from datetime import date as calendar_date
from typing import Optional
from .alpha_thesis_score import AlphaThesisScorer, AlphaThesisScore, Grade
from .market_pricing_score import MarketPricingScorer, MarketPricingScore
from .trade_readiness_score import TradeReadinessScorer, TradeReadinessScore, TradeStatus
from .risk_governor_score import RiskGovernorScorer, RiskGovernorScore, RiskDecision


@dataclass
class BSHLAlphaResult:
    """完整评分结果"""
    ticker: str
    date: str
    alpha_thesis: AlphaThesisScore
    market_pricing: MarketPricingScore
    trade_readiness: TradeReadinessScore
    risk_governor: RiskGovernorScore
    final_status: str


class BSHLAlphaScorer:
    """BSHL Alpha 统一评分器"""

    def __init__(self):
        self.alpha_scorer = AlphaThesisScorer()
        self.pricing_scorer = MarketPricingScorer()
        self.trade_scorer = TradeReadinessScorer()
        self.risk_scorer = RiskGovernorScorer()

    def score_complete(
        self,
        ticker: str,
        date: str,
        # Alpha Thesis 参数
        demand_inflection: float,
        supply_chain_bottleneck: float,
        company_benefit_certainty: float,
        evidence_quality: float,
        catalyst_timing: float,
        valuation_mismatch: float,
        competition: float,
        contradiction_clarity: float,
        # Market Pricing 参数
        sector_trend: float,
        relative_strength: float,
        capital_inflow: float,
        crowding: float,
        valuation_digestion: float,
        risk_appetite: float,
        catalyst_priced: float,
        # Trade Readiness 参数
        parent_cycle_direction: float,
        child_cycle_structure: float,
        breakout_confirmation: float,
        pullback_quality: float,
        volume_confirmation: float,
        stop_loss_clarity: float,
        reward_risk: float,
        volatility_controlled: float,
        # Risk Governor 参数
        liquidity: bool,
        volatility_ok: bool,
        evidence_ok: bool,
        social_ok: bool,
        earnings_ok: bool,
        regulatory_ok: bool,
        price_ok: bool,
        stop_ok: bool,
        position_ok: bool,
        correlation_ok: bool,
        closed_bar_confirmed: Optional[bool] = None,
        stop_loss_defined: Optional[bool] = None,
        # Risk Governor 详细说明
        **risk_details,
    ) -> BSHLAlphaResult:
        """
        计算完整评分

        Returns:
            CompleteScore: 完整评分结果
        """

        if not isinstance(ticker, str) or not ticker.strip():
            raise ValueError("ticker must be a nonempty string")
        if not isinstance(date, str):
            raise TypeError("date must be an ISO date string")
        if calendar_date.fromisoformat(date).isoformat() != date:
            raise ValueError("date must use YYYY-MM-DD")
        # 计算各层评分
        alpha_thesis = self.alpha_scorer.score(
            demand_inflection=demand_inflection,
            supply_chain_bottleneck=supply_chain_bottleneck,
            company_benefit_certainty=company_benefit_certainty,
            evidence_quality=evidence_quality,
            catalyst_timing=catalyst_timing,
            valuation_mismatch=valuation_mismatch,
            competition=competition,
            contradiction_clarity=contradiction_clarity,
        )

        market_pricing = self.pricing_scorer.score(
            sector_trend=sector_trend,
            relative_strength=relative_strength,
            capital_inflow=capital_inflow,
            crowding=crowding,
            valuation_digestion=valuation_digestion,
            risk_appetite=risk_appetite,
            catalyst_priced=catalyst_priced,
        )

        trade_readiness = self.trade_scorer.score(
            parent_cycle_direction=parent_cycle_direction,
            child_cycle_structure=child_cycle_structure,
            breakout_confirmation=breakout_confirmation,
            pullback_quality=pullback_quality,
            volume_confirmation=volume_confirmation,
            stop_loss_clarity=stop_loss_clarity,
            reward_risk=reward_risk,
            volatility_controlled=volatility_controlled,
            closed_bar_confirmed=closed_bar_confirmed,
            stop_loss_defined=stop_loss_defined,
        )

        risk_governor = self.risk_scorer.check(
            liquidity=liquidity,
            volatility=volatility_ok,
            evidence_quality=evidence_ok,
            social_crowding=social_ok,
            earnings_risk=earnings_ok,
            regulatory_uncertainty=regulatory_ok,
            price_location=price_ok,
            stop_loss_distance=stop_ok,
            position_exposure=position_ok,
            correlation=correlation_ok,
            **risk_details,
        )

        # 确定最终状态
        final_status = self._determine_final_status(
            alpha_thesis=alpha_thesis,
            market_pricing=market_pricing,
            trade_readiness=trade_readiness,
            risk_governor=risk_governor,
        )

        return BSHLAlphaResult(
            ticker=ticker,
            date=date,
            alpha_thesis=alpha_thesis,
            market_pricing=market_pricing,
            trade_readiness=trade_readiness,
            risk_governor=risk_governor,
            final_status=final_status,
        )

    def _determine_final_status(
        self,
        alpha_thesis: AlphaThesisScore,
        market_pricing: MarketPricingScore,
        trade_readiness: TradeReadinessScore,
        risk_governor: RiskGovernorScore,
    ) -> str:
        """确定最终状态"""

        # Hard constraints dominate soft scores. These are readiness gates,
        # not calibrated probabilities of investment returns.
        decision = risk_governor.decision
        if decision is RiskDecision.VETO:
            return "Veto"
        if trade_readiness.status is TradeStatus.NO_TRADE:
            return "Avoid"
        if (decision is RiskDecision.WATCH_ONLY or alpha_thesis.grade is Grade.D
                or alpha_thesis.breakdown.evidence_quality < 10):
            return "Research Only"
        if decision is RiskDecision.WAIT:
            return "Wait Pullback"
        if decision in (RiskDecision.WAIT_CONFIRMATION, RiskDecision.REDUCE_SIZE):
            return "Watchlist"
        if decision is not RiskDecision.PASS:
            return "Research Only"
        if trade_readiness.status is TradeStatus.WAIT:
            return "Wait Pullback"
        if trade_readiness.status is TradeStatus.WATCH_CLOSELY or market_pricing.grade == "D":
            return "Watchlist"
        if trade_readiness.status is TradeStatus.TRADE_READY:
            return "Trade Ready"

        # 默认为 Research Only
        return "Research Only"

    def print_score(self, score: BSHLAlphaResult):
        """打印评分结果"""
        print(f"\n{'='*60}")
        print(f"BSHL Alpha Skill 完整评分 - {score.ticker}")
        print(f"日期: {score.date}")
        print(f"{'='*60}\n")

        # Alpha Thesis
        print(f"【Alpha Thesis 评分】")
        print(f"总分: {score.alpha_thesis.total}/100 ({score.alpha_thesis.grade.value})")
        for reason in score.alpha_thesis.reasoning:
            print(f"  - {reason}")

        # Market Pricing
        print(f"\n【Market Pricing 评分】")
        print(f"总分: {score.market_pricing.total}/100 ({score.market_pricing.grade})")
        print(f"市场含义: {score.market_pricing.implication}")

        # Trade Readiness
        print(f"\n【Trade Readiness 评分】")
        print(f"总分: {score.trade_readiness.total}/100 ({score.trade_readiness.status.value})")
        for reason in score.trade_readiness.reasoning:
            print(f"  - {reason}")
        print(f"行动: {score.trade_readiness.action}")

        # Risk Governor
        print(f"\n【Risk Governor 检查】")
        print(f"决策: {score.risk_governor.decision.value}")
        for reason in score.risk_governor.reasoning:
            print(f"  - {reason}")
        print(f"建议: {score.risk_governor.suggested_action}")

        # 最终状态
        print(f"\n【最终状态】")
        print(f"状态: {score.final_status}")
        print(f"{'='*60}\n")


# Compatibility with the original misspelled API and result name.
BSHEAlphaScorer = BSHLAlphaScorer
CompleteScore = BSHLAlphaResult


def main():
    """示例用法"""
    scorer = BSHLAlphaScorer()

    # 示例评分
    result = scorer.score_complete(
        ticker="NVDA",
        date="2026-08-01",
        # Alpha Thesis
        demand_inflection=14,
        supply_chain_bottleneck=13,
        company_benefit_certainty=14,
        evidence_quality=14,
        catalyst_timing=9,
        valuation_mismatch=6,
        competition=8,
        contradiction_clarity=10,
        # Market Pricing
        sector_trend=13,
        relative_strength=12,
        capital_inflow=10,
        crowding=8,
        valuation_digestion=7,
        risk_appetite=12,
        catalyst_priced=3,
        # Trade Readiness
        parent_cycle_direction=14,
        child_cycle_structure=8,
        breakout_confirmation=12,
        pullback_quality=5,
        volume_confirmation=8,
        stop_loss_clarity=12,
        reward_risk=5,
        volatility_controlled=5,
        # Risk Governor
        liquidity=True,
        volatility_ok=True,
        evidence_ok=True,
        social_ok=True,
        earnings_ok=True,
        regulatory_ok=True,
        price_ok=False,
        stop_ok=True,
        position_ok=True,
        correlation_ok=False,
        price_detail="价格远离 20 日均线超过 2 倍 ATR",
        correlation_detail="与半导体板块相关性 0.85",
    )

    scorer.print_score(result)


if __name__ == "__main__":
    main()
