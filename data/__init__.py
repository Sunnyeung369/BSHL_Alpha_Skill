"""
BSHL Alpha Skill - Data Interfaces Package

数据接口抽象层，支持多数据源。
"""

from .market_data import market_data_manager, MarketDataManager, Quote, OHLCV, TechnicalIndicator, OptionData
from .fundamental_data import fundamental_data_manager, FundamentalDataManager, CompanyInfo, Financials, Guidance, EarningsCall
from .news_data import news_data_manager, NewsDataManager, NewsItem, PressRelease, Sentiment

__all__ = [
    # Market Data
    "market_data_manager",
    "MarketDataManager",
    "Quote",
    "OHLCV",
    "TechnicalIndicator",
    "OptionData",
    # Fundamental Data
    "fundamental_data_manager",
    "FundamentalDataManager",
    "CompanyInfo",
    "Financials",
    "Guidance",
    "EarningsCall",
    # News Data
    "news_data_manager",
    "NewsDataManager",
    "NewsItem",
    "PressRelease",
    "Sentiment",
]
