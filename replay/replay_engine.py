"""
BSHL Alpha Skill - Replay Engine

Legacy case-snapshot simulation, not a bar-based backtest or execution model.
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import json
import math

from .case_library import ReplayCase, DecisionSnapshot, CaseOutcome, ReplayCaseLibrary, replay_case_library


@dataclass
class ReplayConfig:
    """回放配置"""
    start_date: date
    end_date: date
    symbols: List[str]
    initial_capital: float
    commission_rate: float = 0.001

    def __post_init__(self):
        if self.start_date > self.end_date:
            raise ValueError("start_date must not exceed end_date")
        if (isinstance(self.initial_capital, bool) or not math.isfinite(self.initial_capital)
                or self.initial_capital <= 0):
            raise ValueError("initial_capital must be finite and positive")
        if not math.isfinite(self.commission_rate) or not 0 <= self.commission_rate < 1:
            raise ValueError("commission_rate must be in [0, 1)")


@dataclass
class Trade:
    """交易记录"""
    symbol: str
    action: str  # buy, sell
    price: float
    shares: int
    timestamp: datetime
    reason: str


@dataclass
class Portfolio:
    """投资组合"""
    cash: float
    positions: Dict[str, int]  # symbol -> shares
    trades: List[Trade]

    def get_value(self, prices: Dict[str, float]) -> float:
        """计算组合价值"""
        value = self.cash
        for symbol, shares in self.positions.items():
            if not shares:
                continue
            if symbol not in prices:
                raise ValueError(f"missing valuation price: {symbol}")
            price = prices[symbol]
            if not math.isfinite(price) or price <= 0:
                raise ValueError(f"invalid valuation price: {symbol}")
            value += price * shares
        return value


class ReplayEngine:
    """回放引擎"""

    def __init__(self, config: ReplayConfig, case_library: ReplayCaseLibrary):
        self.config = config
        self.case_library = case_library
        self.portfolio = Portfolio(
            cash=config.initial_capital,
            positions={},
            trades=[],
        )
        self.replay_log: List[Dict] = []

    def replay(self) -> Dict:
        """Rebuild an illustrative case simulation on every call."""
        self.portfolio = Portfolio(self.config.initial_capital, {}, [])
        self.replay_log = []
        # 获取时间范围内的所有案例
        cases = self._get_cases_in_range()

        # 按时间排序
        cases.sort(key=lambda c: (c.original_date, c.id))

        # 逐个回放
        for case in cases:
            self._replay_case(case)

        # 生成报告
        return self._generate_report(cases)

    def _get_cases_in_range(self) -> List[ReplayCase]:
        """获取时间范围内的案例"""
        cases = []
        for case in self.case_library.get_all_cases():
            if self.config.start_date <= case.original_date <= self.config.end_date:
                if case.symbol in self.config.symbols or "*" in self.config.symbols:
                    cases.append(case)
        return cases

    def _replay_case(self, case: ReplayCase):
        """回放单个案例"""
        if not math.isfinite(case.original_price) or case.original_price <= 0:
            raise ValueError(f"invalid original price: {case.id}")
        if case.outcome_date < case.original_date:
            raise ValueError(f"outcome precedes decision: {case.id}")
        observed = case.outcome_date <= self.config.end_date
        # 记录日志
        log_entry = {
            "case_id": case.id,
            "symbol": case.symbol,
            "date": case.original_date.isoformat(),
            "original_price": case.original_price,
            "original_status": case.original_status,
            "action": "NONE",
            "outcome_price": case.outcome_price if observed else None,
            "outcome": case.outcome.value if observed else None,
            "price_change": case.price_change_percent if observed else None,
            "outcome_available": observed,
        }

        # 根据原始状态决定动作
        if case.original_status == "Trade Ready":
            # 检查风控
            if case.risk_governor_decision == "Pass":
                # 模拟买入
                self._execute_trade(case, "buy", log_entry)
            elif case.risk_governor_decision == "Veto":
                log_entry["action"] = "SKIPPED (VETO)"
            elif case.risk_governor_decision == "Watch Only":
                log_entry["action"] = "SKIPPED (WATCH)"

        self.replay_log.append(log_entry)

    def _execute_trade(self, case: ReplayCase, action: str, log_entry: Dict):
        """执行交易"""
        if action == "buy":
            # 计算买入数量
            shares = int(self.portfolio.cash / case.original_price * 0.1)  # 10% 仓位
            if shares > 0:
                cost = shares * case.original_price
                commission = cost * self.config.commission_rate
                total_cost = cost + commission

                if total_cost <= self.portfolio.cash:
                    self.portfolio.cash -= total_cost
                    self.portfolio.positions[case.symbol] = self.portfolio.positions.get(case.symbol, 0) + shares

                    trade = Trade(
                        symbol=case.symbol,
                        action="buy",
                        price=case.original_price,
                        shares=shares,
                        timestamp=datetime.combine(case.original_date, datetime.min.time()),
                        reason=f"Case {case.id}",
                    )
                    self.portfolio.trades.append(trade)
                    log_entry["action"] = "BOUGHT"

        elif action == "sell":
            # 卖出所有持仓
            if case.symbol in self.portfolio.positions and self.portfolio.positions[case.symbol] > 0:
                shares = self.portfolio.positions[case.symbol]
                proceeds = shares * case.original_price
                commission = proceeds * self.config.commission_rate
                total_proceeds = proceeds - commission

                self.portfolio.cash += total_proceeds
                self.portfolio.positions[case.symbol] = 0

                trade = Trade(
                    symbol=case.symbol,
                    action="sell",
                    price=case.original_price,
                    shares=shares,
                    timestamp=datetime.combine(case.original_date, datetime.min.time()),
                    reason=f"Case {case.id}",
                )
                self.portfolio.trades.append(trade)
                log_entry["action"] = "SOLD"

    def _generate_report(self, cases: List[ReplayCase]) -> Dict:
        """生成回放报告"""
        # 计算最终组合价值
        observed = sorted((case for case in cases if case.outcome_date <= self.config.end_date),
                          key=lambda c: (c.outcome_date, c.id))
        final_prices = {case.symbol: case.outcome_price for case in observed}
        missing_prices = sorted(symbol for symbol, shares in self.portfolio.positions.items()
                                if shares and symbol not in final_prices)
        final_value = None if missing_prices else self.portfolio.get_value(final_prices)

        # 计算收益
        total_return = ((final_value - self.config.initial_capital) / self.config.initial_capital
                        if final_value is not None else None)

        # 统计交易
        total_trades = len(self.portfolio.trades)
        buy_trades = sum(1 for t in self.portfolio.trades if t.action == "buy")
        sell_trades = sum(1 for t in self.portfolio.trades if t.action == "sell")

        # 统计成功率
        executed_trades = [log for log in self.replay_log if log["action"] in ["BOUGHT", "SOLD"]]
        resolved_trades = [log for log in executed_trades if log["outcome_available"]]
        successful_trades = sum(1 for log in resolved_trades if log["price_change"] > 0)
        success_rate = successful_trades / len(resolved_trades) if resolved_trades else None

        return {
            "mode": "legacy_case_snapshot_simulation",
            "performance_validated": False,
            "limitations": ["No bar sequence, exit rules or slippage model",
                            "Valuation uses last observed case outcome, not an end-date market quote"],
            "config": {
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "symbols": self.config.symbols,
                "initial_capital": self.config.initial_capital,
            },
            "performance": {
                "final_value": final_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100 if total_return is not None else None,
                "valuation_status": "unknown" if missing_prices else "illustrative",
                "missing_prices": missing_prices,
                "valuation_dates": {case.symbol: case.outcome_date.isoformat() for case in observed},
            },
            "trades": {
                "total": total_trades,
                "buy": buy_trades,
                "sell": sell_trades,
                "success_rate": success_rate * 100 if success_rate is not None else None,
                "resolved_cases": len(resolved_trades),
            },
            "cases": {
                "total": len(cases),
                "executed": len(executed_trades),
                "skipped": len(self.replay_log) - len(executed_trades),
            },
            "log": self.replay_log,
        }


class RuleTester:
    """规则测试器"""

    def __init__(self, case_library: ReplayCaseLibrary):
        self.case_library = case_library

    def test_rule(self, rule: Callable[[DecisionSnapshot], bool],
                  rule_id: Optional[str] = None, min_cases: int = 30) -> Dict:
        """测试规则

        Args:
            rule: 规则函数，输入案例，返回 True/False

        Returns:
            测试结果
        """
        if min_cases < 1:
            raise ValueError("min_cases must be positive")
        cases = [case for case in self.case_library.get_all_cases()
                 if rule_id is None or rule_id in case.rule_ids]

        # 应用规则
        passed = []
        failed = []
        for case in cases:
            decision = rule(case.decision_snapshot())
            if not isinstance(decision, bool):
                raise ValueError("rule must return a boolean")
            if decision:
                passed.append(case)
            else:
                failed.append(case)

        # 计算规则对成功案例的覆盖率
        success_cases = [c for c in cases if c.outcome == CaseOutcome.SUCCESS]
        covered_success = sum(1 for c in success_cases if c in passed)
        coverage = covered_success / len(success_cases) if success_cases else 0

        # 计算规则对失败案例的过滤率
        failure_cases = [c for c in cases if c.outcome == CaseOutcome.FAILURE]
        filtered_failure = sum(1 for c in failure_cases if c not in passed)
        filter_rate = filtered_failure / len(failure_cases) if failure_cases else 0

        return {
            "mode": "case_rule_diagnostics",
            "status": "insufficient" if len(cases) < min_cases else "diagnostic_only",
            "performance_validated": False,
            "rule_applied": len(passed) + len(failed),
            "passed": len(passed),
            "failed": len(failed),
            "success_coverage": coverage * 100,
            "failure_filter_rate": filter_rate * 100,
            "passed_cases": [c.id for c in passed],
            "failed_cases": [c.id for c in failed],
        }


def main():
    """示例用法"""
    from datetime import date

    # 创建回放配置
    config = ReplayConfig(
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
        symbols=["*"],  # * 表示所有标的
        initial_capital=100000,
    )

    # 创建回放引擎
    engine = ReplayEngine(config, replay_case_library)

    # 执行回放
    report = engine.replay()

    # 打印报告
    print("=== BSHL Alpha Skill 回放报告 ===\n")
    print(f"回放期间: {report['config']['start_date']} 至 {report['config']['end_date']}")
    print(f"初始资金: ${report['config']['initial_capital']:,.2f}")
    print(f"案例估值: {report['performance']['final_value']}")
    print(f"示意收益率: {report['performance']['total_return_pct']}")

    print(f"\n交易统计:")
    print(f"  总交易: {report['trades']['total']}")
    print(f"  买入: {report['trades']['buy']}")
    print(f"  卖出: {report['trades']['sell']}")
    print(f"  案例成功率: {report['trades']['success_rate']}")

    print(f"\n案例统计:")
    print(f"  总案例: {report['cases']['total']}")
    print(f"  执行: {report['cases']['executed']}")
    print(f"  跳过: {report['cases']['skipped']}")


if __name__ == "__main__":
    main()
