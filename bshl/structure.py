"""Experimental deterministic daily structure rules; no return forecasts.

Thresholds are research parameters. A pivot becomes available only after its
right-hand confirmation bars. Parent-week direction uses completed declared
sessions, never an unfinished week or an invented exchange calendar.
"""

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
import math

from .market import Dataset, as_of_slice, parse_timestamp, timezone_from_name, validate_dataset


@dataclass(frozen=True)
class StructureConfig:
    atr_period: int = 14
    ma_fast: int = 20
    ma_slow: int = 50
    pivot_left: int = 2
    pivot_right: int = 2
    breakout_buffer_percent: float = 0.1
    breakout_volume_ratio: float = 1.3
    pullback_atr_tolerance: float = 0.5
    overheat_atr: float = 3.0
    stop_buffer_atr: float = 0.25
    breakout_lookback: int = 5
    minimum_parent_weeks: int = 2

    def __post_init__(self):
        for name in ("atr_period", "ma_fast", "ma_slow", "pivot_left", "pivot_right", "breakout_lookback", "minimum_parent_weeks"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{name} must be a positive integer")
        if self.minimum_parent_weeks < 2 or self.ma_slow < self.ma_fast:
            raise ValueError("require at least two parent weeks and ma_slow >= ma_fast")
        for name in ("breakout_buffer_percent", "breakout_volume_ratio", "pullback_atr_tolerance", "overheat_atr", "stop_buffer_atr"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite nonnegative number")


def moving_average(bars, period):
    return sum(bar.close for bar in bars[-period:]) / period if len(bars) >= period else None


def wilder_atr(bars, period=14):
    """Seed with the first N true ranges, then Wilder's 1/N smoothing."""
    if isinstance(period, bool) or not isinstance(period, int) or period < 1:
        raise ValueError("ATR period must be a positive integer")
    if len(bars) < period:
        return None
    ranges = [max(bar.high - bar.low,
                  abs(bar.high - bars[index - 1].close) if index else 0,
                  abs(bar.low - bars[index - 1].close) if index else 0)
              for index, bar in enumerate(bars)]
    atr = sum(ranges[:period]) / period
    for true_range in ranges[period:]:
        atr = ((period - 1) * atr + true_range) / period
    return atr


def confirmed_pivots(bars, left=2, right=2):
    """Strict extrema; equal highs/lows do not produce confirmed pivots."""
    highs, lows = [], []
    for index in range(left, len(bars) - right):
        neighbors = list(bars[index-left:index]) + list(bars[index+1:index+right+1])
        if all(bars[index].high > bar.high for bar in neighbors):
            highs.append((index, bars[index].high))
        if all(bars[index].low < bar.low for bar in neighbors):
            lows.append((index, bars[index].low))
    return highs, lows


def completed_weekly_bars(dataset, as_of):
    """Return completed parent-week close records from the supplied calendar.

    A calendar truncated within the current week cannot prove that week is
    complete. A later declared session or passage beyond Sunday supplies the
    week-boundary coverage. Every declared session of a week needs a closed bar.
    """
    if not dataset.session_dates:
        return []
    zone = timezone_from_name(dataset.timezone)
    local_day = parse_timestamp(as_of).astimezone(zone).date()
    by_date = {bar.timestamp.astimezone(zone).date(): bar for bar in dataset.bars if bar.is_closed}
    weeks = {}
    for session in dataset.session_dates:
        monday = session - timedelta(days=session.weekday())
        weeks.setdefault(monday, []).append(session)
    result = []
    last_calendar_day = dataset.session_dates[-1]
    for monday, sessions in sorted(weeks.items()):
        next_monday = monday + timedelta(days=7)
        coverage = last_calendar_day >= next_monday or local_day >= next_monday
        if coverage and all(session in by_date for session in sessions):
            records = [by_date[session] for session in sessions]
            if all(parse_timestamp(bar.available_at) <= parse_timestamp(as_of) for bar in records):
                result.append({"week": monday.isoformat(), "timestamp": records[-1].timestamp.isoformat(),
                               "close": records[-1].close, "sessions": len(records)})
    return result


def analyze_structure(dataset: Dataset, as_of: datetime | None = None, config=None) -> dict:
    validate_dataset(dataset)
    if config is None:
        config = StructureConfig()
    elif isinstance(config, dict):
        config = StructureConfig(**config)
    elif not isinstance(config, StructureConfig):
        raise ValueError("config must be a StructureConfig or mapping")
    if as_of is None:
        as_of = max((bar.available_at for bar in dataset.bars), default=dataset.retrieved_at)
    as_of = parse_timestamp(as_of)
    visible = as_of_slice(dataset, as_of)
    closed = [bar for bar in visible.bars if bar.is_closed]
    last = visible.bars[-1] if visible.bars else None
    closed_bar_confirmed = bool(last and last.is_closed)
    ma20, ma50 = moving_average(closed, config.ma_fast), moving_average(closed, config.ma_slow)
    atr = wilder_atr(closed, config.atr_period)
    weekly = completed_weekly_bars(visible, as_of)
    parent_confirmed = len(weekly) >= config.minimum_parent_weeks
    parent = "UNKNOWN"
    if parent_confirmed:
        parent = "UP" if weekly[-1]["close"] > weekly[-2]["close"] else "DOWN" if weekly[-1]["close"] < weekly[-2]["close"] else "CONSOLIDATION"
    highs, lows = confirmed_pivots(closed, config.pivot_left, config.pivot_right)
    resistance = highs[-1][1] if highs else None
    support = lows[-1][1] if lows else None
    history_ok = len(closed) >= max(config.ma_slow, config.atr_period + 1)
    price = last.close if last else None
    avg_volume = sum(bar.volume for bar in closed[-21:-1]) / 20 if len(closed) >= 21 else None
    volume_ratio = closed[-1].volume / avg_volume if avg_volume and closed else None
    distance = (price - ma20) / atr if price is not None and ma20 is not None and atr and atr > 0 else None
    overheated = bool(distance is not None and distance > config.overheat_atr)
    breakdown = bool(closed_bar_confirmed and support is not None and price < support)
    eligible = history_ok and parent_confirmed and parent == "UP" and closed_bar_confirmed
    breakout = bool(eligible and resistance is not None and len(closed) >= 2
                    and closed[-1].close > resistance * (1 + config.breakout_buffer_percent / 100)
                    and closed[-2].close <= resistance
                    and volume_ratio is not None and volume_ratio >= config.breakout_volume_ratio)
    recent_breakout = False
    if resistance is not None and highs:
        earliest = max(highs[-1][0] + config.pivot_right + 1, len(closed) - config.breakout_lookback - 1, 1)
        recent_breakout = any(closed[index].close > resistance * (1 + config.breakout_buffer_percent / 100)
                              and closed[index-1].close <= resistance
                              for index in range(earliest, len(closed)-1))
    pullback = bool(eligible and recent_breakout and atr and resistance is not None
                    and abs(closed[-1].low - resistance) <= config.pullback_atr_tolerance * atr
                    and closed[-1].close >= resistance and closed[-1].close > closed[-1].open
                    and volume_ratio is not None and volume_ratio >= 1.0)
    reasons = []
    if not last:
        reasons.append("No bars were closed and available by the analysis time.")
    if not history_ok:
        reasons.append(f"Need at least {max(config.ma_slow, config.atr_period + 1)} closed daily bars.")
    if not visible.session_dates:
        reasons.append("No provider-declared session calendar; parent-week confirmation is blocked.")
    elif not parent_confirmed:
        reasons.append("Not enough fully completed declared parent weeks.")
    if last and not closed_bar_confirmed:
        reasons.append("Latest visible bar is provisional; it cannot confirm an entry.")
    if breakdown:
        state = "Breakdown"
        reasons.append("A closed daily bar broke the latest confirmed pivot low.")
    elif overheated:
        state = "Exhaustion"
        reasons.append("Price is beyond the experimental ATR distance limit.")
    elif not history_ok or not parent_confirmed or not closed_bar_confirmed:
        state = "No Trade"
    elif pullback:
        state = "Pullback Entry Zone"
        reasons.append("Closed rebound at a previously broken confirmed resistance level.")
    elif breakout:
        state = "Confirmed Breakout"
        reasons.append("Closed resistance breakout with volume and completed parent trend confirmation.")
    elif resistance is not None and atr and abs(price - resistance) <= config.pullback_atr_tolerance * atr:
        state = "Breakout Watch"
        reasons.append("Near confirmed resistance without a fully confirmed breakout.")
    else:
        state = "Base Building"
        reasons.append("No confirmed entry structure under the experimental rules.")
    stop = support - config.stop_buffer_atr * atr if support is not None and atr else None
    if stop is not None and (stop <= 0 or price is None or stop >= price):
        stop = None
    return {"state": state, "closed_bar_confirmed": closed_bar_confirmed,
            "suggested_stop": stop, "support": support, "resistance": resistance, "reasons": reasons,
            "metrics": {"ma20": ma20, "ma50": ma50, "atr": atr,
                        "atr_percent": atr / price * 100 if atr is not None and price else None,
                        "price": price, "volume_ratio": volume_ratio,
                        "distance_from_ma20_atr": distance, "parent_cycle": parent,
                        "parent_week_confirmed": parent_confirmed, "parent_weeks": weekly,
                        "pivot_high_confirmed": bool(highs), "pivot_low_confirmed": bool(lows),
                        "breakout_confirmed": breakout, "pullback_confirmed": pullback,
                        "overheated": overheated, "breakdown": breakdown,
                        "history_sufficient": history_ok, "parameters_experimental": True,
                        "parameters": asdict(config)}}
