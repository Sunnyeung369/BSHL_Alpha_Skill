# BSHL Alpha Skill v0.5
## 精准买卖高低结构投研技能系统

---

## 一、系统定位

### 核心能力链路

```
产业链卡点
    ↓
投研证据链 + 市场定价 + K线结构 + 风控总闸 + 复盘写回
```

**系统特点：**

| 维度 | BSHL Alpha Skill |
|------|------------------|
| 核心能力 | 找机会、判断时机、控制亏损 |
| 输出形式 | 作战卡（雷达卡、拆解卡、准备卡、否决卡、复盘卡） |
| 判断原则 | 反证优先 |
| 评分系统 | 三层评分（Alpha Thesis / Market Pricing / Trade Readiness） |
| 系统进化 | 可审计日志 + 规则写回 |

### 一句话定义

> **BSHL Alpha Skill 是一套面向全球多资产类别的 AI 投研到交易准备系统，覆盖美股、港股、A股、ETF、加密货币与代币，用证据链确认逻辑，用市场结构过滤时机，用 K线确认执行窗口，用 Risk Governor 控制风险，用日志系统沉淀复盘资产。**

---

## 二、独特优势（五点升级）

### 1. 从"产业链卡点"升级到"Alpha 生成链"

**核心链路：**
```
宏观环境 → 产业变化 → 供应链卡点 → 公司映射 → 证据链 → 定价差 → 资金结构 → K线位置 → 仓位计划 → 风控否决 → 复盘写回
```

**回答的关键问题：**
- 为什么它可能涨？
- 什么时候可能涨？
- 市场是否已经定价？
- 资金是否已经进场？
- 现在追是低赔率还是高赔率？
- 错了以后在哪里认错？
- 这次失败能沉淀什么规则？

### 2. 从"研究报告"升级到"作战卡"

**五类卡片输出：**

| 卡片类型 | 功能 | 输出 |
|----------|------|------|
| 赛道雷达卡 | 判断方向是否形成机会 | 主题、催化剂、受益链、候选标的 |
| 公司拆解卡 | 判断公司是否真正受益 | Alpha Thesis、证据账本、反证矩阵 |
| 交易准备卡 | 判断是否具备介入条件 | K线结构、入场区、止损位、盈亏比 |
| 风险否决卡 | 判断什么情况必须放弃 | 风控条件、否决原因、观察条件 |
| 复盘归因卡 | 判断成功或失败的真实原因 | 原始判断 vs 实际走势、规则更新 |

### 3. 从"逻辑自洽"升级到"反证优先"

**每个结论必须配：**
- 支持证据
- 反对证据
- 过期证据
- 弱证据
- 一票否决证据
- 需要继续验证的证据

> **没有反证矩阵的投研，全是高级自嗨。**

### 4. 从"分数排名"升级到"三层评分"

| 评分层级 | 解决问题 | 输出 |
|----------|----------|------|
| Alpha Thesis Score | 逻辑是否成立 | 研究价值 |
| Market Pricing Score | 市场是否已经定价 | 赔率价值 |
| Trade Readiness Score | 现在能否进入交易准备 | 执行价值 |

**最终不输出"买入评级"，输出状态：**
- Research Only
- Watchlist
- Trade Ready
- Wait Pullback
- Avoid
- Veto

### 5. 从"AI 观点"升级到"可审计日志"

**每次判断必须留下结构化日志：**
- 当时看的是什么标的
- 当时依据哪些证据
- 当时市场环境如何
- 当时 K线结构如何
- 当时给了什么结论
- 后来价格如何走
- 判断错在哪里
- 哪条规则需要修正

> **没有日志，就没有进化。没有进化，Skill 只是提示词玩具。**

---

## 三、目录结构

```
BSHL_Alpha_Skill/
│
├── SKILL.md              # 技能入口，快速使用指南
├── README.md             # 本文件，完整架构说明
│
├── constitution/         # 核心原则与契约
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
├── references/           # 参考规则与标准
│   ├── evidence_ladder.md
│   ├── market_regime_gate.md
│   ├── supply_chain_bottleneck_map.md
│   ├── valuation_sanity_check.md
│   ├── technical_structure_rules.md
│   ├── liquidity_and_crowding_rules.md
│   ├── crypto_onchain_rules.md
│   ├── macro_liquidity_rules.md
│   └── catalyst_calendar_rules.md
│
├── schemas/             # 结构化数据定义
│   ├── alpha_thesis.schema.json
│   ├── evidence_ledger.schema.json
│   ├── market_regime.schema.json
│   ├── trade_readiness.schema.json
│   ├── risk_governor.schema.json
│   └── review_log.schema.json
│
├── scoring/             # 评分脚本（Python）
│   ├── alpha_thesis_score.py
│   ├── market_pricing_score.py
│   ├── trade_readiness_score.py
│   ├── risk_governor_score.py
│   └── position_risk_score.py
│
├── prompts/             # 核心提示词模板
│   ├── radar_prompt.md
│   ├── deep_dive_prompt.md
│   ├── contradiction_prompt.md
│   ├── trade_card_prompt.md
│   └── review_prompt.md
│
├── examples/            # 示例案例
│   ├── stock_deep_dive_example.md
│   ├── etf_theme_example.md
│   ├── crypto_token_example.md
│   └── failed_trade_review_example.md
│
└── evals/              # 测试与回放
    ├── test_cases.md
    ├── replay_cases.md
    ├── hallucination_tests.md
    └── risk_veto_tests.md
```

---

## 四、六层架构详解

### Layer 1: Universe Radar - 标的雷达层

**职责**：发现机会来源

**覆盖方向：**
- 美股、港股、A股
- ETF、指数
- Crypto（RWA、DAT、稳定币、平台币、DePIN、DeSci、Meme）
- 产业主题：AI、半导体、能源与电力、国防科技、生物科技
- 新兴方向：机器人、核能与电网、消费科技、供应链重构

**输出字段：**
| 字段 | 说明 |
|------|------|
| Theme | 主题 |
| Catalyst | 催化剂 |
| Affected Chain | 受影响产业链 |
| Beneficiary Type | 受益公司类型 |
| Candidate Assets | 候选标的 |
| Urgency | 时间紧迫度 |
| Confidence | 初始置信度 |

---

### Layer 2: Alpha Thesis - 投研假设层

**职责**：判断逻辑是否成立

**核心问题：**
- 需求是否真实增加？
- 供给是否短期受限？
- 公司是否在卡点位置？
- 客户是否愿意付费？
- 收入是否可能兑现？
- 毛利是否可能改善？
- 估值是否仍有空间？
- 催化剂是否临近？
- 有无替代路线？
- 市场是否已经讲烂了？

**标准 Thesis 输出：**
```yaml
标的: XXX
核心假设: ...
受益链条: ...
关键证据: ...
反证条件: ...
催化时间: ...
估值错配: ...
最大风险: ...
结论等级: ...
```

---

### Layer 3: Evidence Ledger - 证据账本层

**职责**：结构化管理每条证据

**证据结构：**
```json
{
  "claim": "公司可能受益于某产业链卡点",
  "source_type": "filing / transcript / company_release / industry_report / media / social",
  "source_date": "YYYY_MM_DD",
  "evidence_strength": "strong / medium / weak",
  "supports_or_refutes": "supports / refutes / mixed",
  "affected_thesis": "demand / supply / margin / valuation / catalyst / risk",
  "freshness": "fresh / aging / stale",
  "confidence": 0.0,
  "kill_switch": true
}
```

**硬规则：**
> **强证据可以提高置信度，弱证据只能提出假设，不能单独支撑交易准备。**

---

### Layer 4: Market Regime - 市场状态层

**职责**：判断市场环境

**必须判断：**
- 大盘趋势、板块趋势
- 利率压力、美元流动性
- 风险偏好、资金宽度
- 主题拥挤度、期权情绪
- 空头结构、龙头股延续性

**输出状态：**
| 状态 | 含义 |
|------|------|
| Risk On | 可以提高进攻权重 |
| Neutral | 只做强逻辑强结构 |
| Risk Off | 降仓或只观察 |
| Crowded | 防止高位接盘 |
| Rotation | 注意板块切换 |
| Breakdown | 风控优先 |

> **没有市场状态过滤的投研系统，迟早会在好逻辑里亏钱。**

---

### Layer 5: BSHL K线结构层

**职责**：确认交易时机

**必须检查：**
- 母周期方向、子周期位置
- 高低结构、突破是否有效
- 回踩是否健康、成交量是否确认
- 相对强弱是否跑赢
- ATR 波动是否过大
- 止损位是否清晰、盈亏比是否足够

**输出结构：**
| 结构 | 含义 |
|------|------|
| Base Building | 筑底观察 |
| Breakout Watch | 突破观察 |
| Confirmed Breakout | 确认突破 |
| Pullback Entry Zone | 回踩准备区 |
| Exhaustion | 过热 |
| Breakdown | 破位 |
| No Trade | 没有交易结构 |

**硬规则：**
- 没有收盘确认，不升级交易状态
- 没有止损位，不进入执行准备
- 没有日志，不允许复盘归因

---

### Layer 6: Risk Governor - 风控总闸层

**职责**：让系统活下去

**一票否决条件：**
- 流动性不足
- 波动过大
- 证据质量太弱
- 社媒热度过度拥挤
- 财报前风险过高
- 重大监管不确定
- 个股已远离均值
- 止损距离过大
- 仓位暴露过高
- 相关资产集中度过高

**输出决策：**
| 决策 | 含义 |
|------|------|
| Pass | 通过 |
| Reduce Size | 降低仓位 |
| Watch Only | 只观察 |
| Wait Confirmation | 等确认 |
| Veto | 否决 |

> **AI 可以提出交易准备建议，Risk Governor 可以直接否决，AI 没有绕过风控的权限。**

---

## 五、标准输出模板

### 【BSHL Alpha Skill 分析卡】

```markdown
## 标的分析卡

**标的**: [Ticker/Name]
**资产类别**: [美股/港股/A股/ETF/Crypto/Token]
**日期**: [YYYY-MM-DD]
**当前任务**: [雷达 / 深度拆解 / 交易准备 / 风控复盘]

---

### 一、一句话结论
**结论**: [一句话总结]
**状态**: [Research Only / Watchlist / Trade Ready / Wait Pullback / Avoid / Veto]

### 二、Alpha Thesis
**核心假设**:
**产业链位置**:
**需求驱动**:
**供给约束**:
**公司受益路径**:
**催化剂**:
**时间窗口**:

### 三、证据账本
**强证据**:
- [证据1] (来源: XXX, 日期: XXX)
- [证据2]

**中证据**:
- [证据1]

**弱证据**:
- [证据1]

**过期证据**:
- [证据1]

**待验证证据**:
- [证据1]

### 四、反证矩阵
**最大反证**:
**替代解释**:
**一票否决证据**:
**需要继续跟踪的问题**:

### 五、市场状态
**大盘**: [趋势]
**板块**: [相对强弱]
**资金**: [流入/流出]
**拥挤度**: [高/中/低]
**风险偏好**: [Risk On/Neutral/Risk Off]

### 六、K线结构
**母周期**: [方向]
**子周期**: [位置]
**关键高低点**: [高点/低点]
**支撑区**: [价位]
**压力区**: [价位]
**交易结构**: [Base Building / Breakout Watch / ...]
**收盘确认状态**: [已确认/未确认]

### 七、Risk Governor
**流动性**: [充足/不足]
**波动**: [可控/过大]
**仓位**: [建议仓位]
**相关性**: [与其他持仓相关性]
**止损可执行性**: [清晰/模糊]
**最终风控结论**: [Pass/Reduce/Watch/Veto]

### 八、行动建议
**研究动作**:
**观察动作**:
**交易准备条件**:
**放弃条件**:
**复盘时间**:

### 九、评分
**Alpha Thesis Score**: [X/100] - [评级]
**Market Pricing Score**: [X/100] - [评级]
**Trade Readiness Score**: [X/100] - [评级]
**Risk Governor**: [状态]
**最终等级**: [等级]
```

---

## 六、核心工作流

### 工作流 1：每日雷达

**输入：**
```
今天帮我扫描 AI、半导体、能源、电力、Crypto、RWA 方向，有哪些值得进入观察池的标的？
```

**输出表格：**
| 主题 | 触发原因 | 受益链条 | 候选标的 | 证据等级 | 市场热度 | 交易状态 |
|------|----------|----------|----------|----------|----------|----------|
| AI 电力 | 数据中心耗电增长 | 电网、变压器、核能 | A/B/C | 中高 | 高 | Watchlist |
| RWA | 监管与机构采用 | 代币化资产、结算层 | X/Y/Z | 中 | 中 | Research Only |

---

### 工作流 2：单标的深度拆解

**输入：**
```
用 BSHL Alpha Skill 分析 NVDA / MSTR / ETH / 某只股票
```

**输出结构：**（见标准输出模板）

---

### 工作流 3：交易准备检查

**输入：**
```
这个标的已经涨了一段，现在还能不能追？
```

**输出示例：**
```
研究价值：高
交易状态：等待回踩
K线结构：远离合理入场区
拥挤风险：高
Risk Governor：Watch Only

建议动作：加入观察池，等待回踩确认或新平台构筑
失效条件：跌破关键结构位且放量
```

---

### 工作流 4：财报前后检查

**必须检查：**
- 市场预期是否过高
- 期权隐含波动是否过高
- 股价是否已经提前反应
- 收入与指引哪个更关键
- 毛利率是否是核心变量
- 管理层措辞是否改变
- 财报后是否出现放量缺口
- 是否需要等待二次确认

**输出：**
| 结果 | 动作 |
|------|------|
| Pre Earnings High Risk | 财报前不追 |
| Post Earnings Gap Hold | 等缺口确认 |
| Guidance Breakout | 观察趋势延续 |
| Sell The News | 避免情绪兑现 |

---

### 工作流 5：复盘写回

**每次交易或观察结束后，必须复盘：**

```markdown
原始判断:
实际走势:
判断正确部分:
判断错误部分:
证据是否失效:
市场状态是否误判:
K线是否提前预警:
风控是否执行:
需要新增规则:
```

**沉淀规则示例：**
```
Rule Update:
当主题热度过高，且标的远离 20 日均线超过 X 倍 ATR，即使 Alpha Thesis 为高，也不能升级为 Trade Ready。
```

---

## 七、评分系统

### 1. Alpha Thesis Score（满分 100）

| 维度 | 权重 |
|------|------|
| 需求拐点 | 15 |
| 供应链卡点 | 15 |
| 公司受益确定性 | 15 |
| 证据质量 | 15 |
| 催化剂时间 | 10 |
| 估值错配 | 10 |
| 竞争格局 | 10 |
| 反证清晰度 | 10 |

**评级：**
- 85 以上：A
- 70-84：B
- 55-69：C
- 55 以下：D

---

### 2. Market Pricing Score（满分 100）

| 维度 | 权重 |
|------|------|
| 板块趋势 | 15 |
| 相对强弱 | 15 |
| 资金流入 | 15 |
| 拥挤度 | 15 |
| 估值消化程度 | 15 |
| 市场风险偏好 | 15 |
| 催化未定价程度 | 10 |

**注意：拥挤度高要扣分。**

---

### 3. Trade Readiness Score（满分 100）

| 维度 | 权重 |
|------|------|
| 母周期方向 | 15 |
| 子周期结构 | 15 |
| 突破确认 | 15 |
| 回踩质量 | 10 |
| 成交量确认 | 10 |
| 止损清晰度 | 15 |
| 盈亏比 | 15 |
| 波动可控 | 5 |

**交易准备等级：**
- 85 以上：Trade Ready
- 70-84：Watch Closely
- 55-69：Wait
- 55 以下：No Trade

---

### 4. Risk Governor

Risk Governor 不看总分，只看是否触发否决。

| 风险 | 动作 |
|------|------|
| 证据弱 | Research Only |
| 流动性差 | Veto |
| 止损过远 | Veto |
| 过度拥挤 | Reduce Size 或 Watch Only |
| 财报前波动过高 | Wait |
| 市场 Risk Off | 降级 |
| K线破位 | Veto |
| 仓位相关性过高 | Reduce Size |

---

## 八、实施路线

### 第 1 阶段：纯文本 Skill v0.1 ✅ 已完成 (2026-06-06)

**交付物：**
- SKILL.md ✅
- constitution/ ✅
- workflows/ ✅
- references/ ✅
- prompts/ ✅
- examples/ ✅

---

### 第 2 阶段：结构化 JSON v0.2 ✅ 已完成 (2026-06-06)

**交付物：**
- alpha_thesis.schema.json ✅
- evidence_ledger.schema.json ✅
- market_regime.schema.json ✅
- trade_readiness.schema.json ✅
- risk_governor.schema.json ✅
- review_log.schema.json ✅

---

### 第 3 阶段：评分脚本 v0.3 ✅ 已完成 (2026-06-06)

**交付物：**
- alpha_thesis_score.py ✅
- market_pricing_score.py ✅
- trade_readiness_score.py ✅
- risk_governor_score.py ✅
- position_risk_score.py ✅
- scorer.py ✅

---

### 第 4 阶段：数据接口 v0.4 ✅ 已完成 (2026-06-06)

**数据源：**
- 行情数据、财报数据、新闻数据
- SEC 文件、ETF 持仓
- 链上数据、社媒热度、期权数据

**交付物：**
- market_data.py ✅
- fundamental_data.py ✅
- news_data.py ✅

---

### 第 5 阶段：回放系统 v0.5 ✅ 当前版本 (2026-06-06)

**目标：** 验证规则有效性 + 个人专属进化

**交付物：**
- replay_engine.py ✅
- case_library.py ✅
- personal_evolution.py ✅ — 个人专属进化系统
- 规则验证脚本 ✅
- 性能报告生成 ✅

**核心能力：**
- **个人进化** — 根据用户真实使用历史自适应调整规则权重
- **规则动态** — 成功率低的规则自动降权或禁用
- **专属洞察** — 基于个人交易历史的成功率分析
- **经验沉淀** — 自动积累个人交易经验

**回放案例：**
- 好逻辑但价格已透支
- 好公司但市场 Risk Off
- 小票社媒拉盘后暴跌
- 财报超预期但高开低走
- 主题强但影子股不涨
- 龙头强势，跟风股失效
- 链上信号强但价格破位
- ETF 强于个股
- 证据强但收入兑现慢
- 高拥挤交易被反杀

---

## 九、使用指南

### 快速开始

1. **单标的分析**
```
用 BSHL Alpha Skill 分析 NVDA
```

2. **主题扫描**
```
BSHL Alpha Skill，帮我扫描 AI 电力主题的机会
```

3. **交易准备检查**
```
BSHL Alpha Skill，检查 COIN 现在的交易准备状态
```

4. **生成完整卡片**
```
用 BSHL Alpha Skill 为 MSTR 生成完整分析卡
```

---

## 十、版本信息

- **当前版本**: v0.5 回放系统
- **发布日期**: 2026-06-06
- **覆盖市场**: 美股、港股、A股、ETF、加密货币、代币、全球各类可交易资产
- **核心优势**: 完整六层架构，结构化输出，自动评分，数据接口，回放验证

---

*BSHL Alpha Skill — 证据驱动，结构确认，风险优先，复盘进化*
