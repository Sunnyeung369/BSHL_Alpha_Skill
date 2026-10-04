# Liquidity and Crowding — 流动性与拥挤

## 已实现的门控

US/USD 日线最近可见 volume × close < 1000 万美元时，liquidity 检查失败并 Veto。达到金额不代表订单能成交，也不会自动补齐未知人工检查。日线金额不是买卖盘深度。

social_crowding 失败产生 Reduce Size，correlation 和 position_exposure 失败亦然；未知检查产生 Wait Confirmation。已知更高优先级风险仍优先。Veto 不能改成“极小仓位试试”。[风控工作流](../workflows/risk_governor_check.md)列出完整优先级。

## 需要人工核验的内容

点差、盘口、可成交量、持有人集中度、社媒统计、期权情绪和资产相关性没有实时接口。来源和日期不明确时保持未知；不能发明讨论量或相关系数。港股、A股、Crypto 的金额门槛与交易约束需要独立验证，不套用本版本 USD 规则。

## 仓位计算

账户输入包括已有单标的、所属板块和总敞口，必须形成包含关系。默认单标的上限 5%、板块 25%、总敞口 80%；止损预算默认 1%。实际新增金额取所有约束的最小值，扣除已有仓位；可给 liquidity_capital_limit。未知止损、杠杆或相关性/流动性限制不通过时不新增。

这些限制用于解释研究计划。跳空、成本和流动性损失不受预算保证；没有券商执行或自动减仓。

[仓位与账户输入](../docs/WORKSPACE.md) · [历史模板](../docs/archive/liquidity_and_crowding_rules-v0.5.md)
