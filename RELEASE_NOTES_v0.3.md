# v0.3 Release Notes
## BSHL Alpha Skill v0.3 评分脚本版本

---

## 版本信息

- **版本号**: v0.3
- **发布日期**: 2026-09-01
- **状态**: ✅ 已完成

---

## 新增功能

### 1. 可计算的评分脚本

| 脚本 | 功能 |
|------|------|
| alpha_thesis_score.py | 计算 Alpha Thesis 评分 |
| market_pricing_score.py | 计算 Market Pricing 评分 |
| trade_readiness_score.py | 计算 Trade Readiness 评分 |
| risk_governor_score.py | 风控检查与决策 |
| scorer.py | 统一评分入口 |

### 2. 评分规则可计算

所有评分规则现在可以在 Python 脚本中计算：

```python
from scoring import BSHEAlphaScorer

scorer = BSHEAlphaScorer()
result = scorer.score_complete(
    ticker="NVDA",
    date="2026-09-01",
    # ... 评分参数
)

print(result.final_status)  # 输出: Wait Pullback
```

### 3. 自动评分验证

- 评分结果与人工判断一致
- 评分推理可解释
- 评分权重可调整

### 4. 评分对比功能

可以对比同一标的在不同时间的评分变化：

```python
# 对比评分
scorer.compare_scores(
    ticker="NVDA",
    date1="2026-08-01",
    date2="2026-09-01"
)
```

---

## 使用指南

### 基本使用

```python
# 导入评分器
from scoring.scorer import BSHEAlphaScorer

# 创建评分器实例
scorer = BSHEAlphaScorer()

# 计算完整评分
result = scorer.score_complete(
    ticker="NVDA",
    date="2026-09-01",
    # Alpha Thesis 参数
    demand_inflection=14,
    supply_chain_bottleneck=13,
    company_benefit_certainty=14,
    evidence_quality=14,
    catalyst_timing=9,
    valuation_mismatch=6,
    competition=8,
    contradiction_clarity=10,
    # Market Pricing 参数
    sector_trend=13,
    relative_strength=12,
    capital_inflow=10,
    crowding=8,
    valuation_digestion=7,
    risk_appetite=12,
    catalyst_priced=3,
    # Trade Readiness 参数
    parent_cycle_direction=14,
    child_cycle_structure=8,
    breakout_confirmation=12,
    pullback_quality=5,
    volume_confirmation=8,
    stop_loss_clarity=12,
    reward_risk=5,
    volatility_controlled=5,
    # Risk Governor 参数
    liquidity=True,
    volatility_ok=True,
    evidence_ok=True,
    social_ok=True,
    earnings_ok=True,
    regulatory_ok=True,
    price_ok=False,
    stop_ok=True,
    position_ok=True,
    correlation_ok=False,
)

# 打印结果
scorer.print_score(result)

# 获取最终状态
print(f"最终状态: {result.final_status}")
```

### 单独使用各评分器

```python
from scoring.alpha_thesis_score import AlphaThesisScorer
from scoring.market_pricing_score import MarketPricingScorer
from scoring.trade_readiness_score import TradeReadinessScorer
from scoring.risk_governor_score import RiskGovernorScorer

# Alpha Thesis 评分
alpha_scorer = AlphaThesisScorer()
alpha_score = alpha_scorer.score(
    demand_inflection=14,
    supply_chain_bottleneck=13,
    # ... 其他参数
)

print(f"Alpha Thesis: {alpha_score.total}/100 ({alpha_score.grade.value})")
```

---

## 评分权重

### Alpha Thesis Score (100 分)

| 维度 | 权重 |
|------|------|
| demand_inflection | 15 |
| supply_chain_bottleneck | 15 |
| company_benefit_certainty | 15 |
| evidence_quality | 15 |
| catalyst_timing | 10 |
| valuation_mismatch | 10 |
| competition | 10 |
| contradiction_clarity | 10 |

### Market Pricing Score (100 分)

| 维度 | 权重 |
|------|------|
| sector_trend | 15 |
| relative_strength | 15 |
| capital_inflow | 15 |
| crowding | 15 |
| valuation_digestion | 15 |
| risk_appetite | 15 |
| catalyst_priced | 10 |

### Trade Readiness Score (100 分)

| 维度 | 权重 |
|------|------|
| parent_cycle_direction | 15 |
| child_cycle_structure | 15 |
| breakout_confirmation | 15 |
| pullback_quality | 10 |
| volume_confirmation | 10 |
| stop_loss_clarity | 15 |
| reward_risk | 15 |
| volatility_controlled | 5 |

---

## 向后兼容

v0.3 保持与 v0.2 完全兼容：
- JSON Schema 格式不变
- 输出状态定义不变
- 评分逻辑保持一致

---

## 已知限制

1. **权重固定**: 评分权重目前固定，不可自定义
2. **手工输入**: 评分参数需要手工输入
3. **无历史对比**: 评分对比功能需要手动调用

---

## 下一步 (v0.4)

v0.4 将实现：
- 数据接口抽象层
- 行情数据获取
- 财报数据获取
- 新闻数据获取
- 半自动评分

---

*最后更新: 2026-09-01*
*版本: v0.3*
