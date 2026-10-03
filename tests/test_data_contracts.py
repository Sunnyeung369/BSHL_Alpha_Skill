"""Regression tests for unavailable providers, mock isolation and JSON contracts."""

import copy
from dataclasses import asdict
import json
from pathlib import Path
import unittest

from data import (
    DataUnavailableError, FundamentalDataManager, MarketDataManager,
    MockFundamentalSource, MockMarketSource, MockNewsSource, NewsDataManager,
)
from data.market_data import AlphaQuoteSource, CryptoDataSource, YahooQuoteSource
from data.fundamental_data import SECSource, YahooFinanceSource
from data.news_data import SeekingAlphaNews, YahooFinanceNews

try:
    import jsonschema
except ImportError:
    jsonschema = None

ROOT = Path(__file__).resolve().parents[1]


class ProviderContractTests(unittest.TestCase):
    def test_all_unconnected_market_operations_raise(self):
        for provider in (YahooQuoteSource(), CryptoDataSource(), AlphaQuoteSource("unused")):
            for method in ("get_quote", "get_ohlcv", "get_technical_indicators", "get_options_data"):
                with self.subTest(provider=type(provider).__name__, method=method):
                    with self.assertRaises(DataUnavailableError):
                        getattr(provider, method)("DOES-NOT-EXIST")

    def test_all_unconnected_fundamental_operations_raise(self):
        for provider in (YahooFinanceSource(), SECSource()):
            for method in ("get_company_info", "get_latest_financials", "get_guidance", "get_earnings_call"):
                with self.subTest(provider=type(provider).__name__, method=method):
                    with self.assertRaises(DataUnavailableError):
                        getattr(provider, method)("MSTR")
            with self.assertRaises(DataUnavailableError):
                provider.get_financials("MSTR", "Q1", 2026)
            with self.assertRaises(DataUnavailableError):
                provider.get_earnings_transcript("MSTR", 2026, "Q1")

    def test_all_unconnected_news_operations_raise(self):
        for provider in (YahooFinanceNews(), SeekingAlphaNews()):
            for method in ("get_news", "get_press_releases", "search_news"):
                with self.subTest(provider=type(provider).__name__, method=method):
                    with self.assertRaises(DataUnavailableError):
                        getattr(provider, method)("MSTR")

    def test_defaults_never_fallback_to_mock(self):
        for manager, method in ((MarketDataManager(enable_mock=True), "get_quote"),
                                (FundamentalDataManager(enable_mock=True), "get_company_info"),
                                (NewsDataManager(enable_mock=True), "get_news")):
            with self.assertRaises(DataUnavailableError):
                getattr(manager, method)("NVDA")
            with self.assertRaises(DataUnavailableError):
                getattr(manager, method)("NVDA", source="unknown")
        with self.assertRaises(DataUnavailableError):
            NewsDataManager(enable_mock=True).get_all_news("NVDA")

    def test_mock_requires_both_enablement_and_explicit_selection(self):
        for provider_type in (MockMarketSource, MockFundamentalSource, MockNewsSource):
            with self.assertRaises(DataUnavailableError):
                provider_type()
        with self.assertRaises(DataUnavailableError):
            MarketDataManager().get_quote("DEMO", source="mock")
        for manager_type in (MarketDataManager, FundamentalDataManager, NewsDataManager):
            with self.assertRaises(ValueError):
                manager_type(enable_mock="false")

    def test_mock_records_have_frozen_provenance_and_symbol_identity(self):
        market = MarketDataManager(enable_mock=True)
        fundamentals = FundamentalDataManager(enable_mock=True)
        news = NewsDataManager(enable_mock=True)
        records = [market.get_quote("MSTR", source="mock"),
                   market.get_ohlcv("MSTR", limit=2, source="mock")[0],
                   market.get_technical_indicators("MSTR", source="mock"),
                   market.get_options_data("MSTR", source="mock"),
                   fundamentals.get_company_info("MSTR", source="mock"),
                   fundamentals.get_latest_financials("MSTR", source="mock"),
                   fundamentals.get_guidance("MSTR", source="mock"),
                   fundamentals.get_earnings_call("MSTR", source="mock"),
                   news.get_news("MSTR", source="mock")[0],
                   news.get_press_releases("MSTR", source="mock")[0]]
        for record in records:
            with self.subTest(record=type(record).__name__):
                payload = asdict(record)
                self.assertEqual(payload["symbol"], "MSTR")
                self.assertTrue(payload["is_mock"])
                self.assertEqual(payload["data_mode"], "mock")
                self.assertEqual(payload["source"], "mock")
                self.assertEqual(payload["retrieved_at"].year, 2020)
                self.assertIn("example.invalid", payload["source_url"])
        self.assertIn("MSTR", records[4].name)
        self.assertNotIn("NVIDIA", records[4].name)
        self.assertIn("[MOCK]", records[8].title)

    def test_invalid_symbols_and_limits_are_rejected(self):
        provider = MockMarketSource(enabled=True)
        for symbol in ("", "  ", "bad ticker", None, 12):
            with self.assertRaises(ValueError):
                provider.get_quote(symbol)
        for limit in (0, -1, True, 2.5, 10001):
            with self.assertRaises(ValueError):
                provider.get_ohlcv("DEMO", limit=limit)


class SchemaStructureTests(unittest.TestCase):
    def test_json_schemas_parse_and_evidence_fields_are_required(self):
        for path in (ROOT / "schemas").glob("*.schema.json"):
            schema = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(schema["type"], "object")
        schema = self.schema("evidence_ledger")
        self.assertGreaterEqual(schema["properties"]["evidence"]["minItems"], 1)
        for field in ("source_url", "source_date", "freshness", "claim"):
            self.assertIn(field, schema["properties"]["evidence"]["items"]["required"])

    @staticmethod
    def schema(name):
        return json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))


@unittest.skipIf(jsonschema is None, "jsonschema is optional; install the validation extra for instance checks")
class SchemaInstanceTests(SchemaStructureTests):
    def validate(self, name, payload):
        schema = self.schema(name)
        jsonschema.Draft7Validator.check_schema(schema)
        jsonschema.Draft7Validator(schema, format_checker=jsonschema.FormatChecker()).validate(payload)

    def test_bare_trade_ready_and_pass_are_rejected(self):
        for name, field, value in (("trade_readiness", "overall_status", "Trade Ready"),
                                   ("trade_readiness", "final_status", "Trade Ready"),
                                   ("risk_governor", "decision", "Pass")):
            payload = {"ticker": "DEMO", "date": "2026-01-01", field: value}
            if field == "final_status":
                payload["overall_status"] = "Wait"
            with self.subTest(schema=name, field=field):
                with self.assertRaises(jsonschema.ValidationError):
                    self.validate(name, payload)

    def test_mock_cannot_be_trade_ready(self):
        payload = {"ticker": "DEMO", "date": "2026-01-01", "overall_status": "Trade Ready",
                   "current_price": 100, "closed_bar_confirmed": True, "stop_loss_defined": True,
                   "stop_loss": {"level": 95, "clear": True},
                   "reward_risk_ratio": {"ratio": 2, "target": 110},
                   "trade_readiness_score": {"total": 90}, "risk_decision": "Pass",
                   "data_mode": "csv", "is_mock": False, "data_validated": True}
        self.validate("trade_readiness", payload)
        for patch in ({"is_mock": True}, {"data_mode": "mock"}, {"closed_bar_confirmed": False},
                      {"stop_loss_defined": False}, {"risk_decision": "Veto"},
                      {"risk_decision": "Reduce Size"}, {"data_validated": False}):
            invalid = copy.deepcopy(payload)
            invalid.update(patch)
            with self.subTest(patch=patch):
                with self.assertRaises(jsonschema.ValidationError):
                    self.validate("trade_readiness", invalid)

    def test_pass_requires_every_check_and_no_trigger(self):
        checklist = {key: {"status": True, "detail": "verified"}
                     for key in self.schema("risk_governor")["properties"]["checklist"]["properties"]}
        payload = {"ticker": "DEMO", "date": "2026-01-01", "decision": "Pass", "checklist": checklist,
                   "triggered_conditions": [], "reasoning": ["all required checks verified"],
                   "data_mode": "csv", "is_mock": False, "source": "fixture.csv",
                   "as_of": "2026-01-01T00:00:00Z"}
        self.validate("risk_governor", payload)
        invalid = copy.deepcopy(payload)
        invalid["checklist"].pop("liquidity")
        with self.assertRaises(jsonschema.ValidationError):
            self.validate("risk_governor", invalid)
        invalid = copy.deepcopy(payload)
        invalid["checklist"]["liquidity"]["status"] = False
        with self.assertRaises(jsonschema.ValidationError):
            self.validate("risk_governor", invalid)

    def test_evidence_requires_real_calendar_date_and_http_url(self):
        evidence = {"id": "e1", "claim": "historical filing fact", "source_type": "filing",
                    "source_name": "SEC", "source_url": "https://www.sec.gov/Archives/example",
                    "source_date": "2025-01-01", "evidence_strength": "strong",
                    "supports_or_refutes": "supports", "freshness": "aging",
                    "confidence": 0.5, "kill_switch": False}
        payload = {"ticker": "DEMO", "date": "2026-01-01", "evidence": [evidence]}
        self.validate("evidence_ledger", payload)
        for patch in ({"source_date": "2025-99-99"}, {"source_url": ""},
                      {"source_url": "file:///private"}, {"claim": "  "}):
            invalid = copy.deepcopy(payload)
            invalid["evidence"][0].update(patch)
            with self.assertRaises(jsonschema.ValidationError):
                self.validate("evidence_ledger", invalid)


if __name__ == "__main__":
    unittest.main()
