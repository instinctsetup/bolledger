"""SQLite ledger: customers, transactions, balances, daily hisaab.

Money is stored as integer paise (1 rupee = 100 paise) - no float drift.
"""
import sqlite3
import time
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS customers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE COLLATE NOCASE,
  created_ts INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts INTEGER NOT NULL,
  customer_id INTEGER,                -- NULL for bikri/kharcha
  kind TEXT NOT NULL,                 -- udhaar_diya | jama | bikri | kharcha
  amount_paise INTEGER NOT NULL,
  note TEXT,
  raw_text TEXT,
  confidence REAL
);
CREATE INDEX IF NOT EXISTS idx_tx_ts ON transactions(ts);
CREATE INDEX IF NOT EXISTS idx_tx_customer ON transactions(customer_id);
"""

KINDS = {"udhaar_diya", "jama", "bikri", "kharcha"}


def to_paise(rupees: float) -> int:
    return int(round(rupees * 100))


def to_rupees(paise: int) -> float:
    return paise / 100.0


class Ledger:
    def __init__(self, db_path: str | Path = "data/bolledger.db"):
        self.db = sqlite3.connect(str(db_path), check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(SCHEMA)
        self.db.commit()

    def close(self):
        self.db.close()

    # ---- customers ---------------------------------------------------------
    def get_or_create_customer(self, name: str) -> int:
        row = self.db.execute("SELECT id FROM customers WHERE name=?", (name,)).fetchone()
        if row:
            return row["id"]
        cur = self.db.execute("INSERT INTO customers(name, created_ts) VALUES (?,?)", (name, int(time.time())))
        self.db.commit()
        return int(cur.lastrowid)

    def list_customers(self) -> list[dict]:
        rows = self.db.execute("""
          SELECT c.id, c.name,
            COALESCE(SUM(CASE WHEN t.kind='udhaar_diya' THEN t.amount_paise ELSE 0 END),0)
            - COALESCE(SUM(CASE WHEN t.kind='jama' THEN t.amount_paise ELSE 0 END),0) AS balance_paise,
            MAX(t.ts) AS last_ts
          FROM customers c LEFT JOIN transactions t ON t.customer_id=c.id
          GROUP BY c.id ORDER BY balance_paise DESC, c.name
        """).fetchall()
        return [{"id": r["id"], "name": r["name"], "balance": to_rupees(r["balance_paise"]), "last_ts": r["last_ts"]} for r in rows]

    def balance(self, name: str) -> float:
        row = self.db.execute("""
          SELECT COALESCE(SUM(CASE WHEN t.kind='udhaar_diya' THEN t.amount_paise ELSE 0 END),0)
               - COALESCE(SUM(CASE WHEN t.kind='jama' THEN t.amount_paise ELSE 0 END),0) AS b
          FROM customers c LEFT JOIN transactions t ON t.customer_id=c.id WHERE c.name=?
        """, (name,)).fetchone()
        return to_rupees(row["b"]) if row else 0.0

    # ---- transactions ------------------------------------------------------
    def add(self, kind: str, amount_rupees: float, name: str | None = None,
            note: str = "", raw_text: str = "", confidence: float = 1.0) -> dict:
        if kind not in KINDS:
            raise ValueError(f"bad kind {kind}")
        if amount_rupees <= 0:
            raise ValueError("amount must be positive")
        cid = self.get_or_create_customer(name) if name else None
        ts = int(time.time())
        cur = self.db.execute(
            "INSERT INTO transactions(ts, customer_id, kind, amount_paise, note, raw_text, confidence) VALUES (?,?,?,?,?,?,?)",
            (ts, cid, kind, to_paise(amount_rupees), note, raw_text, confidence))
        self.db.commit()
        return {"id": int(cur.lastrowid), "ts": ts, "kind": kind, "amount": amount_rupees, "name": name}

    def recent(self, limit: int = 30) -> list[dict]:
        rows = self.db.execute("""
          SELECT t.*, c.name AS customer_name FROM transactions t
          LEFT JOIN customers c ON c.id=t.customer_id ORDER BY t.ts DESC, t.id DESC LIMIT ?
        """, (limit,)).fetchall()
        return [self._row(r) for r in rows]

    def delete(self, tx_id: int) -> bool:
        cur = self.db.execute("DELETE FROM transactions WHERE id=?", (tx_id,))
        self.db.commit()
        return cur.rowcount > 0

    @staticmethod
    def _row(r: sqlite3.Row) -> dict:
        return {"id": r["id"], "ts": r["ts"], "kind": r["kind"], "amount": to_rupees(r["amount_paise"]),
                "name": r["customer_name"], "note": r["note"], "raw_text": r["raw_text"], "confidence": r["confidence"]}

    # ---- hisaab (report) ----------------------------------------------------
    def hisaab(self, day_ts: int | None = None) -> dict:
        """Daily report for the local day containing day_ts (default: today)."""
        import datetime
        d = datetime.datetime.fromtimestamp(day_ts or time.time())
        start = int(datetime.datetime(d.year, d.month, d.day).timestamp())
        end = start + 86400
        rows = self.db.execute("""
          SELECT kind, SUM(amount_paise) AS s, COUNT(*) AS n FROM transactions
          WHERE ts>=? AND ts<? GROUP BY kind
        """, (start, end)).fetchall()
        by = {r["kind"]: (to_rupees(r["s"]), r["n"]) for r in rows}
        udhaar = by.get("udhaar_diya", (0.0, 0))
        jama = by.get("jama", (0.0, 0))
        bikri = by.get("bikri", (0.0, 0))
        kharcha = by.get("kharcha", (0.0, 0))
        return {
            "date": d.strftime("%Y-%m-%d"),
            "udhaar_diya": udhaar[0], "udhaar_count": udhaar[1],
            "jama": jama[0], "jama_count": jama[1],
            "bikri": bikri[0], "bikri_count": bikri[1],
            "kharcha": kharcha[0], "kharcha_count": kharcha[1],
            "net_cash": bikri[0] + jama[0] - kharcha[0],   # cash in (sales + collections) - expenses
            "total_outstanding": self.total_outstanding(),
        }

    def total_outstanding(self) -> float:
        row = self.db.execute("""
          SELECT COALESCE(SUM(CASE WHEN kind='udhaar_diya' THEN amount_paise ELSE -amount_paise END),0) AS b
          FROM transactions WHERE kind IN ('udhaar_diya','jama')
        """).fetchone()
        return to_rupees(row["b"])
