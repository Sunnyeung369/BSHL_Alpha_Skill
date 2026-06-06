# BSHL Alpha Skill v0.5 发布说明

---

## 版本信息

- **版本号**: v0.5
- **发布日期**: 2026-06-06
- **状态**: ✅ 已完成
- **许可证**: MIT

---

## 本版本更新

### 新增功能：回放系统

| 模块 | 功能 |
|------|------|
| replay_engine.py | 回放引擎、历史回测、规则测试 |
| case_library.py | 案例库管理、规则验证、性能报告 |

### 支持的案例类型

1. 好逻辑但价格已透支
2. 好公司但市场 Risk Off
3. 小票社媒拉盘后暴跌
4. 财报超预期但高开低走
5. 主题强但影子股不涨
6. 龙头强势，跟风股失效
7. 链上信号强但价格破位
8. ETF 强于个股
9. 证据强但收入兑现慢
10. 高拥挤交易被反杀

### 规则验证

```python
from replay import RuleTester

# 测试规则有效性
result = tester.test_rule(my_rule)
print(f"成功率覆盖: {result['success_coverage']:.1f}%")
print(f"失败过滤率: {result['failure_filter_rate']:.1f}%")
```

---

## 完整功能清单

### 六层投研架构
```
Universe Radar → Alpha Thesis → Evidence Ledger → Market Regime → BSHL K线结构 → Risk Governor
```

### 四条铁律
- 证据弱，闭嘴
- 结构差，别动
- 风控否决，直接滚蛋
- 不复盘，永远韭菜

### 三层评分系统
- Alpha Thesis Score — 逻辑是否成立
- Market Pricing Score — 市场是否已定价
- Trade Readiness Score — 现在能否进入交易准备

### 结构化输出
- JSON Schema 完整定义
- 日志保存系统
- 查询功能

### 数据接口
- market_data.py — 行情数据
- fundamental_data.py — 财报数据
- news_data.py — 新闻数据

### 评分脚本
- alpha_thesis_score.py
- market_pricing_score.py
- trade_readiness_score.py
- risk_governor_score.py
- position_risk_score.py

---

## 文件结构

```
BSHL_Alpha_Skill/
├── SKILL.md              # 技能入口
├── README.md             # 完整架构说明
├── ABOUT.md              # 项目介绍
├── QUICKSTART.md         # 快速开始
├── VERSION_ROADMAP.md    # 版本路线图
├── SECURITY.md           # 安全政策
├── CONTRIBUTING.md       # 贡献指南
│
├── constitution/         # 核心原则
│   ├── core_principles.md
│   ├── scope_and_safety.md
│   ├── no_autonomous_trading.md
│   └── terminology.md
│
├── workflows/            # 标准工作流
│   ├── daily_market_radar.md
│   ├── theme_to_asset_mapping.md
│   ├── single_asset_deep_dive.md
│   ├── earnings_event_check.md
│   ├── crypto_token_deep_dive.md
│   ├── trade_readiness_check.md
│   ├── risk_governor_check.md
│   └── post_trade_review.md
│
├── references/           # 参考规则
│   ├── evidence_ladder.md
│   ├── market_regime_gate.md
│   ├── supply_chain_bottleneck_map.md
│   ├── technical_structure_rules.md
│   ├── liquidity_and_crowding_rules.md
│   └── crypto_onchain_rules.md
│
├── prompts/             # 提示词模板
│   ├── radar_prompt.md
│   ├── deep_dive_prompt.md
│   ├── contradiction_prompt.md
│   ├── trade_card_prompt.md
│   └── review_prompt.md
│
├── schemas/             # JSON Schema
│   ├── alpha_thesis.schema.json
│   ├── evidence_ledger.schema.json
│   ├── market_regime.schema.json
│   ├── trade_readiness.schema.json
│   ├── risk_governor.schema.json
│   └── review_log.schema.json
│
├── scoring/             # 评分脚本
│   ├── alpha_thesis_score.py
│   ├── market_pricing_score.py
│   ├── trade_readiness_score.py
│   ├── risk_governor_score.py
│   ├── position_risk_score.py
│   └── scorer.py
│
├── data/                # 数据接口
│   ├── market_data.py
│   ├── fundamental_data.py
│   └── news_data.py
│
├── replay/              # 回放系统
│   ├── replay_engine.py
│   └── case_library.py
│
├── logs/                # 日志系统
│   └── README.md
│
└── examples/            # 示例案例
    ├── stock_deep_dive_example.md
    ├── crypto_token_example.md
    └── failed_trade_review_example.md
```

---

## 适用市场

- 美股、港股、A股
- ETF、指数
- Crypto（RWA、DAT、稳定币、平台币、DePIN、DeSci、Meme）
- 产业主题：AI、半导体、能源与电力、国防科技、生物科技

---

## 快速开始

### 方式一：直接对话

```
用 BSHL Alpha Skill 分析 NVDA
```

### 方式二：指定工作流

```
BSHL Alpha Skill，启动每日雷达
BSHL Alpha Skill，检查这个标的的交易准备状态
BSHL Alpha Skill，复盘这笔交易
```

### 方式三：Card 输出

```
用 BSHL Alpha Skill 生成 MSTR 的完整分析卡
```

---

## 输出示例

### 分析卡片结构

```markdown
## 标的分析卡

### 一、一句话结论
**结论**: AI 电力需求增长驱动输配电设备升级，公司是卡点供应商
**状态**: Trade Ready

### 二、Alpha Thesis
**核心假设**: 数据中心耗电激增 → 电网扩容 → 变压器需求爆发

### 三、证据账本
**强证据**:
- 2024Q4 财报：订单积压创历史新高
- 电网投资法案通过 500 亿专项预算

### 四、反证矩阵
**最大反证**: 传统电力需求疲软可能抵消数据中心增量

### 五、评分
**Alpha Thesis Score**: 78/100 - B
**Market Pricing Score**: 72/100 - B
**Trade Readiness Score**: 81/100 - A
**最终等级**: Trade Ready
```

---

## 安全声明

**本 Skill 不做三件事：**
1. 不做人格模仿
2. 不直接给无条件买卖指令
3. 不默认自动下单

**所有交易决策需用户人工确认。**

---

## 版本路线

| 版本 | 状态 | 说明 |
|------|------|------|
| v0.1 | ✅ | 纯文本 Skill MVP |
| v0.2 | ✅ | 结构化 JSON |
| v0.3 | ✅ | 评分脚本 |
| v0.4 | ✅ | 数据接口 |
| v0.5 | ✅ | 回放系统 |
| v0.6 | 🔜 | 复盘写回 |
| v1.0 | 🔜 | Trading OS 集成 |

详见 [VERSION_ROADMAP.md](VERSION_ROADMAP.md)

---

## 贡献

欢迎提交 Issue 和 Pull Request！

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 免责声明

投资有风险，决策需谨慎。本系统仅为辅助工具，不构成投资建议。用户应对自己的决策负责。

---

*BSHL Alpha Skill — 证据驱动，结构确认，风险优先，复盘进化*

*发布日期: 2026-06-06*
*版本: v0.5*
