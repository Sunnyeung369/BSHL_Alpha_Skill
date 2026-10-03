"""
BSHL Alpha Skill - Market Data Interface

行情数据接口抽象层，支持多数据源。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from datetime import datetime, timedelta
from .contracts import (DataProvenance, DataUnavailableError, MOCK_TIME, mock_metadata,
                        validate_symbol, validate_limit)
import json


@dataclass
class Quote(DataProvenance):
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
class OHLCV(DataProvenance):
    """K线数据"""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class TechnicalIndicator(DataProvenance):
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
class OptionData(DataProvenance):
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


class UnavailableMarketSource(MarketDataSource):
    """Reserved adapter: no live connection has been implemented."""
    provider_name = "unconfigured"

    def _unavailable(self, symbol, operation):
        validate_symbol(symbol)
        raise DataUnavailableError(f"{self.provider_name}: {operation} is not connected; choose an explicit mock/CSV provider")

    def get_quote(self, symbol):
        return self._unavailable(symbol, "quote")

    def get_ohlcv(self, symbol, period="1d", limit=100):
        validate_limit(limit)
        return self._unavailable(symbol, "OHLCV")

    def get_technical_indicators(self, symbol):
        return self._unavailable(symbol, "technical indicators")

    def get_options_data(self, symbol):
        return self._unavailable(symbol, "options")


class AlphaQuoteSource(UnavailableMarketSource):
    provider_name = "alpha_vantage"

    def __init__(self, api_key=None):
        self.api_key = api_key


class YahooQuoteSource(UnavailableMarketSource):
    provider_name = "yahoo"


class CryptoDataSource(UnavailableMarketSource):
    provider_name = "crypto"

    def __init__(self, exchange="binance"):
        self.exchange = exchange


class MockMarketSource(MarketDataSource):
    """Deterministic synthetic data. Must be explicitly enabled and selected."""

    def __init__(self, *, enabled=False):
        if enabled is not True:
            raise DataUnavailableError("MockMarketSource requires enabled=True; synthetic data cannot be used as live data")

    def get_quote(self, symbol):
        symbol = validate_symbol(symbol)
        return Quote(symbol, 100.0, 1.0, 1.01, 102.0, 98.0, 1000000.0,
                     MOCK_TIME, "MOCK", **mock_metadata("quote"))

    def get_ohlcv(self, symbol, period="1d", limit=100):
        symbol = validate_symbol(symbol)
        validate_limit(limit)
        if period != "1d":
            raise DataUnavailableError("mock OHLCV supports only frozen daily bars")
        return [OHLCV(symbol, MOCK_TIME - timedelta(days=limit-i-1),
                      99.0, 102.0, 98.0, 100.0, 1000000.0,
                      **mock_metadata("ohlcv")) for i in range(limit)]

    def get_technical_indicators(self, symbol):
        symbol = validate_symbol(symbol)
        return TechnicalIndicator(symbol, MOCK_TIME, ma20=100.0, ma50=100.0,
                                  ma200=100.0, rsi=50.0, atr=4.0, atr_percent=4.0,
                                  **mock_metadata("indicators"))

    def get_options_data(self, symbol):
        symbol = validate_symbol(symbol)
        return OptionData(symbol, MOCK_TIME, 1000.0, 1000.0, 2000.0, 2000.0,
                          0.25, 0.50, **mock_metadata("options"))


class MarketDataManager:
    """No fallback from an unavailable provider to synthetic data."""

    def __init__(self, *, enable_mock=False):
        if not isinstance(enable_mock, bool):
            raise ValueError("enable_mock must be an explicit boolean")
        self.sources = {"yahoo": YahooQuoteSource(), "crypto": CryptoDataSource()}
        if enable_mock:
            self.sources["mock"] = MockMarketSource(enabled=True)

    def register_source(self, name, source):
        if not name or not isinstance(source, MarketDataSource):
            raise ValueError("register a named MarketDataSource")
        self.sources[name] = source

    def get_source(self, name):
        if name not in self.sources:
            raise DataUnavailableError(f"market provider {name!r} is not registered")
        return self.sources[name]

    def get_quote(self, symbol, source="yahoo"):
        return self.get_source(source).get_quote(symbol)

    def get_ohlcv(self, symbol, period="1d", limit=100, source="yahoo"):
        return self.get_source(source).get_ohlcv(symbol, period, limit)

    def get_technical_indicators(self, symbol, source="yahoo"):
        return self.get_source(source).get_technical_indicators(symbol)

    def get_options_data(self, symbol, source="yahoo"):
        return self.get_source(source).get_options_data(symbol)


market_data_manager = MarketDataManager()


def main():
    """Explicit synthetic demo; never a live quote."""
    quote = MarketDataManager(enable_mock=True).get_quote("DEMO", source="mock")
    print(f"[MOCK / {quote.timestamp.isoformat()}] {quote.symbol}: {quote.price}")


if __name__ == "__main__":
    main()
