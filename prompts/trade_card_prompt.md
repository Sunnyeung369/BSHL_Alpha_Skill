# Research Plan Card — 研究计划提示词

依据已有研究卡解释计划，不能凭提示词自行授予 Trade Ready。使用[交易准备工作流](../workflows/trade_readiness_check.md)的共同门控：Risk Governor 必须 Pass；Reduce Size 需要重新评估，不能作为通过。

## 给 Agent 的请求

> 使用给定 CSV、元数据、人工证据与研究 context，通过当前 bshl analyze 生成有日期的研究卡。保持来源与 mock 标签；缺失项留空并列出 blocker。解释最终状态、必要条件、用户选定止损/目标、盈亏比、反证与失效条件。不要从建议结构止损自动填入用户计划，不发明实时数据或买卖指令。
>
> 如需要仓位，以显式同币种账户 context 调用 bshl size，说明已有单标的、板块和总敞口及受约束的新增量。名义止损预算不保证最大损失；跳空、费用和流动性可能扩大损失。非 Trade Ready 卡可以正常生成，但新增量为零。
>
> 如需保存用户选择，调用 journal 保存原快照，再记录 research、wait、approve_plan 或 reject_plan。原卡片和决定分开；批准不会下单。资料已过期或价格/证据变化时重新分析生成新 ID，不修改旧价格或状态。

## 输出字段

symbol、exchange、currency、as_of、analysis_id、rule_version、data_mode、is_mock、来源及核验限制；技术结构与各评分；风险原检查/未知项/触发原因；final_status 与模拟状态；用户选择的止损与目标、RR；blockers、复核条件、证据失效时间。

所有字段从原始卡和计算结果引用。人类补充的催化剂、分批设想或执行说明明确标成人工研究，不当作模拟器已支持的订单类型或券商动作。当前可计算准备配置为 US/USD 日线股票/ETF，其他市场保持研究边界。

[卡片合同](../docs/DATA_CONTRACT.md) · [保存与仓位](../docs/WORKSPACE.md) · [历史模板](../docs/archive/trade_card_prompt-v0.5.md)
