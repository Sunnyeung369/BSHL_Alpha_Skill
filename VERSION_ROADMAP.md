# BSHL Alpha Skill 版本路线图

---

## 当前版本: v0.5 回放系统

**发布日期**: 2026-06-06
**状态**: ✅ 已完成

### v0.5 交付物

- [x] **回放系统** (`replay/`)
  - [x] `replay_engine.py` — 回放引擎
  - [x] `case_library.py` — 案例库管理
  - [x] 规则验证脚本
  - [x] 性能报告生成
  - [x] 10 种经典案例类型

- [x] **数据接口** (`data/`)
  - [x] `market_data.py` — 行情数据
  - [x] `fundamental_data.py` — 财报数据
  - [x] `news_data.py` — 新闻数据

- [x] **评分脚本** (`scoring/`)
  - [x] `alpha_thesis_score.py` — Alpha 评分
  - [x] `market_pricing_score.py` — 市场定价评分
  - [x] `trade_readiness_score.py` — 交易准备评分
  - [x] `risk_governor_score.py` — 风控评分
  - [x] `position_risk_score.py` — 仓位风险评分
  - [x] `scorer.py` — 评分协调器

- [x] **结构化数据** (`schemas/`)
  - [x] `alpha_thesis.schema.json`
  - [x] `evidence_ledger.schema.json`
  - [x] `market_regime.schema.json`
  - [x] `trade_readiness.schema.json`
  - [x] `risk_governor.schema.json`
  - [x] `review_log.schema.json`

- [x] **日志系统** (`logs/`)
  - [x] 日志保存结构
  - [x] 查询功能

### v0.5 核心能力

1. **单标的深度分析** — 六层完整分析
2. **主题到标的映射** — 产业链拆解
3. **交易准备检查** — 能否追判断
4. **结构化输出** — JSON 格式支持
5. **自动评分** — 三层评分系统
6. **数据获取** — 半自动数据接口
7. **回放验证** — 规则有效性验证

---

## 历史版本

### v0.1 MVP (2026-06-06)

纯文本 Skill，基础架构：
- SKILL.md 入口
- constitution/ 核心原则
- workflows/ 标准工作流
- references/ 参考规则
- prompts/ 提示词模板
- examples/ 示例案例

### v0.2 结构化 JSON (2026-06-06)

- 完整 JSON Schema 定义
- 结构化输出支持
- 日志保存系统

### v0.3 评分脚本 (2026-06-06)

- 三层评分系统实现
- 自动评分计算
- 评分可追溯

### v0.4 数据接口 (2026-06-06)

- 行情数据自动获取
- 财报数据自动获取
- 新闻数据自动获取

### v0.5 回放系统 (2026-06-06)

- 回放案例库
- 规则验证引擎
- 性能报告生成
- 10 种经典案例类型

---

## 后续版本

后续版本维护与更新请联系作者。

---

## 版本时间线

```
2026-06-06  v0.1  ✅ 纯文本 Skill MVP
2026-06-06  v0.2  ✅ 结构化 JSON
2026-06-06  v0.3  ✅ 评分脚本
2026-06-06  v0.4  ✅ 数据接口
2026-06-06  v0.5  ✅ 回放系统
```

---

## 联系与贡献

欢迎贡献与反馈。

- GitHub: https://github.com/Sunnyeung369/BSHL_Alpha_Skill
- 提交 Issue 或 Pull Request

---

*最后更新: 2026-06-06*
*当前版本: v0.5*
