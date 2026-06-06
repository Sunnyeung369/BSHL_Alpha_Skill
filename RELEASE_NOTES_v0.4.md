# v0.4 Release Notes
## BSHL Alpha Skill v0.4 数据接口版本

---

## 版本信息

- **版本号**: v0.4
- **发布日期**: 2026-10-01
- **状态**: ✅ 已完成

---

## 新增功能

### 1. 数据接口抽象层

| 模块 | 功能 |
|------|------|
| market_data.py | 行情数据接口 |
| fundamental_data.py | 基本面数据接口 |
| news_data.py | 新闻数据接口 |

### 2. 支持多数据源

- **Yahoo Finance**: 行情、基本面、新闻
- **Alpha Vantage**: 行情数据
- **SEC**: 财报文件
- **Crypto Exchanges**: 加密货币数据

### 3. 半自动评分

数据可以自动获取，减少手工输入：

```python
from data import market_data_manager, fundamental_data_manager
from scoring import BSHEAlphaScorer

# 获取数据
quote = market_data_manager.get_quote("NVDA")
indicators = market_data_manager.get_technical_indicators("NVDA")
financials = fundamental_data_manager.get_latest_financials("NVDA")

# 计算评分
scorer = BSHEAlphaScorer()
result = scorer.score_complete(
    ticker="NVDA",
    date="2026-10-01",
    # 使用实际数据
    parent_cycle_direction=14 if indicators.ma20 < quote.price else 5,
    # ...
)
```

### 4. 数据源可替换

设计原则：**数据源可以替换，字段标准不能乱**

```python
# 注册自定义数据源
from data.market_data import MarketDataManager, MarketDataSource

class MyDataSource(MarketDataSource):
    def get_quote(self, symbol):
        # 自定义实现
        pass

market_data_manager.register_source("my_source", MyDataSource())
```

---

## 数据接口定义

### 行情数据 (Market Data)

```python
Quote:
    symbol: str
    price: float
    change: float
    change_percent: float
    high: float
    low: float
    volume: float
    timestamp: datetime
    market: str

OHLCV:
    symbol, timestamp, open, high, low, close, volume

TechnicalIndicator:
    symbol, timestamp, ma20, ma50, ma200, rsi, atr, atr_percent

OptionData:
    symbol, timestamp, call_volume, put_volume, iv, iv_percentile
```

### 基本面数据 (Fundamental Data)

```python
CompanyInfo:
    symbol, name, exchange, sector, industry, market_cap, description

Financials:
    symbol, period, fiscal_year, report_date
    revenue, gross_margin, net_income, eps
    total_assets, cash_and_equivalents, free_cash_flow

Guidance:
    symbol, period, fiscal_year
    revenue_guidance_low/high, eps_guidance_low/high

EarningsCall:
    symbol, fiscal_year, period, call_date, transcript_available
```

### 新闻数据 (News Data)

```python
NewsItem:
    id, symbol, title, summary, source, url, published_at
    sentiment, sentiment_score, relevance_score, keywords

PressRelease:
    symbol, title, content, release_type, url, published_at
```

---

## 使用指南

### 基本使用

```python
# 导入数据管理器
from data import market_data_manager, fundamental_data_manager, news_data_manager

# 获取行情
quote = market_data_manager.get_quote("NVDA")
print(f"{quote.symbol}: ${quote.price}")

# 获取技术指标
indicators = market_data_manager.get_technical_indicators("NVDA")
print(f"MA20: ${indicators.ma20}, RSI: {indicators.rsi}")

# 获取财报
financials = fundamental_data_manager.get_latest_financials("NVDA")
print(f"Revenue: ${financials.revenue/1e9:.1f}B")

# 获取新闻
news = news_data_manager.get_news("NVDA", limit=5)
for item in news:
    print(f"[{item.sentiment.value}] {item.title}")
```

### 使用自定义数据源

```python
from data.market_data import MarketDataSource, Quote
from datetime import datetime

class MyDataSource(MarketDataSource):
    def get_quote(self, symbol):
        # 实现自定义获取逻辑
        return Quote(
            symbol=symbol,
            price=100.0,
            # ...
        )

# 注册数据源
market_data_manager.register_source("my_source", MyDataSource())

# 使用自定义数据源
quote = market_data_manager.get_quote("NVDA", source="my_source")
```

---

## 数据字段标准

### 必须字段

每个数据类型都有必须字段，数据源必须提供：

- Quote: symbol, price, timestamp, market
- OHLCV: symbol, timestamp, open, high, low, close, volume
- CompanyInfo: symbol, name, sector, market_cap
- Financials: symbol, period, fiscal_year, report_date, revenue, eps
- NewsItem: id, symbol, title, source, url, published_at

### 可选字段

可选字段用于增强功能，但不是必需的：

- TechnicalIndicator: ma20, ma50, ma200, rsi, atr, atr_percent
- OptionData: iv_percentile
- NewsItem: sentiment, sentiment_score

---

## 向后兼容

v0.4 保持与 v0.3 完全兼容：
- 评分脚本接口不变
- JSON Schema 格式不变
- 输出状态定义不变

---

## 已知限制

1. **API 需要配置**: 实际数据源需要 API Key
2. **数据质量差异**: 不同数据源数据质量可能不同
3. **更新频率**: 数据更新频率取决于数据源

---

## 下一步 (v0.5)

v0.5 将实现：
- 回放案例库
- 规则验证脚本
- 性能报告
- 历史回测功能

---

*最后更新: 2026-10-01*
*版本: v0.4*
