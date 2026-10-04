"""Deterministic US cash, long-only daily simulation with explicit session opens.

This is a research simulator, not a broker. The caller supplies session times;
the engine does not invent an exchange calendar. No leverage, borrowing,
dividends, financing, taxes or intraday order-book model are implemented.
"""
from dataclasses import asdict, dataclass, replace
from datetime import date, datetime, time, timezone
import math
from typing import Callable, Optional

from .market import Bar, Dataset, parse_timestamp, session_gaps, validate_dataset
from .serialization import to_jsonable
from .structure import moving_average, wilder_atr


@dataclass(frozen=True, kw_only=True)
class BacktestConfig:
    train_end: date | datetime
    test_start: date | datetime
    initial_capital: float = 100000.0
    commission_bps: float = 1.0
    slippage_bps: float = 2.0
    spread_bps: float = 2.0
    risk_fraction: float = 0.01
    max_position: float = 0.1
    lookback: int = 20
    atr_period: int = 14
    stop_atr: float = 2.0
    reward_risk: float = 2.0
    max_volume_fraction: float = 0.01
    start_date: date | datetime | None = None
    end_date: date | datetime | None = None

    def __post_init__(self):
        if _bound(self.train_end, True) >= _bound(self.test_start, False):
            raise ValueError("train_end must be strictly before test_start")
        for name in ("initial_capital", "risk_fraction", "max_position", "stop_atr", "reward_risk", "max_volume_fraction"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{name} must be finite and positive")
        if max(self.risk_fraction, self.max_position, self.max_volume_fraction) > 1:
            raise ValueError("fractions must not exceed one")
        for name in ("commission_bps", "slippage_bps", "spread_bps"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value < 1000:
                raise ValueError(f"{name} must be in [0, 1000)")
        for name in ("lookback", "atr_period"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 2:
                raise ValueError(f"{name} must be an integer >= 2")
        if self.start_date is not None and self.end_date is not None:
            if _bound(self.start_date, False) > _bound(self.end_date, True):
                raise ValueError("start_date exceeds end_date")


def _bound(value: date | datetime, end: bool) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must be timezone aware")
        return value.astimezone(timezone.utc)
    if isinstance(value, date):
        return datetime.combine(value, time.max if end else time.min, timezone.utc)
    raise ValueError("expected date or timezone-aware datetime")


@dataclass(frozen=True)
class SignalSnapshot:
    symbol: str
    as_of: datetime
    bars: tuple[Bar, ...]


@dataclass(frozen=True)
class TradeSignal:
    stop: float
    target: float
    reason: str = "custom"


SignalCallback = Callable[[SignalSnapshot], Optional[TradeSignal]]


def breakout_signal(snapshot: SignalSnapshot, config: BacktestConfig) -> Optional[TradeSignal]:
    """Previous N highs, closed-bar breakout; Wilder ATR stop distance."""
    bars = snapshot.bars
    if len(bars) < max(config.lookback + 1, config.atr_period + 1):
        return None
    current = bars[-1]
    resistance = max(bar.high for bar in bars[-config.lookback - 1:-1])
    if current.close <= resistance:
        return None
    atr = wilder_atr(bars, config.atr_period)
    stop = current.close - config.stop_atr * atr
    if atr <= 0 or stop <= 0:
        return None
    return TradeSignal(stop, current.close + config.reward_risk * (current.close - stop), "rolling_breakout")


def _check_signal(signal: TradeSignal, close: float) -> None:
    if not isinstance(signal, TradeSignal):
        raise ValueError("callback must return TradeSignal or None")
    if not all(not isinstance(value, bool) and isinstance(value, (int, float))
               and math.isfinite(value) and value > 0 for value in (signal.stop, signal.target)):
        raise ValueError("signal levels must be finite and positive")
    if not isinstance(signal.reason, str) or not signal.reason.strip():
        raise ValueError("signal reason must be a nonempty string")
    if not signal.stop < close < signal.target:
        raise ValueError("long signal requires stop < decision close < target")


def _run_window(dataset: Dataset, config: BacktestConfig, start: datetime, end: datetime,
                callback: Optional[SignalCallback]) -> dict:
    bars = dataset.bars
    execution_drag = (config.slippage_bps + config.spread_bps / 2) / 10000
    commission = config.commission_bps / 10000
    cash = config.initial_capital
    position = None
    pending = None
    visible = []
    newest_decision_bar = None
    traded_notional = 0.0
    regimes = []
    trades, equity_curve, skipped = [], [], []
    events = []
    for index, bar in enumerate(bars):
        events.extend([(bar.session_open, 0, index, "open"),
                       (bar.timestamp, 1, index, "close"),
                       (bar.available_at, 2, index, "publish")])
    events.sort(key=lambda event: (event[0], event[1], event[2]))

    def sell(raw_price, at, reason):
        nonlocal cash, position, traded_notional
        fill = raw_price * (1 - execution_drag)
        exit_fee = position["units"] * fill * commission
        proceeds = position["units"] * fill - exit_fee
        traded_notional += position["units"] * fill
        cash += proceeds
        pnl = proceeds - position["entry_total"]
        trades.append({**position, "exit_at": at.isoformat(), "exit_price": fill,
            "exit_reason": reason, "exit_fee": exit_fee, "pnl_after_costs": pnl,
            "r_after_costs": pnl / position["initial_risk"],
            "total_costs": position["entry_fee"] + exit_fee +
                position["units"] * (position["entry_price"] - position["raw_entry"] + raw_price - fill)})
        position = None

    for at, _, index, kind in events:
        if at > end:
            break
        bar = bars[index]
        if kind == "publish":
            if not bar.is_closed:
                continue
            visible.append(bar)
            visible.sort(key=lambda item: item.timestamp)
            latest = visible[-1]
            if newest_decision_bar is not None and latest.timestamp <= newest_decision_bar:
                continue
            newest_decision_bar = latest.timestamp
            snapshot = SignalSnapshot(dataset.symbol, at, tuple(visible))
            if at >= start:
                average = moving_average(visible, 20)
                regimes.append({"as_of": at.isoformat(), "price_position_vs_ma20":
                    "unknown" if average is None else "above" if latest.close > average else "below" if latest.close < average else "at"})
            signal = callback(snapshot) if callback is not None else breakout_signal(snapshot, config)
            if signal is not None:
                _check_signal(signal, latest.close)
                # Levels and volume budget are frozen from known decision data.
                if position is None:
                    pending = (at, latest.timestamp, signal, latest.volume)
            continue
        if at < start:
            continue
        if kind == "open" and position is not None:
            # Standing stop/target orders act at the open, before a daily close.
            if bar.open <= position["stop"]:
                sell(bar.open, at, "gap_stop")
            elif bar.open >= position["target"]:
                sell(bar.open, at, "gap_target")
        if kind == "open" and position is None and pending is not None:
            decision_at, signal_bar, signal, known_volume = pending
            # Arrival at the auction time is conservatively too late for this open.
            if decision_at >= at:
                continue
            pending = None
            fill = bar.open * (1 + execution_drag)
            if not signal.stop < fill < signal.target:
                skipped.append({"at": at.isoformat(), "reason": "gap_invalidates_frozen_levels"})
                continue
            units = min(math.floor(cash * config.risk_fraction / (fill - signal.stop)),
                math.floor(cash * config.max_position / (fill * (1 + commission))),
                math.floor(cash / (fill * (1 + commission))),
                math.floor(known_volume * config.max_volume_fraction))
            if units <= 0:
                skipped.append({"at": at.isoformat(), "reason": "cash_risk_or_known_volume_insufficient"})
                continue
            entry_fee = units * fill * commission
            total = units * fill + entry_fee
            traded_notional += units * fill
            cash -= total
            position = {"entry_at": at.isoformat(), "decision_at": decision_at.isoformat(),
                "signal_bar": signal_bar.isoformat(), "raw_entry": bar.open,
                "entry_price": fill, "units": units, "entry_fee": entry_fee, "entry_total": total,
                "stop": signal.stop, "target": signal.target, "initial_risk": units * (fill - signal.stop),
                "signal_reason": signal.reason}
        elif kind == "close":
            # Data unavailable by the report cutoff cannot resolve fills or valuation.
            known_at_cutoff = bar.is_closed and bar.available_at <= end
            if position is not None and known_at_cutoff:
                if bar.open <= position["stop"]:
                    sell(bar.open, bar.session_open, "gap_stop")
                elif bar.open >= position["target"]:
                    sell(bar.open, bar.session_open, "gap_target")
                elif bar.low <= position["stop"]:
                    sell(position["stop"], bar.timestamp, "stop_conservative_intrabar")
                elif bar.high >= position["target"]:
                    sell(position["target"], bar.timestamp, "target_intrabar")
            equity = cash + position["units"] * bar.close if position is not None and known_at_cutoff else (
                cash if position is None else None)
            equity_curve.append({"timestamp": at.isoformat(), "available_at": bar.available_at.isoformat(),
                "equity": equity, "price_status": "known" if known_at_cutoff else "unknown"})

    window_bars = [bar for bar in bars if start <= bar.session_open <= end]
    last = window_bars[-1] if window_bars else None
    complete_last = last is not None and last.timestamp <= end and last.is_closed and last.available_at <= end
    valuation_known = position is None or complete_last
    if position is not None and complete_last and last.available_at <= last.timestamp:
        sell(last.close, last.timestamp, "window_end_close")
        if equity_curve:
            equity_curve[-1]["equity"] = cash
    final_value = (cash + position["units"] * last.close if position is not None else cash) if valuation_known and window_bars else None
    exposure_seconds = sum((parse_timestamp(trade["exit_at"]) - parse_timestamp(trade["entry_at"])).total_seconds() for trade in trades)
    if position is not None:
        exposure_seconds += max(0, (end - parse_timestamp(position["entry_at"])).total_seconds())
    peak, max_drawdown = config.initial_capital, 0.0
    for row in equity_curve:
        if row["equity"] is not None:
            peak = max(peak, row["equity"])
            max_drawdown = max(max_drawdown, (peak - row["equity"]) / peak)
    benchmark = {"return_after_costs": None, "status": "unknown", "allocation": "100% cash buy-and-hold"}
    if window_bars and complete_last:
        first = window_bars[0]
        entry = first.open * (1 + execution_drag)
        units = math.floor(config.initial_capital / (entry * (1 + commission)))
        value = config.initial_capital - units * entry * (1 + commission) + units * last.close * (1 - execution_drag) * (1 - commission)
        benchmark.update(return_after_costs=value / config.initial_capital - 1, status="simulated",
            start_at=first.session_open.isoformat(), end_at=last.timestamp.isoformat())
    wins = [trade for trade in trades if trade["pnl_after_costs"] > 0]
    losses = [trade for trade in trades if trade["pnl_after_costs"] < 0]
    return {"window": {"start": start.isoformat(), "end": end.isoformat()},
        "final_value": final_value, "return_after_costs": final_value / config.initial_capital - 1 if final_value is not None else None,
        "valuation_status": "empty_window" if not window_bars else "known" if valuation_known else "unknown", "open_position": position,
        "end_valuation_method": "mark_to_market_without_retroactive_exit" if position is not None and valuation_known else "cash" if position is None else "unknown",
        "trades": trades, "equity_curve": equity_curve, "max_drawdown": max_drawdown,
        "max_drawdown_complete": valuation_known and all(row["equity"] is not None for row in equity_curve),
        "expectancy_r_after_costs": sum(t["r_after_costs"] for t in trades) / len(trades) if trades else None,
        "trade_count": len(trades), "total_costs": sum(t["total_costs"] for t in trades) +
            (position["entry_fee"] + position["units"] * (position["entry_price"] - position["raw_entry"]) if position else 0),
        "win_rate": len(wins) / len(trades) if trades else None,
        "average_win_after_costs": sum(item["pnl_after_costs"] for item in wins) / len(wins) if wins else None,
        "average_loss_after_costs": sum(item["pnl_after_costs"] for item in losses) / len(losses) if losses else None,
        "exposure_seconds": exposure_seconds,
        "exposure_time_fraction": exposure_seconds / (end - start).total_seconds() if end > start and window_bars else None,
        "turnover_notional_over_initial_capital": traded_notional / config.initial_capital,
        "sample_evidence": "insufficient" if len(trades) < 30 else "unvalidated",
        "price_regime_diagnostics": regimes, "failed_trade_samples": losses,
        "benchmark": benchmark, "skipped": skipped}


def run_backtest(dataset: Dataset, config: BacktestConfig, signals: Optional[SignalCallback] = None) -> dict:
    """Pure deterministic computation if a custom callback is itself pure.

Callbacks receive an immutable visible snapshot. Python closures cannot be
sandboxed: callers must not capture future datasets or tune on the holdout.
"""
    validate_dataset(dataset)
    if dataset.market != "US" or dataset.timeframe != "1d" or dataset.currency != "USD":
        raise ValueError("only US/USD/1d cash profile is supported")
    if dataset.asset_type not in ("US_STOCK", "ETF"):
        raise ValueError("only US stocks and ETFs are supported")
    if dataset.adjustment != "unadjusted":
        raise ValueError("execution requires unadjusted prices; corporate actions are unsupported")
    if not dataset.bars:
        raise ValueError("dataset has no bars")
    for bar in dataset.bars:
        opening = getattr(bar, "session_open", None)
        if opening is None or opening.tzinfo is None or opening.utcoffset() is None or opening >= bar.timestamp:
            raise ValueError("each bar requires an explicit timezone-aware session_open before close")
        if bar.volume <= 0:
            raise ValueError("execution profile requires positive-volume daily bars")
    start = _bound(config.start_date, False) if config.start_date is not None else dataset.bars[0].session_open
    end = _bound(config.end_date, True) if config.end_date is not None else max(bar.available_at for bar in dataset.bars)
    if end < start:
        raise ValueError("empty time window")
    if not dataset.session_dates:
        raise ValueError("simulation requires a provider-declared session calendar")
    observed = replace(dataset, bars=tuple(bar for bar in dataset.bars if bar.session_open <= end))
    if session_gaps(observed):
        raise ValueError("simulation history is missing declared sessions; restore the missing bars before replay")
    result = _run_window(dataset, config, start, end, signals)
    train_end, test_start = _bound(config.train_end, True), _bound(config.test_start, False)
    result.update(mode="bar_event_simulation", profile="US_cash_long_only_daily", symbol=dataset.symbol,
        rule_version="rolling-breakout-0.7.0", parameters=to_jsonable(asdict(config)),
        signal_source="custom_callback" if signals is not None else "rolling_breakout",
        source={"url": dataset.source_url, "retrieved_at": to_jsonable(dataset.retrieved_at),
                "verification": "user_supplied_not_independently_verified"},
        is_mock=dataset.is_mock, data_mode=dataset.data_mode, performance_validated=False,
        evidence_status="synthetic_simulation" if dataset.is_mock else "historical_simulation_unvalidated",
        split_protocol={"train_end": train_end.isoformat(), "test_start": test_start.isoformat(),
            "parameters_frozen": True, "holdout_tuning_performed": False},
        in_sample=_run_window(dataset, config, start, min(end, train_end), signals),
        out_of_sample=_run_window(dataset, config, max(start, test_start), end, signals),
        assumptions=["Caller supplies session opens and calendar; engine does not verify an exchange calendar",
            "Next-open auction fills, whole shares, no leverage, fixed bilateral commission/slippage/half-spread",
            "Size uses decision-time volume; no order-book participation or intraday path reconstruction",
            "Frozen signal stop/target; if both touched, stop wins; gap exits use opening price",
            "End-window liquidation uses a known completed close; unknown end price is not replaced",
            "No dividends, splits, taxes, borrowing or financing; choose a corporate-action-free window",
            "Benchmark invests 100% cash, strategy position cap differs; this is not matched-exposure alpha"])
    return result
