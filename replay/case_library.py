"""
BSHL Alpha Skill - Replay Case Library

回放案例库，用于验证规则有效性。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
from enum import Enum


class CaseType(Enum):
    """案例类型"""
    GOOD_LOGIC_PRICED_IN = "good_logic_priced_in"  # 好逻辑但价格已透支
    GOOD_COMPANY_RISK_OFF = "good_company_risk_off"  # 好公司但市场 Risk Off
    SMALL_CAP_PUMP_DUMP = "small_cap_pump_dump"  # 小票社媒拉盘后暴跌
    EARNINGS_BEAT_GAP_DOWN = "earnings_beat_gap_down"  # 财报超预期但高开低走
    THEME_STRONG_SHADOW_WEAK = "theme_strong_shadow_weak"  # 主题强但影子股不涨
    LEADER_STRONG_FOLLOWER_FAIL = "leader_strong_follower_fail"  # 龙头强势，跟风股失效
    CRYPTO_ONCHAIN_STRONG_PRICE_BREAKDOWN = "crypto_onchain_strong_price_breakdown"  # 链上信号强但价格破位
    ETF_BETTER_THAN_STOCKS = "etf_better_than_stocks"  # ETF 强于个股
    EVIDENCE_STRONG_REVENUE_SLOW = "evidence_strong_revenue_slow"  # 产业链证据强但收入兑现慢
    HIGH_CROWD_REVERSAL = "high_crowd_reversal"  # 高拥挤交易被反杀


class CaseOutcome(Enum):
    """案例结果"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"


@dataclass
class ReplayCase:
    """回放案例"""
    id: str
    title: str
    case_type: CaseType
    symbol: str
    asset_class: str  # US_STOCK, HK_STOCK, CRYPTO, etc.

    # 原始分析
    original_date: date
    original_price: float
    original_status: str  # Research Only, Watchlist, Trade Ready, etc.
    alpha_thesis_score: float
    market_pricing_score: float
    trade_readiness_score: float
    risk_governor_decision: str

    # 实际结果
    outcome_date: date
    outcome_price: float
    outcome: CaseOutcome
    price_change_percent: float

    # 案例描述
    description: str
    thesis: str
    key_evidence: List[str]
    market_regime: str

    # 结果分析
    success_reasons: List[str]
    failure_reasons: List[str]
    lessons_learned: List[str]


class ReplayCaseLibrary:
    """回放案例库"""

    def __init__(self):
        self.cases: Dict[str, ReplayCase] = {}
        self._init_default_cases()

    def _init_default_cases(self):
        """初始化默认案例"""
        # 添加示例案例
        case = ReplayCase(
            id="CASE-001",
            title="好逻辑但价格已透支",
            case_type=CaseType.GOOD_LOGIC_PRICED_IN,
            symbol="NVDA",
            asset_class="US_STOCK",
            original_date=date(2025, 3, 1),
            original_price=800.0,
            original_status="Trade Ready",
            alpha_thesis_score=85,
            market_pricing_score=90,  # 市场已定价
            trade_readiness_score=75,
            risk_governor_decision="Pass",
            outcome_date=date(2025, 6, 1),
            outcome_price=750.0,
            outcome=CaseOutcome.FAILURE,
            price_change_percent=-6.25,
            description="AI 逻辑强，但价格在 3 月已充分定价，后续上涨空间有限",
            thesis="AI 数据中心建设推动 GPU 需求",
            key_evidence=["数据中心收入增长 400%", "CEO 确认需求强劲"],
            market_regime="Risk On",
            success_reasons=["逻辑判断正确", "证据准确"],
            failure_reasons=["市场定价程度低估", "拥挤度评估不足"],
            lessons_learned=["即使逻辑好，已定价的标的也要谨慎"],
        )
        self.cases[case.id] = case

    def add_case(self, case: ReplayCase):
        """添加案例"""
        self.cases[case.id] = case

    def get_case(self, case_id: str) -> Optional[ReplayCase]:
        """获取案例"""
        return self.cases.get(case_id)

    def get_cases_by_type(self, case_type: CaseType) -> List[ReplayCase]:
        """按类型获取案例"""
        return [c for c in self.cases.values() if c.case_type == case_type]

    def get_cases_by_symbol(self, symbol: str) -> List[ReplayCase]:
        """按标的获取案例"""
        return [c for c in self.cases.values() if c.symbol == symbol]

    def get_all_cases(self) -> List[ReplayCase]:
        """获取所有案例"""
        return list(self.cases.values())

    def get_success_rate(self) -> float:
        """计算成功率"""
        total = len(self.cases)
        if total == 0:
            return 0.0
        success = sum(1 for c in self.cases.values() if c.outcome == CaseOutcome.SUCCESS)
        return success / total

    def get_success_rate_by_type(self, case_type: CaseType) -> float:
        """按类型计算成功率"""
        cases = self.get_cases_by_type(case_type)
        if not cases:
            return 0.0
        success = sum(1 for c in cases if c.outcome == CaseOutcome.SUCCESS)
        return success / len(cases)


class RuleValidator:
    """规则验证器"""

    def __init__(self, case_library: ReplayCaseLibrary):
        self.case_library = case_library
        self.validation_results: Dict[str, Dict] = {}

    def validate_rule(self, rule_id: str, rule_description: str) -> Dict:
        """验证规则有效性"""
        # 找到相关案例
        relevant_cases = self._find_relevant_cases(rule_id)

        if not relevant_cases:
            return {
                "rule_id": rule_id,
                "valid": False,
                "reason": "No relevant cases found",
                "cases_tested": 0,
            }

        # 计算规则有效性
        success_count = sum(1 for c in relevant_cases if c.outcome == CaseOutcome.SUCCESS)
        total_count = len(relevant_cases)
        success_rate = success_count / total_count if total_count > 0 else 0

        # 判断规则是否有效
        is_valid = success_rate >= 0.6  # 60% 成功率为阈值

        return {
            "rule_id": rule_id,
            "rule_description": rule_description,
            "valid": is_valid,
            "success_rate": success_rate,
            "cases_tested": total_count,
            "cases": [c.id for c in relevant_cases],
            "recommendation": self._generate_recommendation(is_valid, success_rate),
        }

    def _find_relevant_cases(self, rule_id: str) -> List[ReplayCase]:
        """找到相关案例"""
        # 简化实现：返回所有案例
        # 实际实现需要根据规则 ID 匹配相关案例
        return self.case_library.get_all_cases()

    def _generate_recommendation(self, is_valid: bool, success_rate: float) -> str:
        """生成建议"""
        if is_valid:
            return "规则有效，建议保留"
        elif success_rate < 0.4:
            return "规则失效，建议删除或修改"
        else:
            return "规则效果一般，建议优化"

    def validate_all_rules(self, rules: Dict[str, str]) -> Dict[str, Dict]:
        """验证所有规则"""
        results = {}
        for rule_id, description in rules.items():
            results[rule_id] = self.validate_rule(rule_id, description)
        return results


class PerformanceReport:
    """性能报告"""

    def __init__(self, case_library: ReplayCaseLibrary):
        self.case_library = case_library

    def generate_report(self) -> Dict:
        """生成性能报告"""
        cases = self.case_library.get_all_cases()

        # 基础统计
        total_cases = len(cases)
        success_cases = sum(1 for c in cases if c.outcome == CaseOutcome.SUCCESS)
        failure_cases = sum(1 for c in cases if c.outcome == CaseOutcome.FAILURE)
        partial_cases = sum(1 for c in cases if c.outcome == CaseOutcome.PARTIAL)

        # 按类型统计
        type_stats = {}
        for case_type in CaseType:
            type_cases = self.case_library.get_cases_by_type(case_type)
            if type_cases:
                type_success = sum(1 for c in type_cases if c.outcome == CaseOutcome.SUCCESS)
                type_stats[case_type.value] = {
                    "total": len(type_cases),
                    "success": type_success,
                    "success_rate": type_success / len(type_cases),
                }

        # 平均价格变化
        avg_change = sum(c.price_change_percent for c in cases) / total_cases if total_cases > 0 else 0

        return {
            "summary": {
                "total_cases": total_cases,
                "success": success_cases,
                "failure": failure_cases,
                "partial": partial_cases,
                "success_rate": success_cases / total_cases if total_cases > 0 else 0,
                "avg_price_change": avg_change,
            },
            "by_type": type_stats,
            "top_lessons": self._get_top_lessons(cases),
            "common_failures": self._get_common_failures(cases),
        }

    def _get_top_lessons(self, cases: List[ReplayCase]) -> List[str]:
        """获取最重要的经验"""
        all_lessons = []
        for case in cases:
            all_lessons.extend(case.lessons_learned)

        # 统计频率
        lesson_count = {}
        for lesson in all_lessons:
            lesson_count[lesson] = lesson_count.get(lesson, 0) + 1

        # 排序并返回前 5
        sorted_lessons = sorted(lesson_count.items(), key=lambda x: x[1], reverse=True)
        return [lesson for lesson, _ in sorted_lessons[:5]]

    def _get_common_failures(self, cases: List[ReplayCase]) -> List[str]:
        """获取常见失败原因"""
        all_failures = []
        for case in cases:
            if case.outcome == CaseOutcome.FAILURE:
                all_failures.extend(case.failure_reasons)

        # 统计频率
        failure_count = {}
        for failure in all_failures:
            failure_count[failure] = failure_count.get(failure, 0) + 1

        # 排序并返回前 5
        sorted_failures = sorted(failure_count.items(), key=lambda x: x[1], reverse=True)
        return [failure for failure, _ in sorted_failures[:5]]


# 全局实例
replay_case_library = ReplayCaseLibrary()
rule_validator = RuleValidator(replay_case_library)
performance_report = PerformanceReport(replay_case_library)


def main():
    """示例用法"""
    # 生成性能报告
    report = performance_report.generate_report()

    print("=== BSHL Alpha Skill 回放性能报告 ===\n")
    print(f"总案例数: {report['summary']['total_cases']}")
    print(f"成功率: {report['summary']['success_rate']*100:.1f}%")
    print(f"平均价格变化: {report['summary']['avg_price_change']:+.2f}%")

    print("\n按类型统计:")
    for case_type, stats in report['by_type'].items():
        print(f"  {case_type}: {stats['success_rate']*100:.1f}% ({stats['success']}/{stats['total']})")

    print("\n最重要的经验:")
    for i, lesson in enumerate(report['top_lessons'], 1):
        print(f"  {i}. {lesson}")

    print("\n常见失败原因:")
    for i, failure in enumerate(report['common_failures'], 1):
        print(f"  {i}. {failure}")


if __name__ == "__main__":
    main()
