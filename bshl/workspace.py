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
from urllib.parse import urlparse

from data.contracts import validate_symbol
from .market import parse_timestamp
from .serialization import to_jsonable


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


def validate_card(card):
    if not isinstance(card, dict) or card.get("schema_version") != "1.0":
        raise ValueError("Expected research card schema_version 1.0")
    if not isinstance(card.get("analysis_id"), str) or not re.fullmatch(r"[0-9a-f]{64}", card["analysis_id"]):
        raise ValueError("Invalid analysis_id")
    validate_symbol(card.get("symbol"))
    parse_timestamp(card.get("as_of"))
    if card.get("final_status") not in STATES or type(card.get("is_mock")) is not bool:
        raise ValueError("Invalid research status or data label")
    if card["is_mock"] and card["final_status"] != "Research Only":
        raise ValueError("Mock cards must remain Research Only")
    if not isinstance(card.get("rule_version"), str) or not card["rule_version"]:
        raise ValueError("Missing rule version")
    if card["final_status"] == "Trade Ready":
        from scoring.risk_governor_score import RiskGovernorScorer
        risk = card.get("risk_governor", {})
        checks = risk.get("checks", [])
        names = [item.get("name") for item in checks]
        plan = card.get("trade_plan", {})
        trade = card.get("trade_readiness", {})
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
    return to_jsonable(card)


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
        return json.loads(row["payload"])

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
                if before["final_status"] != card["final_status"]:
                    changes.append("readiness_changed")
                if before.get("blockers") != card.get("blockers"):
                    changes.append("blockers_changed")
                if before.get("technical_structure", {}).get("state") != card.get("technical_structure", {}).get("state"):
                    changes.append("structure_changed")
                price = card.get("trade_plan", {}).get("entry_price")
                old_stop = before.get("trade_plan", {}).get("stop_loss_price")
                if type(price) in (int, float) and type(old_stop) in (int, float) and price <= old_stop:
                    changes.append("prior_stop_invalidation_hit")
                if changes:
                    event = {"before": watched["snapshot_id"], "after": card["analysis_id"], "as_of": card["as_of"], "reasons": changes}
                    db.execute("INSERT OR IGNORE INTO changes VALUES(?,?,?,?)", (digest(event), card["symbol"], card["analysis_id"], canonical(event)))
            if watch or watched:
                effective = conditions if conditions is not None else json.loads(watched["conditions"]) if watched else []
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
        parsed = urlparse(source_url)
        if parsed.scheme not in ("https", "http") or not parsed.hostname or not isinstance(name, str) or not name.strip():
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
        due = [{"id": row["id"], "symbol": row["symbol"], **json.loads(row["payload"])} for row in state["calendar"]
               if parse_timestamp(json.loads(row["payload"])["at"]) <= cutoff]
        snapshots = {row["id"]: row for row in state["snapshots"]}
        return {"watchlist": [{**row, "conditions": json.loads(row["conditions"])} for row in state["watchlist"]
                    if parse_timestamp(snapshots[row["snapshot_id"]]["as_of"]) <= cutoff],
                "changes": [{"id": row["id"], "symbol": row["symbol"], **json.loads(row["payload"])} for row in state["changes"]
                    if parse_timestamp(json.loads(row["payload"])["as_of"]) <= cutoff],
                "events_due_for_review": due, "automatic_monitoring": False, "orders_placed": False}

    def propose(self, proposal):
        if not isinstance(proposal, dict) or not str(proposal.get("rule_id", "")).startswith(("research.", "structure.")):
            raise ValueError("Only research/structure candidate namespaces are allowed; hard gates stay fixed")
        if not isinstance(proposal.get("comparison"), dict) or not proposal.get("review_ids") or not isinstance(proposal.get("review_ids"), list):
            raise ValueError("Candidate needs comparison results and existing review_ids")
        with self.connect() as db:
            unique_snapshots = set()
            for record_id in proposal["review_ids"]:
                review = db.execute("SELECT snapshot_id FROM reviews WHERE id=?", (record_id,)).fetchone()
                if review is None:
                    raise ValueError("Unknown review reference")
                unique_snapshots.add(review["snapshot_id"])
            payload = {**to_jsonable(proposal), "review_ids": sorted(set(proposal["review_ids"])),
                       "unique_decision_count": len(unique_snapshots),
                       "evidence_status": "insufficient" if len(unique_snapshots) < 30 else "requires_independent_holdout",
                       "comparison_verification": "user_supplied_not_independently_verified",
                       "status": "candidate_only", "automatically_applied": False}
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
            for review_id in json.loads(candidate["payload"])["review_ids"]:
                review = db.execute("SELECT payload FROM reviews WHERE id=?", (review_id,)).fetchone()
                if parse_timestamp(payload["at"]) < parse_timestamp(json.loads(review["payload"])["at"]):
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
                            card = validate_card(json.loads(row["payload"]))
                            if (row["digest"] != digest(card) or row["id"] != card["analysis_id"]
                                    or row["symbol"] != card["symbol"] or row["as_of"] != card["as_of"]):
                                raise ValueError("Snapshot integrity mismatch")
                        if "payload" in row:
                            json.loads(row["payload"])
                        if table == "watchlist":
                            json.loads(row["conditions"])
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
            conditions = json.loads(row["conditions"])
            if row["symbol"] != card["symbol"] or not isinstance(conditions, list) or not all(isinstance(item, str) and item.strip() for item in conditions):
                raise ValueError("Invalid restored watchlist")
        for table in TABLES:
            if table in ("snapshots", "watchlist"):
                continue
            for row in db.execute(f"SELECT * FROM {table}"):
                payload = json.loads(row["payload"])
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
                    parsed = urlparse(payload.get("source_url", ""))
                    if parsed.scheme not in ("https", "http") or not parsed.hostname:
                        raise ValueError("Invalid restored calendar source")
                elif table == "candidate_decisions":
                    identity["candidate"] = row["candidate_id"]
                    parse_timestamp(payload.get("at"))
                    if payload.get("choice") not in ("approve_for_holdout", "reject") or payload.get("automatically_applied") is not False:
                        raise ValueError("Invalid restored candidate decision")
                if row["id"] != digest(identity):
                    raise ValueError("Record ID mismatch")
                if table == "decisions":
                    if (payload.get("choice") not in ("research", "wait", "approve_plan", "reject_plan")
                            or payload.get("orders_placed") is not False
                            or payload["choice"] == "approve_plan" and card["final_status"] != "Trade Ready"):
                        raise ValueError("Invalid restored user decision")
                if table == "reviews":
                    outcome, r, costs = payload.get("outcome"), payload.get("realized_r_after_costs"), payload.get("costs")
                    if (outcome not in ("profit", "loss", "unknown", "no_trade")
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
                if table == "candidates":
                    if (not str(payload.get("rule_id", "")).startswith(("research.", "structure."))
                            or payload.get("automatically_applied") is not False or payload.get("status") != "candidate_only"):
                        raise ValueError("Invalid restored hard-gate candidate")
                    for review_id in payload.get("review_ids", []):
                        if db.execute("SELECT id FROM reviews WHERE id=?", (review_id,)).fetchone() is None:
                            raise ValueError("Missing restored review evidence")
