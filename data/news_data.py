"""
BSHL Alpha Skill - News Data Interface

新闻数据接口抽象层，支持多新闻源。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, date
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


@dataclass
class PressRelease:
    """公司新闻稿"""
    symbol: str
    title: str
    content: str
    release_type: str  # earnings, guidance, product, partnership, etc.
    url: str
    published_at: datetime


@dataclass
class SocialMediaPost:
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


class YahooFinanceNews(NewsDataSource):
    """Yahoo Finance 新闻源 (示例实现)"""

    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        # 实际实现需要调用 Yahoo Finance API
        return [
            NewsItem(
                id="1",
                symbol=symbol,
                title=f"{symbol} beats earnings expectations",
                summary="Company reported strong Q2 results...",
                source="Yahoo Finance",
                author="John Doe",
                url="https://finance.yahoo.com/news/...",
                published_at=datetime.now(),
                sentiment=Sentiment.POSITIVE,
                sentiment_score=0.7,
                relevance_score=0.9,
                keywords=["earnings", "beat", "strong"],
            ),
            NewsItem(
                id="2",
                symbol=symbol,
                title=f"Analyst upgrades {symbol}",
                summary="Following strong results...",
                source="Bloomberg",
                author="Jane Smith",
                url="https://bloomberg.com/...",
                published_at=datetime.now(),
                sentiment=Sentiment.POSITIVE,
                sentiment_score=0.5,
                relevance_score=0.8,
                keywords=["upgrade", "analyst", "rating"],
            ),
        ]

    def get_press_releases(self, symbol: str, limit: int = 10) -> List[PressRelease]:
        return [
            PressRelease(
                symbol=symbol,
                title=f"{symbol} Reports Q2 2025 Financial Results",
                content="Company announces Q2 revenue of $26B...",
                release_type="earnings",
                url="https://example.com/pr/...",
                published_at=datetime.now(),
            )
        ]

    def search_news(self, query: str, limit: int = 10) -> List[NewsItem]:
        return []


class SeekingAlphaNews(NewsDataSource):
    """Seeking Alpha 新闻源 (示例实现)"""

    def get_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        return []

    def get_press_releases(self, symbol: str, limit: int = 10) -> List[PressRelease]:
        return []

    def search_news(self, query: str, limit: int = 10) -> List[NewsItem]:
        return []


class NewsDataManager:
    """新闻数据管理器"""

    def __init__(self):
        self.sources: Dict[str, NewsDataSource] = {}
        self._init_default_sources()

    def _init_default_sources(self):
        """初始化默认数据源"""
        self.sources["yahoo"] = YahooFinanceNews()
        self.sources["seeking_alpha"] = SeekingAlphaNews()

    def register_source(self, name: str, source: NewsDataSource):
        """注册数据源"""
        self.sources[name] = source

    def get_source(self, name: str) -> Optional[NewsDataSource]:
        """获取数据源"""
        return self.sources.get(name)

    def get_news(self, symbol: str, limit: int = 10, source: str = "yahoo") -> List[NewsItem]:
        """获取新闻"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_news(symbol, limit)
        return []

    def get_press_releases(self, symbol: str, limit: int = 10, source: str = "yahoo") -> List[PressRelease]:
        """获取公司新闻稿"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_press_releases(symbol, limit)
        return []

    def search_news(self, query: str, limit: int = 10, source: str = "yahoo") -> List[NewsItem]:
        """搜索新闻"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.search_news(query, limit)
        return []

    def get_all_news(self, symbol: str, limit: int = 10) -> List[NewsItem]:
        """从所有数据源获取新闻"""
        all_news = []
        for source_name, source_obj in self.sources.items():
            news = source_obj.get_news(symbol, limit)
            all_news.extend(news)
        # 按时间排序
        all_news.sort(key=lambda x: x.published_at, reverse=True)
        return all_news[:limit]


# 全局实例
news_data_manager = NewsDataManager()


def main():
    """示例用法"""
    # 获取新闻
    news = news_data_manager.get_news("NVDA", limit=5)
    for item in news:
        print(f"[{item.source}] {item.title}")
        print(f"  情绪: {item.sentiment.value if item.sentiment else 'N/A'}")
        print(f"  相关性: {item.relevance_score:.2f}")


if __name__ == "__main__":
    main()
