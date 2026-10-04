# Trade Readiness — 交易准备检查

目标是解释一个有日期的研究计划为何满足或不满足准备条件。首先区分技术分层状态、风控决策与最终研究状态；高研究分不能补偿未知风险或缺止损。

## 操作顺序

1. 确认 symbol、market、exchange、currency、日线时间与来源；使用有可用时点和提供方日历的 CSV。
2. 按[证据阶梯](../references/evidence_ladder.md)记录人工研究分、来源、发布时间、可用时间、过期时间与反证。不能编造财务、社媒、期权或资金流数据。
3. 运行[确定性结构](../references/technical_structure_rules.md)。未收盘、历史不足、未完成母周期或尚未确认的 pivot 不能确认准备。
4. 明确用户选择的止损、目标；建议结构止损不会自动变成计划止损。
5. 按[风控总闸](risk_governor_check.md)补齐十项，输出原始卡片并保留 analysis_id。

## Trade Ready 的共同必要条件

非模拟；US/USD、1d、unadjusted 股票/ETF，声明受支持交易所；最后可见收盘不超过四个日历日；来源有效；有可见且未过期的强支持证据；Alpha 不是 D 且 evidence_quality >= 10；Pricing 不是 D；有效突破或回踩结构、母周期与历史确认；风控 Pass；用户止损和目标有效；RR >= 2；Trade 分 >= 85；没有 blocker。

这是共同门控条件，不是获利概率。任何一个缺口都阻断升级。最终状态为 Research Only、Watchlist、Trade Ready、Wait Pullback、Avoid 或 Veto。Wait Pullback 是兼容旧命名的等待状态，也可能因财报等待。

mock 的 final_status 必须为 Research Only；simulation_status 可展示规则的模拟结果。其他市场不建立当前版本真实 Trade Ready。

## 可复现示例

运行 `python scripts/run_demo.py`，查看[突破](../examples/current/breakout/card.md)、[缺止损](../examples/current/no-stop/card.md)、[过热](../examples/current/overheated/card.md)。全部为虚构样本；不能用真实公司名和未经核验的旧价格包装为当前行情。

保存原计划后再复核新证据。新批准必须使用当前规则与尚有效的证据；过期计划要重新生成，不能只改 final_status 或复制旧分数。

[完整合同](../docs/DATA_CONTRACT.md) · [历史人工模板](../docs/archive/trade_readiness_check-v0.5.md)
