# Risk Governor — 风控总闸

本页对应当前可执行规则。人工新闻分析不能代替风险检查；本仓库没有下单功能。

## 输入与三值检查

给出资产、决策时点和十个检查项。`true` 表示检查通过，`false` 表示失败，`null` 或缺失表示未知。监管、财报等尚未实现的数据调查需要人工提供来源；不能为凑齐检查而填 true。

| 检查字段 | 失败后的风控决策 |
|---|---|
| liquidity / volatility / stop_loss_distance / regulatory_uncertainty | Veto |
| evidence_quality | Watch Only |
| earnings_risk / price_location | Wait |
| social_crowding / position_exposure / correlation | Reduce Size |
| 任一未完成检查 | Wait Confirmation；已知更高优先级失败仍优先 |
| 十项全部通过 | Pass；仍需研究、结构和计划门控 |

多项同时触发时：Veto > Watch Only > Wait > Wait Confirmation > Reduce Size > Pass。有效且已可见的 thesis kill switch 也产生 Veto。不能把所有失败都叫一票否决，不能通过缩小仓位绕过 Veto。

## 代码测量会收紧人工结果

当前 US/USD 日线配置：日成交额 < 1000 万美元、ATR14 / 当前价 > 5%、用户止损距离 > 10% 分别使流动性、波动、止损检查失败；价格 > MA20 + 3 ATR 使价格位置失败。无有效强支持证据使证据检查失败。这些是实验门槛，不是收益保证。

仓位计算另有默认上限：单标的 5%、板块 25%、总敞口 80%，账户止损预算默认 1%。输入需满足单标的包含在板块中、板块包含在总敞口中。缺止损、杠杆或相关性/流动性限制不通过时不建议新增。

## 输出与复核

使用 `bshl analyze` 输出原检查、测量覆盖、未知项、触发原因及最终研究状态。Risk Governor 决策与 final_status 是不同字段；mock 的最终状态始终 Research Only。

保存原卡片，再以新时点重新分析。等待、否决和未交易都是有效记录。候选规则不能修改硬门控；人工批准计划也不会下单。

详见[数据合同](../docs/DATA_CONTRACT.md)、[工作区](../docs/WORKSPACE.md)与[实现](../scoring/risk_governor_score.py)。[旧人工模板](../docs/archive/risk_governor_check-v0.5.md)仅供历史回查。
