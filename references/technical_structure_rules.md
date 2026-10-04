# Technical Structure — 当前确定性结构规则

本页解释 `analyze_structure` 的当前日线规则。它描述一个实验规则集，不代表所有技术分析方法。

| 计算 | 当前定义 |
|---|---|
| 均线 | 已收盘可见日线 MA20、MA50；稳定求和 |
| 波动 | Wilder ATR14：首十四个 true range 均值，再以 1/14 平滑 |
| Pivot | 左右各两根的严格高/低极值；同高同低不确认，右侧数据必须已经可用 |
| 母周期 | 提供方声明日历中的已完成周；所有声明交易日都有收盘记录，且日历覆盖或时间已跨周界 |
| 母周期方向 | 最近两根完成周 close 比较得到 UP / DOWN / CONSOLIDATION；少于两周为 UNKNOWN |
| 历史要求 | 至少五十根已收盘日线 |
| 突破 | 当前 close > 已确认阻力 × 1.001，前一 close <= 阻力，量比 >= 1.3；母周期 UP、历史与收盘确认 |
| 回踩 | 最近五根中有已确认阻力的突破；当前 low 距阻力 <= 0.5 ATR，close >= 阻力且收阳，量比 >= 1.0；共同确认条件仍需满足 |
| 量比 | 最近已收盘量 / 此前二十根已收盘平均量；均量为零或历史不足时为未知 |
| 过热 | 当前价 > MA20 + 3 ATR |
| 破位 | 已收盘价格低于最近确认 pivot low |
| 建议止损 | pivot low - 0.25 ATR；不为正或不低于当前价时不建议 |

这些默认参数均为实验参数。RSI、月线、相对强弱和盘中订单簿没有在此计算；不能把人工提问当作程序已经返回的指标。当前 UP 并不表示已实现一套高点低点趋势线判定。

状态按代码优先级输出 Breakdown、Exhaustion、No Trade、Pullback Entry Zone、Confirmed Breakout、Breakout Watch 或 Base Building。有结构不等于最终准备；需要[共同门控](../workflows/trade_readiness_check.md)。当前选定止损距离 > 10% 否决，RR < 2 阻断；并无“一般盈亏比也可交易”的替代门槛。

最新记录的 close timestamp、volume 和 price 随卡保留，以支持导入时复核。导入验证不会重新认证原始行情或重建全部 K 线；要重算结构必须保留 CSV 和元数据。

[数据合同](../docs/DATA_CONTRACT.md) · [结构实现](../bshl/structure.py) · [历史模板](../docs/archive/technical_structure_rules-v0.5.md)
