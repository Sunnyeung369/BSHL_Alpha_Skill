"""Transactional local research journal. Decisions are records, never orders."""
from contextlib import contextmanager
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import sqlite3
import tempfile

from data.contracts import validate_symbol
from .market import parse_timestamp
from .serialization import to_jsonable, loads


TABLES = {
    "snapshots": ("id", "symbol", "as_of", "digest", "payload"),
    "watchlist": ("symbol", "snapshot_id", "conditions"),
    "decisions": ("id", "snapshot_id", "payload"),
    "reviews": ("id", "snapshot_id", "payload"),
    "calendar": ("id", "symbol", "payload"),
    "changes": ("id", "symbol", "snapshot_id", "payload"),
    "candidates": ("id", "payload"),
    "candidate_decisions": ("id", "candidate_id", "payload"),
}
STATES = {"Research Only", "Watchlist", "Trade Ready", "Wait Pullback", "Avoid", "Veto"}


def canonical(value):
    return json.dumps(to_jsonable(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value):
    return sha256(canonical(value).encode("utf-8")).hexdigest()


def _change_reasons(before, after):
    reasons = []
    if before["final_status"] != after["final_status"]:
        reasons.append("readiness_changed")
    if before["blockers"] != after["blockers"]:
        reasons.append("blockers_changed")
    if before["technical_structure"].get("state") != after["technical_structure"].get("state"):
        reasons.append("structure_changed")
    old_plan, new_plan = before["trade_plan"], after["trade_plan"]
    if old_plan.get("stop_loss_defined") is True and new_plan["entry_price"] <= old_plan["stop_loss_price"]:
        reasons.append("prior_stop_invalidation_hit")
    return reasons


def _candidate_payload(db, proposal):
    if (not isinstance(proposal, dict) or not isinstance(proposal.get("rule_id"), str)
            or not re.fullmatch(r"(?:research|structure)\.[a-zA-Z0-9_.-]+", proposal["rule_id"])):
        raise ValueError("Only research/structure candidate namespaces are allowed; hard gates stay fixed")
    if (not isinstance(proposal.get("comparison"), dict) or not isinstance(proposal.get("review_ids"), list)
            or not proposal["review_ids"] or not all(isinstance(item, str) for item in proposal["review_ids"])):
        raise ValueError("Candidate needs comparison results and existing review_ids")
    unique_snapshots = set()
    for record_id in proposal["review_ids"]:
        review = db.execute("SELECT snapshot_id FROM reviews WHERE id=?", (record_id,)).fetchone()
        if review is None:
            raise ValueError("Unknown review reference")
        unique_snapshots.add(review["snapshot_id"])
    return {**to_jsonable(proposal), "review_ids": sorted(set(proposal["review_ids"])),
            "unique_decision_count": len(unique_snapshots),
            "evidence_status": "insufficient" if len(unique_snapshots) < 30 else "requires_independent_holdout",
            "comparison_verification": "user_supplied_not_independently_verified",
            "status": "candidate_only", "automatically_applied": False}


def validate_card(card, *, historical=False):
    if not isinstance(card, dict) or card.get("schema_version") != "1.0":
        raise ValueError("Expected research card schema_version 1.0")
    for field in ("source", "technical_structure", "trade_readiness", "risk_governor", "evidence", "trade_plan", "context"):
        if not isinstance(card.get(field), dict):
            raise ValueError(f"Card {field} must be an object")
    for field in ("alpha_thesis", "market_pricing"):
        if card.get(field) is not None and not isinstance(card[field], dict):
            raise ValueError(f"Card {field} must be an object or null")
    if not isinstance(card.get("blockers"), list) or not all(isinstance(item, str) for item in card["blockers"]):
        raise ValueError("Invalid card blockers")
    if not isinstance(card.get("analysis_id"), str) or not re.fullmatch(r"[0-9a-f]{64}", card["analysis_id"]):
        raise ValueError("Invalid analysis_id")
    validate_symbol(card.get("symbol"))
    parse_timestamp(card.get("as_of"))
    if card.get("final_status") not in STATES or type(card.get("is_mock")) is not bool:
        raise ValueError("Invalid research status or data label")
    if card["is_mock"] and card["final_status"] != "Research Only":
        raise ValueError("Mock cards must remain Research Only")
    if (card.get("data_mode") not in ("csv", "mock", "live")
            or card.get("data_mode") == "mock" and card["is_mock"] is not True
            or card["is_mock"] and card.get("data_mode") != "mock"):
        raise ValueError("Invalid or conflicting card data mode")
    if not isinstance(card.get("rule_version"), str) or not card["rule_version"]:
        raise ValueError("Missing rule version")
    plan = card["trade_plan"]
    entry, stop, target = (plan.get(key) for key in ("entry_price", "stop_loss_price", "target_price"))
    if type(entry) not in (int, float) or not math.isfinite(entry) or entry <= 0:
        raise ValueError("Invalid card entry price")
    for value in (stop, target):
        if value is not None and (type(value) not in (int, float) or not math.isfinite(value) or value <= 0):
            raise ValueError("Invalid selected level")
    if (type(plan.get("stop_loss_defined")) is not bool or type(plan.get("target_defined")) is not bool
            or plan["stop_loss_defined"] != (stop is not None and stop < entry)
            or plan["target_defined"] != (target is not None and target > entry)):
        raise ValueError("Inconsistent selected-level flags")
    from .engine import RULE_VERSION, _url
    if not _url(card["source"].get("url")):
        raise ValueError("Invalid card provenance URL")
    if card["rule_version"] == RULE_VERSION:
        _validate_calculated_card(card)
    elif card["final_status"] == "Trade Ready" and not historical:
        raise ValueError("Rebuild older/unknown Trade Ready cards with the current rules before importing")
    if card["final_status"] == "Trade Ready":
        from scoring.risk_governor_score import RiskGovernorScorer
        risk = card.get("risk_governor", {})
        checks = risk.get("checks", [])
        if not isinstance(checks, list) or not all(isinstance(item, dict) for item in checks):
            raise ValueError("Invalid risk checklist")
        names = [item.get("name") for item in checks]
        plan = card.get("trade_plan", {})
        trade = card.get("trade_readiness", {})
        source = card.get("source", {})
        structure = card.get("technical_structure", {})
        metrics = structure.get("metrics", {})
        if (source.get("market") != "US" or source.get("currency") != "USD" or source.get("timeframe") != "1d"
                or source.get("asset_type") not in ("US_STOCK", "ETF") or source.get("adjustment") != "unadjusted"
                or source.get("exchange") not in ("NYSE", "NASDAQ", "NYSE_ARCA", "CBOE")
                or structure.get("state") not in ("Confirmed Breakout", "Pullback Entry Zone")
                or structure.get("closed_bar_confirmed") is not True
                or metrics.get("parent_week_confirmed") is not True or metrics.get("history_sufficient") is not True
                or card.get("evidence", {}).get("strong_support_count", 0) < 1
                or card.get("evidence", {}).get("active_kill_switch_count") != 0
                or (card.get("alpha_thesis") or {}).get("grade") not in ("A", "B", "C")
                or (card.get("alpha_thesis") or {}).get("breakdown", {}).get("evidence_quality", 0) < 10
                or (card.get("market_pricing") or {}).get("grade") not in ("A", "B", "C")
                or type(trade.get("total")) not in (int, float) or not 85 <= trade["total"] <= 100):
            raise ValueError("Trade Ready card lacks a supported evidence/structure profile")
        if (set(names) != set(RiskGovernorScorer.ITEMS) or len(names) != 10
                or not all(item.get("status") is True for item in checks)
                or risk.get("decision") != "Pass" or risk.get("missing_checks") != []
                or risk.get("triggered_conditions") != [] or card.get("blockers") != []
                or plan.get("stop_loss_defined") is not True or plan.get("target_defined") is not True
                or trade.get("closed_bar_confirmed") is not True or trade.get("stop_loss_defined") is not True):
            raise ValueError("Trade Ready card has unresolved gates")
        entry, stop, target = (plan.get(key) for key in ("entry_price", "stop_loss_price", "target_price"))
        if not all(type(value) in (int, float) and math.isfinite(value) for value in (entry, stop, target)):
            raise ValueError("Invalid trade levels")
        if not 0 < stop < entry < target or (target - entry) / (entry - stop) < 2:
            raise ValueError("Invalid reward/risk")
        ratio = (target - entry) / (entry - stop)
        if type(plan.get("reward_risk_ratio")) not in (int, float) or abs(plan["reward_risk_ratio"] - ratio) > 1e-9 or (entry - stop) / entry > .10:
            raise ValueError("Inconsistent ratio or excessive stop distance")
    return to_jsonable(card)


def _validate_calculated_card(card):
    """Recheck derived gates without claiming to authenticate supplied market bars."""
    from scoring import AlphaThesisScorer, MarketPricingScorer
    from .engine import _score, _evidence_at, _risk_score, _trade_score
    context, source, structure, plan = (card[key] for key in ("context", "source", "technical_structure", "trade_plan"))
    allowed = {"alpha_scores", "pricing_scores", "risk_checks", "stop_loss_price", "target_price", "evidence"}
    if set(context) - allowed:
        raise ValueError("Unknown card context fields")
    metrics = structure.get("metrics")
    if not isinstance(metrics, dict):
        raise ValueError("Card metrics must be an object")
    from datetime import date
    from .market import Dataset, validate_dataset
    try:
        declared = Dataset(symbol=card["symbol"], **{key: source[key] for key in
            ("market", "timeframe", "currency", "timezone", "adjustment", "asset_type", "exchange")},
            source_url=source["url"], retrieved_at=parse_timestamp(source["retrieved_at"]),
            session_dates=tuple(date.fromisoformat(value) for value in source["session_dates"]),
            is_mock=card["is_mock"], data_mode=card["data_mode"])
        validate_dataset(declared)
    except (KeyError, TypeError) as exc:
        raise ValueError("Invalid declared card source") from exc
    if source.get("verification") != "user_supplied_not_independently_verified":
        raise ValueError("A card cannot authenticate its own supplied source")
    at = parse_timestamp(card["as_of"])
    close_at = parse_timestamp(metrics.get("latest_bar_timestamp"))
    volume = metrics.get("latest_bar_volume")
    if close_at > at or type(volume) not in (int, float) or not math.isfinite(volume) or volume < 0:
        raise ValueError("Invalid last-bar time or volume")
    if card["final_status"] == "Trade Ready" and (at - close_at).total_seconds() > 4 * 86400:
        raise ValueError("Imported Trade Ready market data is stale")
    if (metrics.get("price") != plan["entry_price"]
            or context.get("stop_loss_price") != plan["stop_loss_price"]
            or context.get("target_price") != plan["target_price"]):
        raise ValueError("Selected levels or entry price disagree with the original context/metrics")
    expected_ratio = ((plan["target_price"] - plan["entry_price"]) / (plan["entry_price"] - plan["stop_loss_price"])
                      if plan["stop_loss_defined"] and plan["target_defined"] else None)
    if (canonical(expected_ratio) != canonical(plan.get("reward_risk_ratio"))
            or plan.get("stop_source") != ("user" if plan["stop_loss_price"] is not None else "absent")):
        raise ValueError("Inconsistent selected-plan metadata")
    evidence = _evidence_at(context.get("evidence", []), at)
    risk = _risk_score(context, structure, evidence, market=source.get("market"), currency=source.get("currency"),
                       entry=plan["entry_price"], stop=plan["stop_loss_price"], volume=volume)
    expected = {
        "alpha_thesis": _score(AlphaThesisScorer(), context.get("alpha_scores"), "alpha_scores"),
        "market_pricing": _score(MarketPricingScorer(), context.get("pricing_scores"), "pricing_scores"),
        "evidence": evidence, "risk_governor": risk,
        "trade_readiness": _trade_score(structure, plan["stop_loss_defined"], expected_ratio),
    }
    for field, computed in expected.items():
        if canonical(card[field]) != canonical(computed):
            raise ValueError(f"Card {field} disagrees with recomputed context and gates")


def _validate_approval(card, stamp, *, historical=False):
    from .engine import RULE_VERSION, _evidence_at
    validate_card(card, historical=historical)
    # Preserve legacy decisions under their historical rules; new approvals
    # always require the current rule version through validate_card above.
    if historical and card["rule_version"] != RULE_VERSION:
        return
    close_at = parse_timestamp(card["technical_structure"]["metrics"]["latest_bar_timestamp"])
    evidence = _evidence_at(card["context"].get("evidence", []), stamp)
    if ((stamp - close_at).total_seconds() > 4 * 86400 or evidence["strong_support_count"] < 1
            or evidence["active_kill_switch_count"]):
        raise ValueError("Plan is stale or its evidence changed; reassess before recording approval")


class Workspace:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            version = db.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, 1):
                raise ValueError("Unsupported workspace schema; preserve the database")
            db.executescript("""
                CREATE TABLE IF NOT EXISTS snapshots(id TEXT PRIMARY KEY, symbol TEXT NOT NULL,
                  as_of TEXT NOT NULL, digest TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS watchlist(symbol TEXT PRIMARY KEY,
                  snapshot_id TEXT NOT NULL REFERENCES snapshots(id), conditions TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS decisions(id TEXT PRIMARY KEY,
                  snapshot_id TEXT NOT NULL REFERENCES snapshots(id), payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,
                  snapshot_id TEXT NOT NULL REFERENCES snapshots(id), payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS calendar(id TEXT PRIMARY KEY, symbol TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS changes(id TEXT PRIMARY KEY, symbol TEXT NOT NULL,
                  snapshot_id TEXT NOT NULL REFERENCES snapshots(id), payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS candidate_decisions(id TEXT PRIMARY KEY,
                  candidate_id TEXT NOT NULL REFERENCES candidates(id), payload TEXT NOT NULL);
                PRAGMA user_version=1;
            """)
            for table in TABLES:
                if table == "watchlist":
                    continue
                for action in ("UPDATE", "DELETE"):
                    db.execute(f"CREATE TRIGGER IF NOT EXISTS immutable_{table}_{action} BEFORE {action} ON {table} BEGIN SELECT RAISE(ABORT, 'immutable record'); END")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        try:
            with db:
                yield db
        finally:
            db.close()

    @staticmethod
    def _snapshot(db, analysis_id):
        row = db.execute("SELECT payload FROM snapshots WHERE id=?", (analysis_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown snapshot")
        return loads(row["payload"])

    def snapshot(self, analysis_id):
        with self.connect() as db:
            return self._snapshot(db, analysis_id)

    def save(self, card, *, watch=False, conditions=None):
        card = validate_card(card)
        if type(watch) is not bool:
            raise ValueError("watch must be a boolean")
        if conditions is not None and (not isinstance(conditions, list) or not all(isinstance(item, str) and item.strip() for item in conditions)):
            raise ValueError("conditions must be nonempty strings")
        with self.connect() as db:
            old = db.execute("SELECT digest FROM snapshots WHERE id=?", (card["analysis_id"],)).fetchone()
            if old and old["digest"] != digest(card):
                raise ValueError("Snapshot ID collision; original is immutable")
            db.execute("INSERT OR IGNORE INTO snapshots VALUES(?,?,?,?,?)", (card["analysis_id"], card["symbol"], card["as_of"], digest(card), canonical(card)))
            watched = db.execute("SELECT * FROM watchlist WHERE symbol=?", (card["symbol"],)).fetchone()
            changes = []
            if watched and watched["snapshot_id"] != card["analysis_id"]:
                before = self._snapshot(db, watched["snapshot_id"])
                if parse_timestamp(card["as_of"]) < parse_timestamp(before["as_of"]):
                    raise ValueError("Cannot replace a watchlist with an older decision")
                changes = _change_reasons(before, card)
                if changes:
                    event = {"before": watched["snapshot_id"], "after": card["analysis_id"], "as_of": card["as_of"], "reasons": changes}
                    db.execute("INSERT OR IGNORE INTO changes VALUES(?,?,?,?)", (digest(event), card["symbol"], card["analysis_id"], canonical(event)))
            if watch or watched:
                effective = conditions if conditions is not None else loads(watched["conditions"]) if watched else []
                db.execute("INSERT INTO watchlist VALUES(?,?,?) ON CONFLICT(symbol) DO UPDATE SET snapshot_id=excluded.snapshot_id, conditions=excluded.conditions",
                           (card["symbol"], card["analysis_id"], canonical(effective)))
            return {"analysis_id": card["analysis_id"], "changes": changes, "watched": bool(watch or watched)}

    def decide(self, analysis_id, choice, at, note=""):
        if choice not in ("research", "wait", "approve_plan", "reject_plan") or not isinstance(note, str):
            raise ValueError("Invalid user decision")
        stamp = parse_timestamp(at)
        with self.connect() as db:
            card = self._snapshot(db, analysis_id)
            if stamp < parse_timestamp(card["as_of"]):
                raise ValueError("Decision predates snapshot")
            if choice == "approve_plan" and card["final_status"] != "Trade Ready":
                raise ValueError("Only a non-mock Trade Ready plan may be recorded as approved")
            if choice == "approve_plan":
                _validate_approval(card, stamp)
            payload = {"choice": choice, "at": stamp.isoformat(), "note": note, "orders_placed": False}
            record_id = digest({"snapshot": analysis_id, **payload})
            db.execute("INSERT OR IGNORE INTO decisions VALUES(?,?,?)", (record_id, analysis_id, canonical(payload)))
            return record_id

    def review(self, analysis_id, outcome, at, *, realized_r=None, costs=0.0, note=""):
        if outcome not in ("profit", "loss", "no_trade", "unknown") or not isinstance(note, str):
            raise ValueError("Invalid review outcome")
        if type(costs) not in (int, float) or not math.isfinite(costs) or costs < 0:
            raise ValueError("Costs must be finite and nonnegative")
        if realized_r is not None and (type(realized_r) not in (int, float) or not math.isfinite(realized_r)):
            raise ValueError("realized_r must be finite or null")
        if outcome == "profit" and (realized_r is None or realized_r <= 0) or outcome == "loss" and (realized_r is None or realized_r >= 0):
            raise ValueError("Profit/loss requires correctly signed realized_r after costs")
        if outcome in ("no_trade", "unknown") and realized_r is not None:
            raise ValueError("No trade/unknown cannot have a realized trade return")
        stamp = parse_timestamp(at)
        with self.connect() as db:
            card = self._snapshot(db, analysis_id)
            if stamp < parse_timestamp(card["as_of"]):
                raise ValueError("Review predates decision")
            payload = {"outcome": outcome, "at": stamp.isoformat(), "realized_r_after_costs": realized_r, "costs": costs, "note": note}
            record_id = digest({"snapshot": analysis_id, **payload})
            db.execute("INSERT OR IGNORE INTO reviews VALUES(?,?,?)", (record_id, analysis_id, canonical(payload)))
            return record_id

    def schedule(self, symbol, name, at, source_url):
        validate_symbol(symbol)
        from .engine import _url
        if not _url(source_url) or not isinstance(name, str) or not name.strip():
            raise ValueError("Calendar event needs a name and HTTP(S) source")
        payload = {"name": name, "at": parse_timestamp(at).isoformat(), "source_url": source_url,
                   "verification": "user_supplied", "action": "review_research"}
        record_id = digest({"symbol": symbol, **payload})
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO calendar VALUES(?,?,?)", (record_id, symbol, canonical(payload)))
        return record_id

    def status(self, as_of):
        cutoff = parse_timestamp(as_of)
        state = self.export()["tables"]
        due = [{"id": row["id"], "symbol": row["symbol"], **loads(row["payload"])} for row in state["calendar"]
               if parse_timestamp(loads(row["payload"])["at"]) <= cutoff]
        snapshots = {row["id"]: row for row in state["snapshots"]}
        return {"watchlist": [{**row, "conditions": loads(row["conditions"])} for row in state["watchlist"]
                    if parse_timestamp(snapshots[row["snapshot_id"]]["as_of"]) <= cutoff],
                "changes": [{"id": row["id"], "symbol": row["symbol"], **loads(row["payload"])} for row in state["changes"]
                    if parse_timestamp(loads(row["payload"])["as_of"]) <= cutoff],
                "events_due_for_review": due, "automatic_monitoring": False, "orders_placed": False}

    def propose(self, proposal):
        with self.connect() as db:
            payload = _candidate_payload(db, proposal)
            record_id = digest(payload)
            db.execute("INSERT OR IGNORE INTO candidates VALUES(?,?)", (record_id, canonical(payload)))
            return record_id

    def approve_candidate(self, candidate_id, choice, at, note):
        if choice not in ("approve_for_holdout", "reject") or not isinstance(note, str) or not note.strip():
            raise ValueError("Candidate review needs a choice and rationale")
        payload = {"choice": choice, "at": parse_timestamp(at).isoformat(), "note": note, "automatically_applied": False}
        record_id = digest({"candidate": candidate_id, **payload})
        with self.connect() as db:
            candidate = db.execute("SELECT payload FROM candidates WHERE id=?", (candidate_id,)).fetchone()
            if candidate is None:
                raise ValueError("Unknown candidate")
            for review_id in loads(candidate["payload"])["review_ids"]:
                review = db.execute("SELECT payload FROM reviews WHERE id=?", (review_id,)).fetchone()
                if parse_timestamp(payload["at"]) < parse_timestamp(loads(review["payload"])["at"]):
                    raise ValueError("Candidate decision predates its review evidence")
            db.execute("INSERT OR IGNORE INTO candidate_decisions VALUES(?,?,?)", (record_id, candidate_id, canonical(payload)))
        return record_id

    def export(self):
        with self.connect() as db:
            tables = {name: [dict(row) for row in db.execute(f"SELECT * FROM {name} ORDER BY {columns[0]}")]
                      for name, columns in TABLES.items()}
        return {"schema_version": 1, "tables": tables, "checksum": digest(tables)}

    @classmethod
    def restore(cls, bundle, target):
        if not isinstance(bundle, dict) or bundle.get("schema_version") != 1 or set(bundle.get("tables", {})) != set(TABLES):
            raise ValueError("Invalid workspace export schema")
        if digest(bundle["tables"]) != bundle.get("checksum"):
            raise ValueError("Export checksum mismatch")
        target = Path(target)
        if target.exists():
            raise FileExistsError("Restore requires a new path; preserve existing workspace")
        target.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(prefix="bshl-restore-", suffix=".sqlite3", dir=target.parent)
        os.close(handle)
        temporary = Path(temporary)
        try:
            workspace = cls(temporary)
            with workspace.connect() as db:
                for table, columns in TABLES.items():
                    for row in bundle["tables"][table]:
                        if not isinstance(row, dict) or set(row) != set(columns) or not all(isinstance(value, str) for value in row.values()):
                            raise ValueError("Invalid export row")
                        if table == "snapshots":
                            card = validate_card(loads(row["payload"]), historical=True)
                            if (row["digest"] != digest(card) or row["id"] != card["analysis_id"]
                                    or row["symbol"] != card["symbol"] or row["as_of"] != card["as_of"]):
                                raise ValueError("Snapshot integrity mismatch")
                        if "payload" in row:
                            loads(row["payload"])
                        if table == "watchlist":
                            loads(row["conditions"])
                        db.execute(f"INSERT INTO {table}({','.join(columns)}) VALUES({','.join('?' for _ in columns)})", tuple(row[key] for key in columns))
                if db.execute("PRAGMA foreign_key_check").fetchall():
                    raise ValueError("Broken snapshot references")
                cls._validate_restored_records(db)
            # Same-volume exclusive hard link publishes a complete, closed DB.
            # Existing targets, including a racing writer, are never replaced.
            os.link(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)
        return cls(target)

    @classmethod
    def _validate_restored_records(cls, db):
        """A recomputed checksum cannot legitimize invalid domain records."""
        for row in db.execute("SELECT * FROM watchlist"):
            card = cls._snapshot(db, row["snapshot_id"])
            conditions = loads(row["conditions"])
            if row["symbol"] != card["symbol"] or not isinstance(conditions, list) or not all(isinstance(item, str) and item.strip() for item in conditions):
                raise ValueError("Invalid restored watchlist")
        for table in TABLES:
            if table in ("snapshots", "watchlist"):
                continue
            for row in db.execute(f"SELECT * FROM {table}"):
                payload = loads(row["payload"])
                if not isinstance(payload, dict):
                    raise ValueError("Record payload must be an object")
                identity = dict(payload)
                if table in ("decisions", "reviews"):
                    identity["snapshot"] = row["snapshot_id"]
                    card = cls._snapshot(db, row["snapshot_id"])
                    if parse_timestamp(payload.get("at")) < parse_timestamp(card["as_of"]):
                        raise ValueError("Restored record predates snapshot")
                elif table == "calendar":
                    identity["symbol"] = row["symbol"]
                    validate_symbol(row["symbol"])
                    parse_timestamp(payload.get("at"))
                    from .engine import _url
                    if (not _url(payload.get("source_url")) or not isinstance(payload.get("name"), str)
                            or not payload["name"].strip() or payload.get("action") != "review_research"
                            or payload.get("verification") != "user_supplied"):
                        raise ValueError("Invalid restored calendar source")
                elif table == "candidate_decisions":
                    identity["candidate"] = row["candidate_id"]
                    parse_timestamp(payload.get("at"))
                    if (payload.get("choice") not in ("approve_for_holdout", "reject") or payload.get("automatically_applied") is not False
                            or not isinstance(payload.get("note"), str) or not payload["note"].strip()):
                        raise ValueError("Invalid restored candidate decision")
                    candidate = loads(db.execute("SELECT payload FROM candidates WHERE id=?", (row["candidate_id"],)).fetchone()["payload"])
                    for review_id in candidate.get("review_ids", []):
                        review = db.execute("SELECT payload FROM reviews WHERE id=?", (review_id,)).fetchone()
                        if review is None or parse_timestamp(payload["at"]) < parse_timestamp(loads(review["payload"])["at"]):
                            raise ValueError("Restored candidate decision predates its review evidence")
                if row["id"] != digest(identity):
                    raise ValueError("Record ID mismatch")
                if table == "decisions":
                    if (payload.get("choice") not in ("research", "wait", "approve_plan", "reject_plan")
                            or not isinstance(payload.get("note"), str)
                            or payload.get("orders_placed") is not False
                            or payload["choice"] == "approve_plan" and card["final_status"] != "Trade Ready"):
                        raise ValueError("Invalid restored user decision")
                    if payload["choice"] == "approve_plan":
                        _validate_approval(card, parse_timestamp(payload["at"]), historical=True)
                if table == "reviews":
                    outcome, r, costs = payload.get("outcome"), payload.get("realized_r_after_costs"), payload.get("costs")
                    if (outcome not in ("profit", "loss", "unknown", "no_trade")
                            or not isinstance(payload.get("note"), str)
                            or type(costs) not in (int, float) or not math.isfinite(costs) or costs < 0
                            or r is not None and (type(r) not in (int, float) or not math.isfinite(r))
                            or outcome == "profit" and (r is None or r <= 0)
                            or outcome == "loss" and (r is None or r >= 0)
                            or outcome in ("unknown", "no_trade") and r is not None):
                        raise ValueError("Invalid restored outcome")
                if table == "changes":
                    before = cls._snapshot(db, payload.get("before"))
                    after = cls._snapshot(db, payload.get("after"))
                    if row["symbol"] != before["symbol"] or row["symbol"] != after["symbol"] or row["snapshot_id"] != after["analysis_id"]:
                        raise ValueError("Invalid restored change references")
                    if (parse_timestamp(payload.get("as_of")) != parse_timestamp(after["as_of"])
                            or parse_timestamp(before["as_of"]) > parse_timestamp(after["as_of"])
                            or not isinstance(payload.get("reasons"), list) or not payload["reasons"]
                            or payload["reasons"] != _change_reasons(before, after)):
                        raise ValueError("Invalid restored change time or reasons")
                if table == "candidates":
                    if canonical(payload) != canonical(_candidate_payload(db, payload)):
                        raise ValueError("Restored candidate differs from its recomputed review evidence")
