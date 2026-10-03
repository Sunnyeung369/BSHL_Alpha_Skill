"""
BSHL Alpha Skill - News Data Interface

新闻数据接口抽象层，支持多新闻源。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, date, timezone
from .contracts import (DataProvenance, DataUnavailableError, MOCK_TIME, mock_metadata,
                        validate_symbol, validate_limit)
from enum import Enum


class Sentiment(Enum):
    """情绪倾向"""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class NewsItem:
    """新闻条目"""
    id: str
    symbol: str
    title: str
    summary: str
    source: str
    author: Optional[str]
    url: str
    published_at: datetime
    sentiment: Optional[Sentiment]
    sentiment_score: Optional[float]  # -1 到 1
    relevance_score: float  # 0 到 1，与标的的相关性
    keywords: List[str]
    source_url: str = ""
    is_mock: bool = False
    data_mode: str = "unavailable"
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class PressRelease(DataProvenance):
    """公司新闻稿"""
    symbol: str
    title: str
    content: str
    release_type: str  # earnings, guidance, product, partnership, etc.
    url: str
    published_at: datetime


@dataclass
class SocialMediaPost(DataProvenance):
    """社媒帖子"""
    platform: str  # twitter, reddit, discord, etc.
    author: str
    content: str
    url: str
    published_at: datetime
    likes: int
    shares: int
    comments: int
    sentiment: Optional[Sentiment]


class NewsDataSource(ABC):
    """新闻数据源抽象类"""

    @abstractmethod
    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """获取新闻"""
        pass

    @abstractmethod
    def get_press_releases(self, symbol: str, limit: int = 10) -> List[PressRelease]:
        """获取公司新闻稿"""
        pass

    @abstractmethod
    def search_news(self, query: str, limit: int = 10) -> List[NewsItem]:
        """搜索新闻"""
        pass


class UnavailableNewsSource(NewsDataSource):
    provider_name = "unconfigured"

    def get_news(self, symbol, limit=10):
        validate_symbol(symbol)
        validate_limit(limit)
        raise DataUnavailableError(f"{self.provider_name}: news is not connected")

    def get_press_releases(self, symbol, limit=10):
        validate_symbol(symbol)
        validate_limit(limit)
        raise DataUnavailableError(f"{self.provider_name}: press releases are not connected")

    def search_news(self, query, limit=10):
        validate_limit(limit)
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query must be a nonempty string")
        raise DataUnavailableError(f"{self.provider_name}: news search is not connected")


class YahooFinanceNews(UnavailableNewsSource):
    provider_name = "yahoo"


class SeekingAlphaNews(UnavailableNewsSource):
    provider_name = "seeking_alpha"


class MockNewsSource(NewsDataSource):
    def __init__(self, *, enabled=False):
        if enabled is not True:
            raise DataUnavailableError("MockNewsSource requires enabled=True")

    def get_news(self, symbol, limit=10):
        symbol = validate_symbol(symbol)
        validate_limit(limit)
        return [NewsItem(f"mock-{symbol}", symbol, f"[MOCK] Synthetic news for {symbol}",
                         "Synthetic fixture, not an actual event.", "mock", None,
                         "https://example.invalid/bshl/mock/news", MOCK_TIME,
                         Sentiment.NEUTRAL, 0.0, 1.0, ["mock"],
                         **{k: v for k, v in mock_metadata("news").items() if k != "source"})]

    def get_press_releases(self, symbol, limit=10):
        symbol = validate_symbol(symbol)
        validate_limit(limit)
        return [PressRelease(symbol, f"[MOCK] {symbol} synthetic release",
                             "Synthetic fixture, not a company announcement.", "mock",
                             "https://example.invalid/bshl/mock/release", MOCK_TIME,
                             **mock_metadata("release"))]

    def search_news(self, query, limit=10):
        raise DataUnavailableError("mock search is unsupported; select a ticker fixture explicitly")


class NewsDataManager:
    def __init__(self, *, enable_mock=False):
        if not isinstance(enable_mock, bool):
            raise ValueError("enable_mock must be an explicit boolean")
        self.sources = {"yahoo": YahooFinanceNews(), "seeking_alpha": SeekingAlphaNews()}
        if enable_mock:
            self.sources["mock"] = MockNewsSource(enabled=True)

    def register_source(self, name, source):
        if not name or not isinstance(source, NewsDataSource):
            raise ValueError("register a named NewsDataSource")
        self.sources[name] = source

    def get_source(self, name):
        if name not in self.sources:
            raise DataUnavailableError(f"news provider {name!r} is not registered")
        return self.sources[name]

    def get_news(self, symbol, limit=10, source="yahoo"):
        return self.get_source(source).get_news(symbol, limit)

    def get_press_releases(self, symbol, limit=10, source="yahoo"):
        return self.get_source(source).get_press_releases(symbol, limit)

    def search_news(self, query, limit=10, source="yahoo"):
        return self.get_source(source).search_news(query, limit)

    def get_all_news(self, symbol, limit=10):
        """Unavailable sources fail explicitly; never silently combine mock with live."""
        validate_limit(limit)
        all_news = []
        for name, provider in self.sources.items():
            if name == "mock":
                continue
            all_news.extend(provider.get_news(symbol, limit))
        all_news.sort(key=lambda item: item.published_at, reverse=True)
        return all_news[:limit]


news_data_manager = NewsDataManager()


def main():
    news = NewsDataManager(enable_mock=True).get_news("DEMO", source="mock")
    for item in news:
        print(f"[{item.data_mode} / {item.published_at.isoformat()}] {item.title}")


if __name__ == "__main__":
    main()
