"""
BSHL Alpha Skill - Personal Evolution System

用户专属进化系统，根据个人真实使用历史实现规则自适应。
"""

from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
import json
from pathlib import Path


class DecisionType(Enum):
    """决策类型"""
    TRADE = "trade"           # 交易
    SKIP = "skip"             # 跳过
    WATCH = "watch"           # 观察
    VETO = "veto"             # 风控否决


class DecisionOutcome(Enum):
    """决策结果"""
    PROFIT = "profit"         # 盈利
    LOSS = "loss"             # 亏损
    BREAK_EVEN = "break_even" # 盈亏平衡
    MISSED = "missed"         # 错过机会
    AVOIDED = "avoided"       # 成功避险


@dataclass
class PersonalDecision:
    """个人决策记录"""
    id: str
    timestamp: datetime
    symbol: str
    asset_class: str

    # 原始判断
    alpha_thesis_score: float
    market_pricing_score: float
    trade_readiness_score: float
    risk_governor_decision: str
    final_status: str  # Research Only, Watchlist, Trade Ready, etc.

    # 用户决策
    user_decision: DecisionType
    user_action: str  # 具体动作描述

    # 实际结果
    outcome: DecisionOutcome
    entry_price: Optional[float] = None
    exit_price: Optional[float] = None
    price_change_percent: Optional[float] = None

    # 反思
    user_notes: str = ""
    lessons_learned: List[str] = field(default_factory=list)
    rules_to_adjust: List[str] = field(default_factory=list)


@dataclass
class PersonalRule:
    """个人规则"""
    id: str
    description: str
    category: str  # evidence, structure, risk, timing, etc.
    enabled: bool = True
    weight: float = 1.0  # 规则权重，影响评分
    success_count: int = 0
    failure_count: int = 0
    last_applied: Optional[datetime] = None
    evolution_history: List[Dict] = field(default_factory=list)

    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 0.5

    def should_disable(self) -> bool:
        """判断是否应该禁用（成功率过低）"""
        total = self.success_count + self.failure_count
        return total >= 5 and self.get_success_rate() < 0.4


class PersonalEvolutionEngine:
    """个人进化引擎"""

    def __init__(self, user_id: str, data_dir: Optional[Path] = None):
        self.user_id = user_id
        self.data_dir = data_dir or Path.home() / ".bshl" / user_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.decisions: List[PersonalDecision] = []
        self.rules: Dict[str, PersonalRule] = {}

        self._load_data()
        self._init_default_rules()

    def _load_data(self):
        """加载用户数据"""
        decisions_file = self.data_dir / "decisions.jsonl"
        if decisions_file.exists():
            with open(decisions_file, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    self.decisions.append(self._parse_decision(data))

        rules_file = self.data_dir / "rules.json"
        if rules_file.exists():
            with open(rules_file, "r", encoding="utf-8") as f:
                rules_data = json.load(f)
                for rule_id, rule_data in rules_data.items():
                    self.rules[rule_id] = PersonalRule(**rule_data)

    def _parse_decision(self, data: Dict) -> PersonalDecision:
        """解析决策数据"""
        return PersonalDecision(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            symbol=data["symbol"],
            asset_class=data["asset_class"],
            alpha_thesis_score=data["alpha_thesis_score"],
            market_pricing_score=data["market_pricing_score"],
            trade_readiness_score=data["trade_readiness_score"],
            risk_governor_decision=data["risk_governor_decision"],
            final_status=data["final_status"],
            user_decision=DecisionType(data["user_decision"]),
            user_action=data["user_action"],
            outcome=DecisionOutcome(data["outcome"]),
            entry_price=data.get("entry_price"),
            exit_price=data.get("exit_price"),
            price_change_percent=data.get("price_change_percent"),
            user_notes=data.get("user_notes", ""),
            lessons_learned=data.get("lessons_learned", []),
            rules_to_adjust=data.get("rules_to_adjust", []),
        )

    def _init_default_rules(self):
        """初始化默认规则"""
        default_rules = {
            "EVIDENCE_MIN_SCORE": PersonalRule(
                id="EVIDENCE_MIN_SCORE",
                description="Alpha Thesis 低于 70 分不交易",
                category="evidence",
                weight=1.0,
            ),
            "PRICING_CROWDED_SKIP": PersonalRule(
                id="PRICING_CROWDED_SKIP",
                description="Market Pricing 高于 85 分（过度拥挤）不追高",
                category="pricing",
                weight=1.0,
            ),
            "STRUCTURE_CONFIRMED": PersonalRule(
                id="STRUCTURE_CONFIRMED",
                description="K线结构未确认不进入交易准备",
                category="structure",
                weight=1.0,
            ),
            "RISK_VETO_OVERRIDE": PersonalRule(
                id="RISK_VETO_OVERRIDE",
                description="Risk Governor 否决直接放弃，不考虑其他评分",
                category="risk",
                weight=2.0,  # 更高权重
            ),
            "TIMING_PULLBACK": PersonalRule(
                id="TIMING_PULLBACK",
                description="已涨超过 20% 且无回踩，等待回踩确认",
                category="timing",
                weight=0.8,
            ),
        }

        for rule_id, rule in default_rules.items():
            if rule_id not in self.rules:
                self.rules[rule_id] = rule

    def record_decision(self, decision: PersonalDecision):
        """记录用户决策"""
        self.decisions.append(decision)
        self._update_rules(decision)
        self._save_decision(decision)

    def _update_rules(self, decision: PersonalDecision):
        """根据决策结果更新规则"""
        for rule_id in decision.rules_to_adjust:
            if rule_id in self.rules:
                rule = self.rules[rule_id]
                if decision.outcome == DecisionOutcome.PROFIT:
                    rule.success_count += 1
                elif decision.outcome == DecisionOutcome.LOSS:
                    rule.failure_count += 1

                rule.last_applied = decision.timestamp

                # 记录进化历史
                rule.evolution_history.append({
                    "timestamp": decision.timestamp.isoformat(),
                    "decision_id": decision.id,
                    "outcome": decision.outcome.value,
                    "notes": decision.user_notes,
                })

                # 检查是否需要禁用规则
                if rule.should_disable():
                    rule.enabled = False
                    rule.evolution_history.append({
                        "timestamp": decision.timestamp.isoformat(),
                        "event": "rule_disabled",
                        "reason": f"成功率过低 ({rule.get_success_rate():.1%})",
                    })

        self._save_rules()

    def _save_decision(self, decision: PersonalDecision):
        """保存决策记录"""
        decisions_file = self.data_dir / "decisions.jsonl"
        with open(decisions_file, "a", encoding="utf-8") as f:
            data = {
                "id": decision.id,
                "timestamp": decision.timestamp.isoformat(),
                "symbol": decision.symbol,
                "asset_class": decision.asset_class,
                "alpha_thesis_score": decision.alpha_thesis_score,
                "market_pricing_score": decision.market_pricing_score,
                "trade_readiness_score": decision.trade_readiness_score,
                "risk_governor_decision": decision.risk_governor_decision,
                "final_status": decision.final_status,
                "user_decision": decision.user_decision.value,
                "user_action": decision.user_action,
                "outcome": decision.outcome.value,
                "entry_price": decision.entry_price,
                "exit_price": decision.exit_price,
                "price_change_percent": decision.price_change_percent,
                "user_notes": decision.user_notes,
                "lessons_learned": decision.lessons_learned,
                "rules_to_adjust": decision.rules_to_adjust,
            }
            f.write(json.dumps(data, ensure_ascii=False) + "\n")

    def _save_rules(self):
        """保存规则"""
        rules_file = self.data_dir / "rules.json"
        rules_data = {}
        for rule_id, rule in self.rules.items():
            rules_data[rule_id] = {
                "id": rule.id,
                "description": rule.description,
                "category": rule.category,
                "enabled": rule.enabled,
                "weight": rule.weight,
                "success_count": rule.success_count,
                "failure_count": rule.failure_count,
                "last_applied": rule.last_applied.isoformat() if rule.last_applied else None,
                "evolution_history": rule.evolution_history,
            }

        with open(rules_file, "w", encoding="utf-8") as f:
            json.dump(rules_data, f, ensure_ascii=False, indent=2)

    def get_personal_insights(self) -> Dict:
        """获取个人专属洞察"""
        if not self.decisions:
            return {"message": "暂无决策记录"}

        # 统计
        total = len(self.decisions)
        profit = sum(1 for d in self.decisions if d.outcome == DecisionOutcome.PROFIT)
        loss = sum(1 for d in self.decisions if d.outcome == DecisionOutcome.LOSS)
        missed = sum(1 for d in self.decisions if d.outcome == DecisionOutcome.MISSED)
        avoided = sum(1 for d in self.decisions if d.outcome == DecisionOutcome.AVOIDED)

        # 成功率
        executed = profit + loss
        success_rate = profit / executed if executed > 0 else 0

        # 按标的统计
        symbol_stats = {}
        for d in self.decisions:
            if d.symbol not in symbol_stats:
                symbol_stats[d.symbol] = {"profit": 0, "loss": 0, "total": 0}
            symbol_stats[d.symbol]["total"] += 1
            if d.outcome == DecisionOutcome.PROFIT:
                symbol_stats[d.symbol]["profit"] += 1
            elif d.outcome == DecisionOutcome.LOSS:
                symbol_stats[d.symbol]["loss"] += 1

        # 最盈利/最亏损标的
        best_symbol = max(symbol_stats.items(),
                         key=lambda x: x[1]["profit"] - x[1]["loss"],
                         key=lambda x: (x[1]["profit"] / (x[1]["profit"] + x[1]["loss"]) if (x[1]["profit"] + x[1]["loss"]) > 0 else 0))

        # 规则状态
        active_rules = [r for r in self.rules.values() if r.enabled]
        disabled_rules = [r for r in self.rules.values() if not r.enabled]

        # 累计经验
        all_lessons = []
        for d in self.decisions:
            all_lessons.extend(d.lessons_learned)

        lesson_count = {}
        for lesson in all_lessons:
            lesson_count[lesson] = lesson_count.get(lesson, 0) + 1

        top_lessons = sorted(lesson_count.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "summary": {
                "total_decisions": total,
                "profit": profit,
                "loss": loss,
                "missed": missed,
                "avoided": avoided,
                "success_rate": success_rate,
            },
            "best_symbols": [
                {"symbol": s, "success_rate": p["profit"]/(p["profit"]+p["loss"]) if (p["profit"]+p["loss"])>0 else 0}
                for s, p in sorted(symbol_stats.items(),
                                   key=lambda x: x[1]["profit"]/(x[1]["profit"]+x[1]["loss"]) if (x[1]["profit"]+x[1]["loss"])>0 else 0,
                                   reverse=True)[:3]
            ],
            "rules": {
                "active": len(active_rules),
                "disabled": len(disabled_rules),
                "details": [
                    {
                        "id": r.id,
                        "description": r.description,
                        "success_rate": r.get_success_rate(),
                        "enabled": r.enabled,
                    }
                    for r in self.rules.values()
                ]
            },
            "top_lessons": [lesson for lesson, _ in top_lessons],
        }

    def get_adjusted_weights(self) -> Dict[str, float]:
        """获取调整后的规则权重（用于个性化评分）"""
        weights = {}
        for rule_id, rule in self.rules.items():
            if rule.enabled:
                # 基于成功率动态调整权重
                success_rate = rule.get_success_rate()
                if success_rate > 0.7:
                    weights[rule_id] = rule.weight * 1.2  # 提高权重
                elif success_rate < 0.5:
                    weights[rule_id] = rule.weight * 0.8  # 降低权重
                else:
                    weights[rule_id] = rule.weight
        return weights

    def evolve(self) -> Dict:
        """执行进化迭代，返回进化建议"""
        insights = self.get_personal_insights()

        suggestions = []

        # 基于成功率建议
        if insights["summary"]["success_rate"] < 0.5:
            suggestions.append({
                "type": "warning",
                "message": "当前成功率低于 50%，建议更严格地遵循风控规则"
            })

        # 基于规则状态建议
        for rule in insights["rules"]["details"]:
            if not rule["enabled"]:
                suggestions.append({
                    "type": "info",
                    "message": f"规则 '{rule['description']}' 已因成功率过低被禁用"
                })

        # 基于经验建议
        if insights["top_lessons"]:
            suggestions.append({
                "type": "lesson",
                "message": f"最重要的经验: {insights['top_lessons'][0]}"
            })

        return {
            "insights": insights,
            "suggestions": suggestions,
            "adjusted_weights": self.get_adjusted_weights(),
        }


# 全局实例（使用时需要指定 user_id）
_engines: Dict[str, PersonalEvolutionEngine] = {}


def get_engine(user_id: str = "default") -> PersonalEvolutionEngine:
    """获取用户的进化引擎"""
    if user_id not in _engines:
        _engines[user_id] = PersonalEvolutionEngine(user_id)
    return _engines[user_id]


def main():
    """示例用法"""
    engine = get_engine("demo_user")

    # 示例：记录一次决策
    from datetime import datetime

    decision = PersonalDecision(
        id="DEC-001",
        timestamp=datetime.now(),
        symbol="NVDA",
        asset_class="US_STOCK",
        alpha_thesis_score=75,
        market_pricing_score=70,
        trade_readiness_score=80,
        risk_governor_decision="Pass",
        final_status="Trade Ready",
        user_decision=DecisionType.TRADE,
        user_action="买入 10% 仓位",
        outcome=DecisionOutcome.PROFIT,
        entry_price=800.0,
        exit_price=850.0,
        price_change_percent=6.25,
        user_notes="AI 需求逻辑验证正确",
        lessons_learned=["科技股在 Risk On 环境下表现更好"],
        rules_to_adjust=["EVIDENCE_MIN_SCORE", "STRUCTURE_CONFIRMED"],
    )

    engine.record_decision(decision)

    # 获取进化洞察
    evolution = engine.evolve()

    print("=== BSHL Alpha Skill 个人进化报告 ===\n")
    print(f"总决策数: {evolution['insights']['summary']['total_decisions']}")
    print(f"成功率: {evolution['insights']['summary']['success_rate']:.1%}")
    print(f"活跃规则: {evolution['insights']['rules']['active']}")

    print("\n进化建议:")
    for suggestion in evolution["suggestions"]:
        print(f"  [{suggestion['type'].upper()}] {suggestion['message']}")


if __name__ == "__main__":
    main()
