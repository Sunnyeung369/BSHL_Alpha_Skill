"""Generate transparent synthetic candles. Never a real market dataset."""
import csv
from datetime import date, datetime, time, timedelta, timezone
import json
from math import sin
from pathlib import Path
from zoneinfo import ZoneInfo

root = Path(__file__).resolve().parents[1]
assets = root / "bshl/assets"
assets.mkdir(parents=True, exist_ok=True)
sessions = []
day = date(2025, 1, 6)
while len(sessions) < 100:
    if day.weekday() < 5:
        sessions.append(day)
    day += timedelta(days=1)
for scenario in ("breakout", "overheated"):
    rows = []
    previous = 100.0
    for index, day in enumerate(sessions):
        close = round(100 + index * .25 + sin(index / 4) * .3, 4)
        if 88 <= index < 99:
            close = [120.5, 121, 124, 123, 122, 121.5, 122, 122.5, 123, 123.5, 124][index - 88]
        if index == 99:
            close = 126 if scenario == "breakout" else 155
        opening = round(previous + .1, 4)
        stamp = datetime.combine(day, time(16), ZoneInfo("America/New_York")).astimezone(timezone.utc)
        session_open = datetime.combine(day, time(9, 30), ZoneInfo("America/New_York")).astimezone(timezone.utc)
        rows.append({"timestamp": stamp.isoformat(), "open": opening,
            "high": round(max(opening, close) + .8, 4),
            "low": round(min(opening, close) - .8, 4), "close": close,
            "volume": 3000000 if index == 99 else 1000000,
            "available_at": stamp.isoformat(), "is_closed": "true", "session_open": session_open.isoformat()})
        previous = close
    # A strict local maximum/minimum, confirmed by subsequent daily bars.
    rows[90]["high"] = 125.0
    rows[93]["low"] = 120.0
    with (assets / (scenario + ".csv")).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    meta = {"symbol": "DEMO", "market": "US", "timeframe": "1d", "currency": "USD",
        "timezone": "America/New_York", "adjustment": "unadjusted",
        "source_url": "https://example.invalid/bshl/synthetic-candles", "data_mode": "mock",
        "is_mock": True, "asset_type": "ETF", "retrieved_at": rows[-1]["available_at"],
        "session_dates": [day.isoformat() for day in sessions]}
    (assets / (scenario + ".metadata.json")).write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
context = {
    "alpha_scores": dict(demand_inflection=15, supply_chain_bottleneck=15,
        company_benefit_certainty=15, evidence_quality=15, catalyst_timing=10,
        valuation_mismatch=10, competition=10, contradiction_clarity=10),
    "pricing_scores": dict(sector_trend=15, relative_strength=15, capital_inflow=15,
        crowding=15, valuation_digestion=15, risk_appetite=15, catalyst_priced=10),
    "risk_checks": {name: True for name in ("liquidity", "volatility", "evidence_quality",
        "social_crowding", "earnings_risk", "regulatory_uncertainty", "price_location",
        "stop_loss_distance", "position_exposure", "correlation")},
    "stop_loss_price": 121.0, "target_price": 145.0,
    "evidence": [{"id": "SYNTHETIC-001", "claim": "Fictional fixture for exercising the pipeline, not an investment thesis",
        "source_type": "company_release", "source_url": "https://example.invalid/bshl/fixture",
        "published_at": "2025-01-01T00:00:00+00:00", "available_at": "2025-01-01T00:00:00+00:00",
        "evidence_strength": "strong", "supports_or_refutes": "supports", "kill_switch": False}],
}
(assets / "demo.context.json").write_text(json.dumps(context, indent=2) + "\n", encoding="utf-8")
print("Synthetic fixtures generated; weekday calendar is fictional, not verified NYSE sessions")

