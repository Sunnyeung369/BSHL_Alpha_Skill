"""Shared provider errors and explicit data provenance.

An unavailable adapter is an error, not an empty dataset or fabricated quote.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re


class DataUnavailableError(RuntimeError):
    """A provider has no verified data for the requested operation."""


def validate_symbol(symbol: str) -> str:
    """Validate syntax; this does not assert that a security exists."""
    if not isinstance(symbol, str) or not re.fullmatch(r"[A-Za-z0-9^][A-Za-z0-9.^/_-]{0,39}", symbol):
        raise ValueError("symbol must be a nonempty ticker with no whitespace")
    return symbol.upper()


def validate_limit(limit: int) -> None:
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 10000:
        raise ValueError("limit must be an integer between 1 and 10000")


@dataclass(kw_only=True)
class DataProvenance:
    """Metadata included by dataclass serialization for every returned record."""

    source: str = "unverified"
    source_url: str = ""
    is_mock: bool = False
    data_mode: str = "unavailable"
    retrieved_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


MOCK_TIME = datetime(2020, 1, 1, tzinfo=timezone.utc)


def mock_metadata(kind: str) -> dict:
    return {
        "source": "mock",
        "source_url": f"https://example.invalid/bshl/mock/{kind}",
        "is_mock": True,
        "data_mode": "mock",
        "retrieved_at": MOCK_TIME,
    }
