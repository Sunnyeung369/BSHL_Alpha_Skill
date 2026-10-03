"""
BSHL Alpha Skill - Fundamental Data Interface

基本面数据接口抽象层，支持财报数据、公司基本面等。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date
from .contracts import (DataProvenance, DataUnavailableError, MOCK_TIME, mock_metadata,
                        validate_symbol)
import json


@dataclass
class CompanyInfo(DataProvenance):
    """公司基本信息"""
    symbol: str
    name: str
    exchange: str
    sector: str
    industry: str
    market_cap: float
    shares_outstanding: float
    float_shares: float
    description: str


@dataclass
class Financials(DataProvenance):
    """财务数据"""
    symbol: str
    period: str  # Q1, Q2, Q3, Q4, FY
    fiscal_year: int
    report_date: date

    # 损益表
    revenue: float
    cost_of_revenue: float
    gross_profit: float
    gross_margin: float
    operating_income: float
    net_income: float
    eps: float
    eps_diluted: float

    # 资产负债表
    total_assets: float
    total_liabilities: float
    shareholders_equity: float
    cash_and_equivalents: float
    long_term_debt: float

    # 现金流
    operating_cash_flow: float
    capex: float
    free_cash_flow: float


@dataclass
class Guidance(DataProvenance):
    """公司指引"""
    symbol: str
    period: str
    fiscal_year: int

    revenue_guidance_low: Optional[float]
    revenue_guidance_high: Optional[float]
    eps_guidance_low: Optional[float]
    eps_guidance_high: Optional[float]

    guidance_date: date


@dataclass
class EarningsCall(DataProvenance):
    """财报电话会议"""
    symbol: str
    fiscal_year: int
    period: str
    call_date: date
    call_time: str
    webcast_url: Optional[str]
    transcript_available: bool


class FundamentalDataSource(ABC):
    """基本面数据源抽象类"""

    @abstractmethod
    def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        """获取公司基本信息"""
        pass

    @abstractmethod
    def get_financials(self, symbol: str, period: str, fiscal_year: int) -> Optional[Financials]:
        """获取财务数据"""
        pass

    @abstractmethod
    def get_latest_financials(self, symbol: str) -> Optional[Financials]:
        """获取最新财务数据"""
        pass

    @abstractmethod
    def get_guidance(self, symbol: str) -> Optional[Guidance]:
        """获取公司指引"""
        pass

    @abstractmethod
    def get_earnings_call(self, symbol: str) -> Optional[EarningsCall]:
        """获取财报会议信息"""
        pass

    @abstractmethod
    def get_earnings_transcript(self, symbol: str, fiscal_year: int, period: str) -> Optional[str]:
        """获取财报会议记录"""
        pass


class UnavailableFundamentalSource(FundamentalDataSource):
    provider_name = "unconfigured"

    def _unavailable(self, symbol, operation):
        validate_symbol(symbol)
        raise DataUnavailableError(f"{self.provider_name}: {operation} is not connected")

    def get_company_info(self, symbol):
        return self._unavailable(symbol, "company information")

    def get_financials(self, symbol, period, fiscal_year):
        return self._unavailable(symbol, "financials")

    def get_latest_financials(self, symbol):
        return self._unavailable(symbol, "latest financials")

    def get_guidance(self, symbol):
        return self._unavailable(symbol, "guidance")

    def get_earnings_call(self, symbol):
        return self._unavailable(symbol, "earnings call")

    def get_earnings_transcript(self, symbol, fiscal_year, period):
        return self._unavailable(symbol, "earnings transcript")


class YahooFinanceSource(UnavailableFundamentalSource):
    provider_name = "yahoo"


class SECSource(UnavailableFundamentalSource):
    provider_name = "sec"


class MockFundamentalSource(FundamentalDataSource):
    """Synthetic company facts preserving requested symbol identity."""

    def __init__(self, *, enabled=False):
        if enabled is not True:
            raise DataUnavailableError("MockFundamentalSource requires enabled=True")

    def get_company_info(self, symbol):
        symbol = validate_symbol(symbol)
        return CompanyInfo(symbol, f"[MOCK] {symbol} Synthetic Company", "MOCK", "Synthetic",
                           "Synthetic", 1000000.0, 10000.0, 8000.0,
                           "Synthetic fixture; not facts about a real company.",
                           **mock_metadata("company"))

    def get_financials(self, symbol, period, fiscal_year):
        symbol = validate_symbol(symbol)
        if period not in {"Q1", "Q2", "Q3", "Q4", "FY"}:
            raise ValueError("period must be Q1/Q2/Q3/Q4/FY")
        if isinstance(fiscal_year, bool) or not isinstance(fiscal_year, int) or not 1900 <= fiscal_year <= 2100:
            raise ValueError("fiscal_year must be between 1900 and 2100")
        return Financials(symbol, period, fiscal_year, date(fiscal_year, 12, 31),
                          1000.0, 400.0, 600.0, 0.6, 300.0, 200.0, 2.0, 2.0,
                          5000.0, 2000.0, 3000.0, 1000.0, 500.0, 250.0, 50.0, 200.0,
                          **mock_metadata("financials"))

    def get_latest_financials(self, symbol):
        return self.get_financials(symbol, "FY", 2019)

    def get_guidance(self, symbol):
        symbol = validate_symbol(symbol)
        return Guidance(symbol, "FY", 2020, 1000.0, 1100.0, 2.0, 2.2,
                        MOCK_TIME.date(), **mock_metadata("guidance"))

    def get_earnings_call(self, symbol):
        symbol = validate_symbol(symbol)
        return EarningsCall(symbol, 2019, "FY", MOCK_TIME.date(), "00:00 UTC",
                            "https://example.invalid/bshl/mock/earnings", False,
                            **mock_metadata("earnings"))

    def get_earnings_transcript(self, symbol, fiscal_year, period):
        validate_symbol(symbol)
        raise DataUnavailableError("no mock or real earnings transcript is provided")


class FundamentalDataManager:
    def __init__(self, *, enable_mock=False):
        if not isinstance(enable_mock, bool):
            raise ValueError("enable_mock must be an explicit boolean")
        self.sources = {"yahoo": YahooFinanceSource(), "sec": SECSource()}
        if enable_mock:
            self.sources["mock"] = MockFundamentalSource(enabled=True)

    def register_source(self, name, source):
        if not name or not isinstance(source, FundamentalDataSource):
            raise ValueError("register a named FundamentalDataSource")
        self.sources[name] = source

    def get_source(self, name):
        if name not in self.sources:
            raise DataUnavailableError(f"fundamental provider {name!r} is not registered")
        return self.sources[name]

    def get_company_info(self, symbol, source="yahoo"):
        return self.get_source(source).get_company_info(symbol)

    def get_financials(self, symbol, period, fiscal_year, source="yahoo"):
        return self.get_source(source).get_financials(symbol, period, fiscal_year)

    def get_latest_financials(self, symbol, source="yahoo"):
        return self.get_source(source).get_latest_financials(symbol)

    def get_guidance(self, symbol, source="yahoo"):
        return self.get_source(source).get_guidance(symbol)

    def get_earnings_call(self, symbol, source="yahoo"):
        return self.get_source(source).get_earnings_call(symbol)

    def get_earnings_transcript(self, symbol, fiscal_year, period, source="yahoo"):
        return self.get_source(source).get_earnings_transcript(symbol, fiscal_year, period)


fundamental_data_manager = FundamentalDataManager()


def main():
    info = FundamentalDataManager(enable_mock=True).get_company_info("DEMO", source="mock")
    print(f"[MOCK] {info.name}; source={info.source}; as_of={info.retrieved_at.isoformat()}")


if __name__ == "__main__":
    main()
