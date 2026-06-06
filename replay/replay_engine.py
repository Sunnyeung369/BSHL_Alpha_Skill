"""
BSHL Alpha Skill - Replay Engine

回放引擎，用于历史回测和规则验证。
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from datetime import datetime, date, timedelta
import json

from .case_library import ReplayCase, CaseType, CaseOutcome, ReplayCaseLibrary


@dataclass
class ReplayConfig:
    """回放配置"""
    start_date: date
    end_date: date
    symbols: List[str]
    initial_capital: float
    commission_rate: float = 0.001


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
            if symbol in prices:
                value += prices[symbol] * shares
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
        """执行回放"""
        # 获取时间范围内的所有案例
        cases = self._get_cases_in_range()

        # 按时间排序
        cases.sort(key=lambda c: c.original_date)

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
        # 记录日志
        log_entry = {
            "case_id": case.id,
            "symbol": case.symbol,
            "date": case.original_date.isoformat(),
            "original_price": case.original_price,
            "original_status": case.original_status,
            "action": "NONE",
            "outcome_price": case.outcome_price,
            "outcome": case.outcome.value,
            "price_change": case.price_change_percent,
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
        final_prices = {case.symbol: case.outcome_price for case in cases}
        final_value = self.portfolio.get_value(final_prices)

        # 计算收益
        total_return = (final_value - self.config.initial_capital) / self.config.initial_capital

        # 统计交易
        total_trades = len(self.portfolio.trades)
        buy_trades = sum(1 for t in self.portfolio.trades if t.action == "buy")
        sell_trades = sum(1 for t in self.portfolio.trades if t.action == "sell")

        # 统计成功率
        executed_trades = [log for log in self.replay_log if log["action"] in ["BOUGHT", "SOLD"]]
        successful_trades = sum(1 for log in executed_trades if log.get("price_change", 0) > 0)
        success_rate = successful_trades / len(executed_trades) if executed_trades else 0

        return {
            "config": {
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "symbols": self.config.symbols,
                "initial_capital": self.config.initial_capital,
            },
            "performance": {
                "final_value": final_value,
                "total_return": total_return,
                "total_return_pct": total_return * 100,
            },
            "trades": {
                "total": total_trades,
                "buy": buy_trades,
                "sell": sell_trades,
                "success_rate": success_rate * 100,
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

    def test_rule(self, rule: Callable[[ReplayCase], bool]) -> Dict:
        """测试规则

        Args:
            rule: 规则函数，输入案例，返回 True/False

        Returns:
            测试结果
        """
        cases = self.case_library.get_all_cases()

        # 应用规则
        passed = []
        failed = []
        for case in cases:
            if rule(case):
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
    print(f"最终价值: ${report['performance']['final_value']:,.2f}")
    print(f"总收益率: {report['performance']['total_return_pct']:+.2f}%")

    print(f"\n交易统计:")
    print(f"  总交易: {report['trades']['total']}")
    print(f"  买入: {report['trades']['buy']}")
    print(f"  卖出: {report['trades']['sell']}")
    print(f"  成功率: {report['trades']['success_rate']:.1f}%")

    print(f"\n案例统计:")
    print(f"  总案例: {report['cases']['total']}")
    print(f"  执行: {report['cases']['executed']}")
    print(f"  跳过: {report['cases']['skipped']}")


if __name__ == "__main__":
    main()
