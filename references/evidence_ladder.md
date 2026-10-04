# Evidence Ladder — 来源、时点与反证

强证据是研究支撑的必要输入，不能单独授予交易准备。来源标签、URL、数量和评分都不能替代真实性核查。

## 应保存的记录

每条证据保存唯一 id、claim、source_url、published_at、available_at、source_type、evidence_strength、supports_or_refutes。可另给 expires_at 和 kill_switch。时间必须带偏移，available_at 不得早于 published_at。

可用强支持需同时满足：来源为 HTTP(S) 且无嵌入凭据；claim 非空；发布时间和可用时间都不晚于决策时点；尚未到期；evidence_strength 为 strong；source_type 是 filing、transcript、company_release 或 industry_report；supports_or_refutes 为 supports。

监管等资料可作研究依据，但只有上述四个 source_type 会进入本版本的强支持计数。不要随意改标签以求通过。重复报道也不等于独立证据；代码计数不是独立性或因果强度估计。

## 三个常见边界

- 官方文件也可能引用错误、被误读或过期；打开原文核对具体 claim、单位与日期。
- 媒体、社媒、传闻可以提供线索或反证，不能填补缺失的强支持。没有“强 + 强 = 已校准高概率”的公式。
- 失效时间由研究者显式给出。代码不自动认定 AI 六个月、传统行业十二个月均有效；未给 expires_at 的记录需要人工复核。

已可见且有效来源/claim 的 kill_switch 会否决 thesis。未来或到期记录留在审计中，但不能支持或否决当前判断。反证尚未触发 kill_switch 时，需反映在人工作出的研究分、风险检查和说明中；代码没有自动理解新闻矛盾的模型。

所有来源仍标记 user_supplied_not_independently_verified。批准计划时重新检查证据有效性；原始快照不改写。

[输入合同](../docs/DATA_CONTRACT.md) · [原理](../constitution/core_principles.md) · [历史模板](../docs/archive/evidence_ladder-v0.5.md)
