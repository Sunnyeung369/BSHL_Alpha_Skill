"""Strict, point-in-time daily OHLCV snapshots using the Python standard library.

The provider supplies the session calendar. A list of weekdays is not an
exchange calendar. ``timestamp`` is the close time, ``available_at`` is when
the complete record became available to this research workflow.
"""

import csv
from dataclasses import dataclass, replace
from datetime import date, datetime, timezone
import json
import math
from pathlib import Path
from urllib.parse import urlparse
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from data.contracts import validate_symbol


CSV_COLUMNS = ("timestamp", "open", "high", "low", "close", "volume", "available_at", "is_closed")


def parse_timestamp(value: str | datetime) -> datetime:
    """Require an explicit UTC offset; normalize aware timestamps to UTC."""
    if isinstance(value, str):
        if not value or value.strip() != value:
            raise ValueError("timestamp must be a nonempty ISO datetime without surrounding whitespace")
        try:
            value = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("timestamp must be an ISO datetime with an explicit UTC offset") from exc
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("timestamp must include an explicit UTC offset")
    return value.astimezone(timezone.utc)


def timezone_from_name(name: str):
    if name in {"UTC", "Etc/UTC"}:
        return timezone.utc
    if not isinstance(name, str) or not name.strip():
        raise ValueError("timezone must be UTC or an IANA timezone name")
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ValueError(f"timezone {name!r} is unavailable; provide a valid IANA timezone database") from exc


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    available_at: datetime
    is_closed: bool = True
    session_open: datetime | None = None


@dataclass(frozen=True, kw_only=True)
class Dataset:
    symbol: str
    market: str = "US"
    timeframe: str = "1d"
    currency: str = "USD"
    timezone: str = "UTC"
    adjustment: str = "unadjusted"
    source_url: str = ""
    data_mode: str = "csv"
    is_mock: bool = False
    bars: tuple[Bar, ...] = ()
    asset_type: str = "US_STOCK"
    retrieved_at: datetime | None = None
    session_dates: tuple[date, ...] = ()


def _finite(value, name, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if value <= 0 if positive else value < 0:
        raise ValueError(f"{name} must be {'positive' if positive else 'nonnegative'}")


def validate_dataset(dataset: Dataset) -> None:
    """Validate the complete supplied snapshot without silently sorting or filling gaps."""
    if not isinstance(dataset, Dataset):
        raise ValueError("dataset must be a Dataset")
    validate_symbol(dataset.symbol)
    if dataset.market not in {"US", "HK", "CN", "CRYPTO"}:
        raise ValueError("unsupported market")
    if dataset.timeframe != "1d":
        raise ValueError("this research release supports daily bars only")
    if dataset.asset_type not in {"US_STOCK", "HK_STOCK", "CN_STOCK", "ETF", "CRYPTO", "TOKEN"}:
        raise ValueError("unsupported asset_type")
    if dataset.adjustment not in {"unadjusted", "split_adjusted", "total_return"}:
        raise ValueError("adjustment must be unadjusted/split_adjusted/total_return")
    if dataset.data_mode not in {"csv", "live", "mock"} or not isinstance(dataset.is_mock, bool):
        raise ValueError("data_mode/is_mock must be explicit valid values")
    if dataset.data_mode == "mock" and not dataset.is_mock:
        raise ValueError("mock data_mode requires is_mock=true")
    if not isinstance(dataset.currency, str) or len(dataset.currency) != 3 or not dataset.currency.isupper() or not dataset.currency.isalpha():
        raise ValueError("currency must be a three-letter uppercase code")
    zone = timezone_from_name(dataset.timezone)
    parsed_url = urlparse(dataset.source_url)
    if parsed_url.scheme not in {"https", "http"} or not parsed_url.netloc or any(ch.isspace() for ch in dataset.source_url):
        raise ValueError("source_url must be an HTTP(S) provenance URL")
    if dataset.retrieved_at is None:
        raise ValueError("retrieved_at is required")
    parse_timestamp(dataset.retrieved_at)
    if not isinstance(dataset.bars, tuple) or not isinstance(dataset.session_dates, tuple):
        raise ValueError("bars and session_dates must be immutable tuples")
    previous_session = None
    for session in dataset.session_dates:
        if not isinstance(session, date) or isinstance(session, datetime):
            raise ValueError("session_dates must contain date objects")
        if previous_session is not None and session <= previous_session:
            raise ValueError("session_dates must be strictly increasing and unique")
        previous_session = session
    previous_time = None
    seen_dates = set()
    declared_sessions = set(dataset.session_dates)
    for bar in dataset.bars:
        if not isinstance(bar, Bar):
            raise ValueError("bars must contain Bar objects")
        stamp, available = parse_timestamp(bar.timestamp), parse_timestamp(bar.available_at)
        if available < stamp:
            raise ValueError("available_at cannot precede the bar close timestamp")
        if bar.session_open is not None:
            session_open = parse_timestamp(bar.session_open)
            if session_open >= stamp or session_open.astimezone(zone).date() != stamp.astimezone(zone).date():
                raise ValueError("session_open must precede close on the same declared local session date")
        if previous_time is not None and stamp <= previous_time:
            raise ValueError("bars must be strictly increasing; duplicates and silent sorting are forbidden")
        previous_time = stamp
        session = stamp.astimezone(zone).date()
        if session in seen_dates:
            raise ValueError("daily bars cannot repeat a local session date")
        seen_dates.add(session)
        if declared_sessions and session not in declared_sessions:
            raise ValueError("a daily bar date is absent from the declared session calendar")
        if not isinstance(bar.is_closed, bool):
            raise ValueError("is_closed must be a boolean")
        for name in ("open", "high", "low", "close"):
            _finite(getattr(bar, name), name, positive=True)
        _finite(bar.volume, "volume")
        if bar.high < max(bar.open, bar.close, bar.low) or bar.low > min(bar.open, bar.close, bar.high):
            raise ValueError("OHLC prices violate high/low bounds")


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate metadata field: {key}")
        result[key] = value
    return result


def load_dataset(csv_path, metadata_path) -> Dataset:
    """Load an explicit CSV snapshot; do not infer facts or connection modes."""
    metadata = json.loads(Path(metadata_path).read_text(encoding="utf-8-sig"), object_pairs_hook=_unique_object,
                          parse_constant=lambda value: (_ for _ in ()).throw(ValueError(f"nonfinite JSON value: {value}")))
    if not isinstance(metadata, dict):
        raise ValueError("metadata must be a JSON object")
    required = {"symbol", "market", "timeframe", "currency", "timezone", "adjustment", "source_url",
                "data_mode", "is_mock", "asset_type", "retrieved_at"}
    if required - metadata.keys():
        raise ValueError(f"missing metadata fields: {', '.join(sorted(required - metadata.keys()))}")
    allowed = required | {"session_dates", "session_open_times", "schema_version"}
    if metadata.keys() - allowed:
        raise ValueError(f"unknown metadata fields: {', '.join(sorted(metadata.keys() - allowed))}")
    if metadata["data_mode"] not in {"csv", "mock"}:
        raise ValueError("CSV loading requires csv/mock mode; it cannot claim a live connection")
    if "schema_version" in metadata and metadata["schema_version"] != "0.6":
        raise ValueError("unsupported metadata schema_version")
    session_dates = metadata.pop("session_dates", [])
    if not isinstance(session_dates, list):
        raise ValueError("session_dates must be a list of ISO calendar dates")
    parsed_sessions = []
    for value in session_dates:
        if not isinstance(value, str) or len(value) != 10:
            raise ValueError("session_dates must contain YYYY-MM-DD dates")
        parsed_sessions.append(date.fromisoformat(value))
    metadata.pop("schema_version", None)
    session_open_times = metadata.pop("session_open_times", {})
    if not isinstance(session_open_times, dict):
        raise ValueError("session_open_times must map ISO session dates to aware open timestamps")
    declared_zone = timezone_from_name(metadata["timezone"])
    declared_sessions = set(parsed_sessions)
    for session_day, open_time in session_open_times.items():
        if not isinstance(session_day, str) or len(session_day) != 10:
            raise ValueError("session_open_times keys must be YYYY-MM-DD dates")
        session = date.fromisoformat(session_day)
        opening = parse_timestamp(open_time)
        if session not in declared_sessions or opening.astimezone(declared_zone).date() != session:
            raise ValueError("session_open_times must match the declared calendar and timezone")
        session_open_times[session_day] = opening
    metadata["retrieved_at"] = parse_timestamp(metadata["retrieved_at"])
    bars = []
    with Path(csv_path).open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames not in (list(CSV_COLUMNS), list(CSV_COLUMNS) + ["session_open"]):
            raise ValueError(f"CSV headers must be {','.join(CSV_COLUMNS)} with optional final session_open")
        for row_number, row in enumerate(reader, 2):
            try:
                if None in row or any(value is None or not value for value in row.values()):
                    raise ValueError("missing or extra CSV values")
                if row["is_closed"] not in {"true", "false"}:
                    raise ValueError("is_closed must be the literal true/false")
                stamp = parse_timestamp(row["timestamp"])
                calendar_open = session_open_times.get(stamp.astimezone(declared_zone).date().isoformat())
                row_open = parse_timestamp(row["session_open"]) if "session_open" in row else None
                if row_open is not None and calendar_open is not None and row_open != calendar_open:
                    raise ValueError("CSV session_open conflicts with metadata session_open_times")
                bars.append(Bar(stamp,
                                *(float(row[name]) for name in ("open", "high", "low", "close", "volume")),
                                parse_timestamp(row["available_at"]), row["is_closed"] == "true",
                                row_open or calendar_open))
            except (TypeError, ValueError) as exc:
                raise ValueError(f"CSV row {row_number}: {exc}") from exc
    dataset = Dataset(**metadata, bars=tuple(bars), session_dates=tuple(parsed_sessions))
    validate_dataset(dataset)
    return dataset


def as_of_slice(dataset: Dataset, as_of: datetime) -> Dataset:
    """Only bars both closed in time and available in time enter this snapshot.

    Provisional bars remain visible diagnostics when is_closed=False; structural
    confirmation explicitly excludes them. Calendar dates remain declared dates.
    """
    validate_dataset(dataset)
    cutoff = parse_timestamp(as_of)
    return replace(dataset, bars=tuple(bar for bar in dataset.bars
                                      if parse_timestamp(bar.timestamp) <= cutoff
                                      and parse_timestamp(bar.available_at) <= cutoff))
