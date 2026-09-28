"""SQLite: задания, заказы, пакеты, разблокировки, события. Один файл, режим WAL."""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

from . import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    created_at REAL NOT NULL,
    status TEXT NOT NULL,            -- queued | processing | done | failed | expired
    progress INTEGER NOT NULL DEFAULT 0,
    stage TEXT,
    error TEXT,
    filename TEXT,
    source_path TEXT NOT NULL,
    target REAL NOT NULL,
    options TEXT NOT NULL,
    ip TEXT,
    device TEXT,
    parent_id TEXT,
    entitlement TEXT,                -- заказ, дающий бесплатную пересборку
    attempts INTEGER NOT NULL DEFAULT 0,
    started_at REAL,
    finished_at REAL,
    meta TEXT
);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status, created_at);
CREATE INDEX IF NOT EXISTS jobs_ip ON jobs(ip, created_at);

CREATE TABLE IF NOT EXISTS orders (
    id TEXT PRIMARY KEY,
    token TEXT NOT NULL,
    created_at REAL NOT NULL,
    product TEXT NOT NULL,           -- single | pack
    amount INTEGER NOT NULL,
    status TEXT NOT NULL,            -- pending | paid | canceled
    job_id TEXT NOT NULL,
    variant INTEGER NOT NULL,
    email TEXT,
    provider TEXT NOT NULL,
    provider_payment_id TEXT,
    confirmation_url TEXT,
    checked_at REAL,
    paid_at REAL,
    pack_code TEXT
);
CREATE INDEX IF NOT EXISTS orders_pid ON orders(provider_payment_id);

CREATE TABLE IF NOT EXISTS packs (
    code TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    order_id TEXT NOT NULL,
    total INTEGER NOT NULL,
    remaining INTEGER NOT NULL,
    email TEXT
);

CREATE TABLE IF NOT EXISTS unlocks (
    job_id TEXT NOT NULL,
    variant INTEGER NOT NULL,
    created_at REAL NOT NULL,
    source TEXT NOT NULL,            -- order:<id> | pack:<code> | rebuild:<order>
    download_token TEXT NOT NULL UNIQUE,
    PRIMARY KEY (job_id, variant)
);

CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    name TEXT NOT NULL,
    job_id TEXT,
    device TEXT,
    ip TEXT,
    props TEXT
);
CREATE INDEX IF NOT EXISTS events_ts ON events(ts, name);

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts REAL NOT NULL,
    job_id TEXT NOT NULL,
    variant INTEGER,
    rating TEXT NOT NULL,            -- ready | needs_fix | bad
    comment TEXT
);
"""

_local = threading.local()


def connect() -> sqlite3.Connection:
    path = config.settings.db_path
    conn = getattr(_local, "conn", None)
    if conn is None or getattr(_local, "path", None) != path:
        import os

        os.makedirs(os.path.dirname(path), exist_ok=True)
        conn = sqlite3.connect(path, timeout=30, isolation_level=None, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=30000")
        conn.executescript(SCHEMA)
        _local.conn, _local.path = conn, path
    return conn


@contextmanager
def tx() -> Iterator[sqlite3.Connection]:
    conn = connect()
    conn.execute("BEGIN IMMEDIATE")
    try:
        yield conn
        conn.execute("COMMIT")
    except BaseException:
        conn.execute("ROLLBACK")
        raise


def one(sql: str, *args: Any) -> sqlite3.Row | None:
    return connect().execute(sql, args).fetchone()


def all_(sql: str, *args: Any) -> list[sqlite3.Row]:
    return connect().execute(sql, args).fetchall()


def run(sql: str, *args: Any) -> sqlite3.Cursor:
    return connect().execute(sql, args)


def event(name: str, job_id: str | None = None, device: str | None = None, ip: str | None = None,
          **props: Any) -> None:
    run("INSERT INTO events (ts, name, job_id, device, ip, props) VALUES (?,?,?,?,?,?)",
        time.time(), name, job_id, device, ip, json.dumps(props, ensure_ascii=False) if props else None)
