"""
BSHL Alpha Skill - Market Data Interface

行情数据接口抽象层，支持多数据源。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, date
import json


@dataclass
class Quote:
    """行情数据"""
    symbol: str
    price: float
    change: float
    change_percent: float
    high: float
    low: float
    volume: float
    timestamp: datetime
    market: str  # US, HK, CN, CRYPTO


@dataclass
class OHLCV:
    """K线数据"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TechnicalIndicator:
    """技术指标"""
    symbol: str
    timestamp: datetime
    ma20: Optional[float] = None
    ma50: Optional[float] = None
    ma200: Optional[float] = None
    rsi: Optional[float] = None
    atr: Optional[float] = None
    atr_percent: Optional[float] = None


@dataclass
class OptionData:
    """期权数据"""
    symbol: str
    timestamp: datetime
    call_volume: float
    put_volume: float
    call_open_interest: float
    put_open_interest: float
    iv: float
    iv_percentile: Optional[float] = None


class MarketDataSource(ABC):
    """行情数据源抽象类"""

    @abstractmethod
    def get_quote(self, symbol: str) -> Quote:
        """获取实时行情"""
        pass

    @abstractmethod
    def get_ohlcv(self, symbol: str, period: str, limit: int) -> List[OHLCV]:
        """获取K线数据

        Args:
            symbol: 标的代码
            period: 周期 (1m, 5m, 15m, 1h, 1d, 1w, 1M)
            limit: 数量限制
        """
        pass

    @abstractmethod
    def get_technical_indicators(self, symbol: str) -> TechnicalIndicator:
        """获取技术指标"""
        pass

    @abstractmethod
    def get_options_data(self, symbol: str) -> Optional[OptionData]:
        """获取期权数据"""
        pass


class AlphaQuoteSource(MarketDataSource):
    """Alpha Vantage 数据源 (示例实现)"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"

    def get_quote(self, symbol: str) -> Quote:
        """获取实时行情"""
        # 实际实现需要调用 API
        # 这里返回示例数据
        return Quote(
            symbol=symbol,
            price=100.0,
            change=2.5,
            change_percent=2.56,
            high=102.0,
            low=98.0,
            volume=1000000,
            timestamp=datetime.now(),
            market="US",
        )

    def get_ohlcv(self, symbol: str, period: str = "1d", limit: int = 100) -> List[OHLCV]:
        """获取K线数据"""
        # 实际实现需要调用 API
        return []

    def get_technical_indicators(self, symbol: str) -> TechnicalIndicator:
        """获取技术指标"""
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(),
            ma20=98.0,
            ma50=95.0,
            ma200=90.0,
            rsi=65.0,
            atr=3.0,
            atr_percent=3.0,
        )

    def get_options_data(self, symbol: str) -> Optional[OptionData]:
        """获取期权数据"""
        return None


class YahooQuoteSource(MarketDataSource):
    """Yahoo Finance 数据源 (示例实现)"""

    def __init__(self):
        self.base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"

    def get_quote(self, symbol: str) -> Quote:
        """获取实时行情"""
        # 实际实现需要调用 Yahoo Finance API
        return Quote(
            symbol=symbol,
            price=100.0,
            change=2.5,
            change_percent=2.56,
            high=102.0,
            low=98.0,
            volume=1000000,
            timestamp=datetime.now(),
            market="US",
        )

    def get_ohlcv(self, symbol: str, period: str = "1d", limit: int = 100) -> List[OHLCV]:
        """获取K线数据"""
        return []

    def get_technical_indicators(self, symbol: str) -> TechnicalIndicator:
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(),
            ma20=98.0,
            ma50=95.0,
            ma200=90.0,
            rsi=65.0,
            atr=3.0,
            atr_percent=3.0,
        )

    def get_options_data(self, symbol: str) -> Optional[OptionData]:
        return OptionData(
            symbol=symbol,
            timestamp=datetime.now(),
            call_volume=100000,
            put_volume=80000,
            call_open_interest=500000,
            put_open_interest=400000,
            iv=0.25,
            iv_percentile=0.60,
        )


class CryptoDataSource(MarketDataSource):
    """Crypto 数据源 (示例实现)"""

    def __init__(self, exchange: str = "binance"):
        self.exchange = exchange

    def get_quote(self, symbol: str) -> Quote:
        return Quote(
            symbol=symbol,
            price=3000.0,
            change=50.0,
            change_percent=1.69,
            high=3050.0,
            low=2950.0,
            volume=1000000,
            timestamp=datetime.now(),
            market="CRYPTO",
        )

    def get_ohlcv(self, symbol: str, period: str = "1d", limit: int = 100) -> List[OHLCV]:
        return []

    def get_technical_indicators(self, symbol: str) -> TechnicalIndicator:
        return TechnicalIndicator(
            symbol=symbol,
            timestamp=datetime.now(),
            ma20=2950.0,
            ma50=2900.0,
            ma200=2800.0,
            rsi=55.0,
            atr=80.0,
            atr_percent=2.67,
        )

    def get_options_data(self, symbol: str) -> Optional[OptionData]:
        return None


class MarketDataManager:
    """行情数据管理器"""

    def __init__(self):
        self.sources: Dict[str, MarketDataSource] = {}
        self._init_default_sources()

    def _init_default_sources(self):
        """初始化默认数据源"""
        self.sources["yahoo"] = YahooQuoteSource()
        self.sources["crypto"] = CryptoDataSource()

    def register_source(self, name: str, source: MarketDataSource):
        """注册数据源"""
        self.sources[name] = source

    def get_source(self, name: str) -> Optional[MarketDataSource]:
        """获取数据源"""
        return self.sources.get(name)

    def get_quote(self, symbol: str, source: str = "yahoo") -> Optional[Quote]:
        """获取行情"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_quote(symbol)
        return None

    def get_ohlcv(self, symbol: str, period: str = "1d", limit: int = 100, source: str = "yahoo") -> List[OHLCV]:
        """获取K线数据"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_ohlcv(symbol, period, limit)
        return []

    def get_technical_indicators(self, symbol: str, source: str = "yahoo") -> Optional[TechnicalIndicator]:
        """获取技术指标"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_technical_indicators(symbol)
        return None

    def get_options_data(self, symbol: str, source: str = "yahoo") -> Optional[OptionData]:
        """获取期权数据"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_options_data(symbol)
        return None


# 全局实例
market_data_manager = MarketDataManager()


def main():
    """示例用法"""
    # 获取行情
    quote = market_data_manager.get_quote("NVDA")
    if quote:
        print(f"{quote.symbol}: ${quote.price} ({quote.change_percent:+.2f}%)")

    # 获取技术指标
    indicators = market_data_manager.get_technical_indicators("NVDA")
    if indicators:
        print(f"MA20: ${indicators.ma20}")
        print(f"RSI: {indicators.rsi}")


if __name__ == "__main__":
    main()
