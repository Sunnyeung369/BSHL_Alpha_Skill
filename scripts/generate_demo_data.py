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
for scenario in ("breakout", "overheated", "pullback", "breakdown"):
    rows = []
    previous = 100.0
    for index, day in enumerate(sessions):
        close = round(100 + index * .25 + sin(index / 4) * .3, 4)
        if 88 <= index < 99:
            close = [120.5, 121, 124, 123, 122, 121.5, 122, 122.5, 123, 123.5, 124][index - 88]
        if index == 99:
            if scenario == "breakout":
                close = 126
            elif scenario == "overheated":
                close = 155
            elif scenario == "pullback":
                # Green candle closing at prior resistance; rebound after
                # the breakout that occurred at index 96 (within lookback=5).
                close = 125.5
            elif scenario == "breakdown":
                # Close below the confirmed pivot low at 120.
                close = 119
        opening = round(previous + .1, 4)
        # For the pullback scenario the last bar must be a green candle
        # (close > open) to satisfy the pullback_confirmed rule.
        if scenario == "pullback" and index == 99:
            opening = 124.5
        # For the breakdown scenario the last bar opens near the support and
        # closes below it.
        if scenario == "breakdown" and index == 99:
            opening = 119.5
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
    # For pullback: need a breakout bar earlier in the lookback window.
    # Bar 96 already closes at 122.5 which is below resistance (125).
    # We need at least one bar in [95..98] that broke above resistance
    # and the previous bar was below it.  Use bar 96 as the breakout bar.
    if scenario == "pullback":
        rows[95]["close"] = 124.9   # bar before breakout: below resistance
        rows[95]["high"] = max(rows[95]["high"], 125.7)
        rows[96]["close"] = 125.2   # breakout bar: closes above resistance * 1.001
        rows[96]["high"] = max(rows[96]["high"], 126.0)
        rows[96]["open"] = 124.8
        rows[96]["low"] = min(rows[96]["low"], 124.0)
        # Bars 97-98 pull back toward resistance to set up the rebound.
        rows[97]["close"] = 125.0
        rows[97]["open"] = 125.3
        rows[97]["high"] = max(rows[97]["high"], 126.0)
        rows[97]["low"] = min(rows[97]["low"], 124.8)
        rows[98]["close"] = 125.1
        rows[98]["open"] = 125.0
        rows[98]["high"] = max(rows[98]["high"], 125.9)
        rows[98]["low"] = min(rows[98]["low"], 124.5)
    with (assets / (scenario + ".csv")).open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    meta = {"symbol": "DEMO", "market": "US", "timeframe": "1d", "currency": "USD",
        "timezone": "America/New_York", "adjustment": "unadjusted",
        "source_url": "https://example.invalid/bshl/synthetic-candles", "data_mode": "mock",
        "is_mock": True, "asset_type": "ETF", "exchange": "SYNTHETIC-US", "retrieved_at": rows[-1]["available_at"],
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

