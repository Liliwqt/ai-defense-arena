"""Private opening context; commits share the account store's charge transaction."""

from dataclasses import dataclass
import hashlib
import json
import time
import unicodedata
import re

from backend.account_store import AccessError, connect_store, database_path


class RepeatedOpening(AccessError):
    """A valid candidate repeats recent context and must not be charged/published."""


def _digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()


def paper_key(files) -> str:
    """Accepted content, including document boundaries, independent of filenames/code."""
    documents = sorted(_digest(file.content) for file in files if file.kind.startswith("research_"))
    if not documents:
        raise ValueError("Opening history requires accepted research content.")
    return "paper-v1:" + _digest(documents)


def question_key(question: str) -> str:
    normalized = " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", question).casefold()))
    return _digest(normalized)


@dataclass(frozen=True)
class OpeningQuestion:
    paper_key: str
    question: str
    panelist: str
    topic_id: str

    @property
    def commit_key(self) -> str:
        return _digest((self.paper_key, self.question, self.panelist, self.topic_id))


def initialize(db, *, postgres=False) -> None:
    db.execute("""CREATE TABLE IF NOT EXISTS research_openings (
        run_kind TEXT NOT NULL, run_id TEXT NOT NULL,
        account_id TEXT NOT NULL REFERENCES accounts(id), paper_key TEXT NOT NULL,
        question TEXT NOT NULL, question_key TEXT NOT NULL, panelist TEXT NOT NULL,
        topic_id TEXT NOT NULL, committed_at INTEGER NOT NULL, commit_order INTEGER NOT NULL,
        PRIMARY KEY(run_kind,run_id))""")
    db.execute("CREATE INDEX IF NOT EXISTS openings_by_host_paper ON research_openings(account_id,paper_key,committed_at)")
    db.execute("CREATE INDEX IF NOT EXISTS openings_by_expiry ON research_openings(committed_at)")
    for table in ("defense_runs", "live_runs"):
        columns = db.columns(table) if postgres else {row["name"] for row in db.execute(f"PRAGMA table_info({table})")}
        if "opening_commit" not in columns:
            db.execute(f"ALTER TABLE {table} ADD COLUMN opening_commit TEXT")


def _prune_expired(db, now: int) -> None:
    db.execute("""DELETE FROM research_openings WHERE (run_kind,run_id) IN
        (SELECT run_kind,run_id FROM research_openings WHERE committed_at<=? LIMIT 100)""",
        (now - 30 * 86400,))


def _recent(db, account_id: str, key: str, now: int) -> list[dict]:
    return [dict(row) for row in db.execute("""SELECT question,question_key,panelist,topic_id
        FROM research_openings WHERE account_id=? AND paper_key=? AND committed_at>?
        ORDER BY commit_order DESC LIMIT 5""", (account_id, key, now - 30 * 86400)).fetchall()]


def recent_openings(account_id: str, key: str, *, now=None) -> list[dict]:
    now = int(time.time()) if now is None else now
    with connect_store(database_path()) as db:
        db.execute("BEGIN IMMEDIATE")
        _prune_expired(db, now)
        return _recent(db, account_id, key, now)


def prune_openings() -> None:
    """Bounded maintenance also removes expired keys that are never read again."""
    with connect_store(database_path()) as db:
        db.execute("BEGIN IMMEDIATE")
        _prune_expired(db, int(time.time()))


def commit_opening(db, account_id: str, run_id: str, opening: OpeningQuestion, *, live: bool, accept_repeat: bool = False) -> None:
    table, kind = ("live_runs", "live") if live else ("defense_runs", "test")
    row = db.execute(f"SELECT opening_commit FROM {table} WHERE id=? AND account_id=?", (run_id, account_id)).fetchone()
    if row is None:
        raise AccessError("Run access has expired. Retry the opening question.")
    if row[0]:
        if row[0] != opening.commit_key:
            raise AccessError("This run already committed a different opening.")
        return
    now = int(time.time())
    _prune_expired(db, now)
    if any(entry["question_key"] == question_key(opening.question)
           for entry in _recent(db, account_id, opening.paper_key, now)) and not accept_repeat:
        raise RepeatedOpening("The AI repeated a recent opening. Retry the first question for another supported angle; no defense was charged.")
    order = db.execute("SELECT COALESCE(MAX(commit_order),0)+1 FROM research_openings WHERE account_id=? AND paper_key=?",
                       (account_id, opening.paper_key)).fetchone()[0]
    db.execute("""INSERT INTO research_openings VALUES (?,?,?,?,?,?,?,?,?,?)""",
               (kind, run_id, account_id, opening.paper_key, opening.question[:4000],
                question_key(opening.question), opening.panelist, opening.topic_id, now, order))
    db.execute("""DELETE FROM research_openings WHERE account_id=? AND paper_key=? AND
        (run_kind,run_id) NOT IN (SELECT run_kind,run_id FROM research_openings WHERE account_id=? AND paper_key=?
        ORDER BY commit_order DESC LIMIT 5)""", (account_id, opening.paper_key, account_id, opening.paper_key))
    db.execute(f"UPDATE {table} SET opening_commit=? WHERE id=?", (opening.commit_key, run_id))
