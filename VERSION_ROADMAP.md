# BSHL Alpha Skill 版本路线图

---

## 当前版本: v0.1 MVP

**发布日期**: 2026-06-06
**状态**: ✅ 已完成

### v0.1 交付物

- [x] SKILL.md - 技能入口
- [x] README.md - 完整架构说明
- [x] constitution/ - 核心原则与契约
  - [x] core_principles.md
  - [x] scope_and_safety.md
  - [x] no_autonomous_trading.md
  - [x] terminology.md
- [x] workflows/ - 标准工作流
  - [x] daily_market_radar.md
  - [x] theme_to_asset_mapping.md
  - [x] single_asset_deep_dive.md
  - [x] earnings_event_check.md
  - [x] crypto_token_deep_dive.md
  - [x] trade_readiness_check.md
  - [x] risk_governor_check.md
  - [x] post_trade_review.md
- [x] references/ - 参考规则
  - [x] evidence_ladder.md
  - [x] market_regime_gate.md
  - [x] technical_structure_rules.md
- [x] schemas/ - 结构化数据定义
  - [x] alpha_thesis.schema.json
  - [x] market_regime.schema.json
  - [x] trade_readiness.schema.json
  - [x] risk_governor.schema.json
- [x] prompts/ - 核心提示词模板
  - [x] deep_dive_prompt.md
  - [x] contradiction_prompt.md
- [x] examples/ - 示例案例
  - [x] stock_deep_dive_example.md
  - [x] crypto_token_example.md
  - [x] failed_trade_review_example.md

### v0.1 核心能力

1. **单标的深度分析** - 六层完整分析
2. **主题到标的映射** - 产业链拆解
3. **交易准备检查** - 能否追判断

### v0.1 限制

- 纯文本输出，无结构化数据
- 无自动评分脚本
- 无数据接口
- 无回放系统

---

## 下一版本: v0.2 结构化 JSON

**预计时间**: 2026 Q3
**状态**: 🔄 规划中

### v0.2 目标

让输出可保存、可比较、可回放。

### v0.2 交付物

- [ ] 完整所有 Schema 定义
  - [ ] evidence_ledger.schema.json
  - [ ] review_log.schema.json
- [ ] 输出格式支持 JSON
- [ ] 日志保存系统
- [ ] 简单的查询功能

---

## v0.3 评分脚本

**预计时间**: 2026 Q4
**状态**: ⏳ 待规划

### v0.3 目标

让评分规则可计算。

### v0.3 交付物

- [ ] alpha_thesis_score.py
- [ ] market_pricing_score.py
- [ ] trade_readiness_score.py
- [ ] risk_governor_score.py

---

## v0.4 数据接口

**预计时间**: 2027 Q1
**状态**: ⏳ 待规划

### v0.4 目标

从手工输入变成半自动分析。

### v0.4 交付物

- [ ] 行情数据接口
- [ ] 财报数据接口
- [ ] 新闻数据接口

---

## v0.5 回放系统

**预计时间**: 2027 Q2
**状态**: ⏳ 待规划

### v0.5 目标

验证规则有没有用。

### v0.5 交付物

- [ ] 回放案例库
- [ ] 规则验证脚本
- [ ] 性能报告

---

## v1.0 BSHL AI Trading OS 集成

**预计时间**: 2027 H2
**状态**: ⏳ 待规划

### v1.0 目标

成为 BSHL 的投研大脑。

### v1.0 交付物

- [ ] 完整系统集成
- [ ] 实时数据流
- [ ] 自动化工作流
- [ ] 复盘自动化

---

*最后更新: 2026-06-06*
