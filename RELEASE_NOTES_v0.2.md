# v0.2 Release Notes
## BSHL Alpha Skill v0.2 结构化 JSON 版本

---

## 版本信息

- **版本号**: v0.2
- **发布日期**: 2026-08-01
- **状态**: ✅ 已完成

---

## 新增功能

### 1. 完整的 Schema 定义

| Schema | 说明 |
|--------|------|
| alpha_thesis.schema.json | 投研假设结构化定义 |
| evidence_ledger.schema.json | 证据账本结构化定义 |
| market_regime.schema.json | 市场状态结构化定义 |
| trade_readiness.schema.json | 交易准备状态结构化定义 |
| risk_governor.schema.json | 风控总闸结构化定义 |
| review_log.schema.json | 复盘日志结构化定义 |

### 2. JSON 输出支持

系统现在支持两种输出格式：
- **Markdown**: 人类可读（默认）
- **JSON**: 机器可处理

**获取 JSON 输出**：
```
用 BSHL Alpha Skill 分析 NVDA，输出 JSON 格式
```

### 3. 日志保存系统

所有分析可以保存为 JSON 文件，用于：
- 历史查询
- 回放验证
- 规则进化

**保存位置**:
```
D:\CC Projects\.claude\skills\BSHL_Alpha_Skill\logs\
├── alpha_thesis\
├── trade_readiness\
├── risk_governor\
└── reviews\
```

### 4. 简单查询功能

**查询历史分析**:
```
查询 NVDA 的历史分析
```

**查询主题相关标的**:
```
查询 AI 电力主题的相关分析
```

**查询复盘记录**:
```
查询 COIN 的复盘记录
```

---

## 数据格式

### Alpha Thesis JSON 示例

```json
{
  "ticker": "NVDA",
  "name": "NVIDIA Corporation",
  "asset_class": "US_STOCK",
  "date": "2026-08-01",
  "core_hypothesis": "AI 数据中心建设将持续推动 GPU 需求增长",
  "alpha_thesis_score": {
    "total": 78,
    "grade": "B",
    "breakdown": {
      "demand_inflection": 14,
      "supply_chain_bottleneck": 13,
      "company_benefit_certainty": 14,
      "evidence_quality": 14,
      "catalyst_timing": 9,
      "valuation_mismatch": 6,
      "competition": 8,
      "contradiction_clarity": 10
    }
  },
  "evidence_ledger": [
    {
      "id": "ev-001",
      "claim": "数据中心收入同比增长 427%",
      "source_type": "filing",
      "source_name": "10-Q",
      "source_date": "2025-05-28",
      "evidence_strength": "strong",
      "supports_or_refutes": "supports",
      "affected_thesis": ["demand"],
      "freshness": "fresh",
      "confidence": 0.9,
      "kill_switch": false
    }
  ],
  "status": "Wait Pullback"
}
```

---

## 使用指南

### 保存分析为 JSON

```
用 BSHL Alpha Skill 分析 NVDA，保存为 JSON
```

### 查询历史

```
# 查询特定标的
查询 NVDA 的所有分析

# 查询特定日期
查询 2026-07 的所有分析

# 查询特定状态
查询所有 Trade Ready 状态的分析
```

---

## 向后兼容

v0.2 保持与 v0.1 完全兼容：
- 所有 Markdown 输出格式不变
- 状态定义保持一致
- 评分逻辑保持一致

---

## 已知限制

1. **日志无自动同步**: 需要手动触发保存
2. **查询功能简单**: 只支持基础查询
3. **无自动验证**: JSON 格式需人工验证

---

## 下一步 (v0.3)

v0.3 将实现：
- 可计算的评分脚本
- 自动评分验证
- 评分对比功能

---

*最后更新: 2026-08-01*
*版本: v0.2*
