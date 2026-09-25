"""SQLite: заказы, платежи (для идемпотентности) и события воронки без персональных данных."""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
from datetime import datetime, timedelta, timezone

SCHEMA = """
CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'new',          -- new | pending | paid | refunded
    price_rub INTEGER NOT NULL,
    data_json TEXT NOT NULL,
    email TEXT NOT NULL,
    payment_id TEXT,
    paid_at TEXT,
    downloads INTEGER NOT NULL DEFAULT 0,
    utm_source TEXT,
    utm_medium TEXT,
    utm_campaign TEXT,
    demo INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    provider TEXT NOT NULL,
    external_id TEXT NOT NULL,
    amount REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    UNIQUE (provider, external_id)
);
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    name TEXT NOT NULL,
    order_ref TEXT,
    utm_source TEXT,
    utm_campaign TEXT
);
CREATE INDEX IF NOT EXISTS events_ts ON events (ts);
"""

EVENT_NAMES = {
    "view_landing", "view_sample", "view_form", "order_created", "order_updated", "view_preview",
    "pay_click", "payment_created", "payment_error", "payment_succeeded", "download", "form_invalid",
}

_lock = threading.Lock()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def order_ref(token: str) -> str:
    """Короткий необратимый идентификатор заказа для аналитики (сам токен — ключ доступа)."""
    return hashlib.sha256(token.encode()).hexdigest()[:12]


class Store:
    def __init__(self, path: str):
        if path != ":memory:":
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    # --- заказы -----------------------------------------------------------
    def create_order(self, token: str, data: dict, price: int, utm: dict, demo: bool) -> None:
        ts = now_iso()
        with _lock:
            self.conn.execute(
                "INSERT INTO orders (token, created_at, updated_at, price_rub, data_json, email, utm_source, utm_medium, utm_campaign, demo)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (token, ts, ts, price, json.dumps(data, ensure_ascii=False), data["email"],
                 utm.get("utm_source"), utm.get("utm_medium"), utm.get("utm_campaign"), int(demo)),
            )
            self.conn.commit()

    def update_order_data(self, token: str, data: dict) -> bool:
        with _lock:
            cur = self.conn.execute(
                "UPDATE orders SET data_json=?, email=?, updated_at=? WHERE token=? AND status IN ('new','pending')",
                (json.dumps(data, ensure_ascii=False), data["email"], now_iso(), token),
            )
            self.conn.commit()
            return cur.rowcount == 1

    def get_order(self, token: str) -> dict | None:
        row = self.conn.execute("SELECT * FROM orders WHERE token=?", (token,)).fetchone()
        if not row:
            return None
        order = dict(row)
        order["data"] = json.loads(order.pop("data_json"))
        return order

    def set_payment_pending(self, token: str, payment_id: str) -> None:
        with _lock:
            self.conn.execute(
                "UPDATE orders SET status='pending', payment_id=?, updated_at=? WHERE token=? AND status IN ('new','pending')",
                (payment_id, now_iso(), token),
            )
            self.conn.commit()

    def reset_payment(self, token: str) -> None:
        with _lock:
            self.conn.execute(
                "UPDATE orders SET status='new', payment_id=NULL, updated_at=? WHERE token=? AND status='pending'",
                (now_iso(), token),
            )
            self.conn.commit()

    def mark_paid(self, token: str, provider: str, external_id: str, amount: float) -> bool:
        """Идемпотентно помечает заказ оплаченным. True — если оплата применена сейчас."""
        with _lock:
            order = self.conn.execute("SELECT id, status FROM orders WHERE token=?", (token,)).fetchone()
            if not order:
                return False
            try:
                self.conn.execute(
                    "INSERT INTO payments (order_id, provider, external_id, amount, status, created_at) VALUES (?,?,?,?,?,?)",
                    (order["id"], provider, external_id, amount, "succeeded", now_iso()),
                )
            except sqlite3.IntegrityError:
                self.conn.rollback()
                return False
            self.conn.execute(
                "UPDATE orders SET status='paid', paid_at=?, payment_id=?, updated_at=? WHERE id=?",
                (now_iso(), external_id, now_iso(), order["id"]),
            )
            self.conn.commit()
            return True

    def count_download(self, token: str) -> None:
        with _lock:
            self.conn.execute("UPDATE orders SET downloads = downloads + 1 WHERE token=?", (token,))
            self.conn.commit()

    def purge_unpaid(self, older_than_days: int) -> int:
        """Удаляет неоплаченные заказы (и анкеты в них) старше N дней — минимизация данных."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=older_than_days)).isoformat(timespec="seconds")
        with _lock:
            cur = self.conn.execute("DELETE FROM orders WHERE status IN ('new','pending') AND created_at < ?", (cutoff,))
            self.conn.commit()
            return cur.rowcount

    # --- события ----------------------------------------------------------
    def log_event(self, name: str, token: str | None = None, utm: dict | None = None) -> None:
        if name not in EVENT_NAMES:
            raise ValueError(f"unknown event {name}")
        utm = utm or {}
        with _lock:
            self.conn.execute(
                "INSERT INTO events (ts, name, order_ref, utm_source, utm_campaign) VALUES (?,?,?,?,?)",
                (now_iso(), name, order_ref(token) if token else None, utm.get("utm_source"), utm.get("utm_campaign")),
            )
            self.conn.commit()

    def funnel(self, days: int = 30) -> list[dict]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
        rows = self.conn.execute(
            "SELECT COALESCE(utm_source,'(прямой)') AS src, name, COUNT(*) AS n,"
            " COUNT(DISTINCT order_ref) AS uniq FROM events WHERE ts >= ? GROUP BY src, name ORDER BY src, name",
            (cutoff,),
        ).fetchall()
        return [dict(r) for r in rows]

    def recent_orders(self, limit: int = 50) -> list[dict]:
        rows = self.conn.execute(
            "SELECT created_at, status, price_rub, email, utm_source, utm_campaign, downloads, demo, payment_id"
            " FROM orders ORDER BY id DESC LIMIT ?", (limit,),
        ).fetchall()
        return [dict(r) for r in rows]

    def revenue(self, days: int = 30) -> dict:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat(timespec="seconds")
        row = self.conn.execute(
            "SELECT COUNT(*) AS n, COALESCE(SUM(price_rub),0) AS rub FROM orders WHERE status='paid' AND demo=0 AND paid_at >= ?",
            (cutoff,),
        ).fetchone()
        return dict(row)
