"""
BSHL Alpha Skill - Fundamental Data Interface

基本面数据接口抽象层，支持财报数据、公司基本面等。
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, date
import json


@dataclass
class CompanyInfo:
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
class Financials:
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
class Guidance:
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
class EarningsCall:
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


class YahooFinanceSource(FundamentalDataSource):
    """Yahoo Finance 基本面数据源 (示例实现)"""

    def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        return CompanyInfo(
            symbol=symbol,
            name="NVIDIA Corporation",
            exchange="NASDAQ",
            sector="Technology",
            industry="Semiconductors",
            market_cap=2500000000000,
            shares_outstanding=2500000000,
            float_shares=2000000000,
            description="NVIDIA Corporation designs and manufactures graphics processors.",
        )

    def get_financials(self, symbol: str, period: str, fiscal_year: int) -> Optional[Financials]:
        return Financials(
            symbol=symbol,
            period=period,
            fiscal_year=fiscal_year,
            report_date=date(2025, 5, 28),
            revenue=26000000000,
            cost_of_revenue=12000000000,
            gross_profit=14000000000,
            gross_margin=0.538,
            operating_income=15000000000,
            net_income=14000000000,
            eps=5.60,
            eps_diluted=5.50,
            total_assets=60000000000,
            total_liabilities=20000000000,
            shareholders_equity=40000000000,
            cash_and_equivalents=10000000000,
            long_term_debt=5000000000,
            operating_cash_flow=16000000000,
            capex=2000000000,
            free_cash_flow=14000000000,
        )

    def get_latest_financials(self, symbol: str) -> Optional[Financials]:
        return self.get_financials(symbol, "Q1", 2025)

    def get_guidance(self, symbol: str) -> Optional[Guidance]:
        return Guidance(
            symbol=symbol,
            period="Q2",
            fiscal_year=2025,
            revenue_guidance_low=28000000000,
            revenue_guidance_high=30000000000,
            eps_guidance_low=0.28,
            eps_guidance_high=0.30,
            guidance_date=date(2025, 5, 28),
        )

    def get_earnings_call(self, symbol: str) -> Optional[EarningsCall]:
        return EarningsCall(
            symbol=symbol,
            fiscal_year=2025,
            period="Q2",
            call_date=date(2025, 8, 15),
            call_time="17:00 ET",
            webcast_url="https://example.com/webcast",
            transcript_available=True,
        )

    def get_earnings_transcript(self, symbol: str, fiscal_year: int, period: str) -> Optional[str]:
        # 实际实现需要从 API 获取
        return "示例财报会议记录..."


class SECSource(FundamentalDataSource):
    """SEC 数据源 (示例实现)"""

    def get_company_info(self, symbol: str) -> Optional[CompanyInfo]:
        # SEC 数据通常不包含公司基本信息
        return None

    def get_financials(self, symbol: str, period: str, fiscal_year: int) -> Optional[Financials]:
        # 实际实现需要从 SEC EDGAR 获取 10-K/10-Q
        return None

    def get_latest_financials(self, symbol: str) -> Optional[Financials]:
        return None

    def get_guidance(self, symbol: str) -> Optional[Guidance]:
        # 指引通常不在 SEC 文件中
        return None

    def get_earnings_call(self, symbol: str) -> Optional[EarningsCall]:
        return None

    def get_earnings_transcript(self, symbol: str, fiscal_year: int, period: str) -> Optional[str]:
        return None


class FundamentalDataManager:
    """基本面数据管理器"""

    def __init__(self):
        self.sources: Dict[str, FundamentalDataSource] = {}
        self._init_default_sources()

    def _init_default_sources(self):
        """初始化默认数据源"""
        self.sources["yahoo"] = YahooFinanceSource()
        self.sources["sec"] = SECSource()

    def register_source(self, name: str, source: FundamentalDataSource):
        """注册数据源"""
        self.sources[name] = source

    def get_source(self, name: str) -> Optional[FundamentalDataSource]:
        """获取数据源"""
        return self.sources.get(name)

    def get_company_info(self, symbol: str, source: str = "yahoo") -> Optional[CompanyInfo]:
        """获取公司基本信息"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_company_info(symbol)
        return None

    def get_financials(self, symbol: str, period: str, fiscal_year: int, source: str = "yahoo") -> Optional[Financials]:
        """获取财务数据"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_financials(symbol, period, fiscal_year)
        return None

    def get_latest_financials(self, symbol: str, source: str = "yahoo") -> Optional[Financials]:
        """获取最新财务数据"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_latest_financials(symbol)
        return None

    def get_guidance(self, symbol: str, source: str = "yahoo") -> Optional[Guidance]:
        """获取公司指引"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_guidance(symbol)
        return None

    def get_earnings_call(self, symbol: str, source: str = "yahoo") -> Optional[EarningsCall]:
        """获取财报会议信息"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_earnings_call(symbol)
        return None

    def get_earnings_transcript(self, symbol: str, fiscal_year: int, period: str, source: str = "yahoo") -> Optional[str]:
        """获取财报会议记录"""
        source_obj = self.get_source(source)
        if source_obj:
            return source_obj.get_earnings_transcript(symbol, fiscal_year, period)
        return None


# 全局实例
fundamental_data_manager = FundamentalDataManager()


def main():
    """示例用法"""
    # 获取公司信息
    info = fundamental_data_manager.get_company_info("NVDA")
    if info:
        print(f"{info.symbol} - {info.name}")
        print(f"Sector: {info.sector}")
        print(f"Market Cap: ${info.market_cap/1e9:.1f}B")

    # 获取最新财报
    financials = fundamental_data_manager.get_latest_financials("NVDA")
    if financials:
        print(f"\nRevenue: ${financials.revenue/1e9:.1f}B")
        print(f"Gross Margin: {financials.gross_margin*100:.1f}%")
        print(f"EPS: ${financials.eps:.2f}")


if __name__ == "__main__":
    main()
