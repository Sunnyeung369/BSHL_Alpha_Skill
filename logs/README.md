# BSHL Alpha Skill 日志系统

---

## 目录结构

```
logs/
├── alpha_thesis/      # 投研假设日志
├── trade_readiness/   # 交易准备日志
├── risk_governor/     # 风控检查日志
└── reviews/           # 复盘日志
```

---

## 日志命名规范

### Alpha Thesis
```
格式: {ticker}_{date}_alpha_thesis.json
示例: NVDA_2026-08-01_alpha_thesis.json
```

### Trade Readiness
```
格式: {ticker}_{date}_trade_readiness.json
示例: NVDA_2026-08-01_trade_readiness.json
```

### Risk Governor
```
格式: {ticker}_{date}_risk_governor.json
示例: NVDA_2026-08-01_risk_governor.json
```

### Reviews
```
格式: {ticker}_{review_date}_review_{id}.json
示例: NVDA_2026-08-15_review_001.json
```

---

## 日志内容

### Alpha Thesis 日志

包含：
- 标的信息
- 核心假设
- 证据账本
- 反证矩阵
- 评分详情

### Trade Readiness 日志

包含：
- 定价状态
- 拥挤度检查
- K线结构
- 风控检查
- 交易建议

### Risk Governor 日志

包含：
- 风险检查清单
- 触发条件
- 最终决策
- 失效条件

### Review 日志

包含：
- 原始判断
- 实际走势
- 对比分析
- 规则更新
- 经验总结

---

## 使用指南

### 保存日志

```
# 保存完整分析
用 BSHL Alpha Skill 分析 NVDA，保存为 JSON

# 只保存特定部分
用 BSHL Alpha Skill 分析 NVDA 的风控状态，保存为 JSON
```

### 查询日志

```
# 查询标的的所有日志
查询 NVDA 的所有日志

# 查询特定类型的日志
查询 NVDA 的复盘日志

# 查询时间范围的日志
查询 2026-07 月的所有分析
```

---

## 日志保留策略

- Alpha Thesis: 永久保留
- Trade Readiness: 保留 1 年
- Risk Governor: 保留 6 个月
- Reviews: 永久保留

---

## 数据清理

定期清理过期日志：

```python
# 清理 6 个月前的 Trade Readiness 日志
python scripts/clean_logs.py --type trade_readiness --days 180
```

---

*最后更新: 2026-08-01*
