from __future__ import annotations

import json
import hashlib
import hmac
import os
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .logging_utils import get_logger

LOGGER = get_logger(__name__)


SCHEMA = """
CREATE TABLE IF NOT EXISTS mentions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project TEXT NOT NULL,
    query TEXT NOT NULL,
    title TEXT NOT NULL,
    snippet TEXT,
    text TEXT,
    url TEXT NOT NULL,
    source TEXT,
    published_at TEXT,
    collected_at TEXT NOT NULL,
    sentiment TEXT NOT NULL,
    sentiment_score REAL NOT NULL DEFAULT 0,
    sentiment_source TEXT NOT NULL DEFAULT 'rule',
    relevant INTEGER NOT NULL DEFAULT 1,
    relevance_source TEXT NOT NULL DEFAULT 'pending',
    language TEXT,
    entities TEXT,
    raw_path TEXT,
    content_hash TEXT NOT NULL UNIQUE,
    likes INTEGER NOT NULL DEFAULT 0,
    reposts INTEGER NOT NULL DEFAULT 0,
    comments INTEGER NOT NULL DEFAULT 0,
    views INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_mentions_project ON mentions(project);
CREATE INDEX IF NOT EXISTS idx_mentions_collected ON mentions(collected_at);
CREATE INDEX IF NOT EXISTS idx_mentions_sentiment ON mentions(sentiment);
CREATE INDEX IF NOT EXISTS idx_mentions_source ON mentions(source);

CREATE TABLE IF NOT EXISTS collection_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    found INTEGER NOT NULL DEFAULT 0,
    inserted INTEGER NOT NULL DEFAULT 0,
    error TEXT
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE,
    email_verified INTEGER NOT NULL DEFAULT 1,
    role TEXT NOT NULL DEFAULT 'user',
    full_name TEXT,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE TABLE IF NOT EXISTS sessions (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires ON sessions(expires_at);

CREATE TABLE IF NOT EXISTS email_verification_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_user ON email_verification_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_email_verification_tokens_expires ON email_verification_tokens(expires_at);

CREATE TABLE IF NOT EXISTS password_reset_tokens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    email TEXT NOT NULL,
    token_hash TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    consumed_at TEXT,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_user ON password_reset_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_password_reset_tokens_expires ON password_reset_tokens(expires_at);

CREATE TABLE IF NOT EXISTS ai_audits (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    created_at TEXT NOT NULL,
    provider TEXT,
    model TEXT,
    checked INTEGER NOT NULL DEFAULT 0,
    agreement REAL,
    mismatches TEXT,
    verdict TEXT,
    details TEXT,
    status TEXT NOT NULL DEFAULT 'ok',
    message TEXT
);

CREATE INDEX IF NOT EXISTS idx_ai_audits_created ON ai_audits(created_at);

CREATE TABLE IF NOT EXISTS source_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER,
    created_at TEXT NOT NULL,
    report TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_source_reports_created ON source_reports(created_at);

CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'trial',
    status TEXT NOT NULL DEFAULT 'trial',
    period_end TEXT,
    quota_projects INTEGER,
    quota_queries INTEGER,
    quota_users INTEGER,
    collection_interval_hours INTEGER,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    queries TEXT NOT NULL DEFAULT '[]',
    control_urls TEXT NOT NULL DEFAULT '[]',
    brand TEXT,
    relevance_hint TEXT,
    language TEXT NOT NULL DEFAULT 'ru',
    region TEXT NOT NULL DEFAULT 'RU',
    owner TEXT,
    schedule_enabled INTEGER NOT NULL DEFAULT 0,
    schedule_interval_hours INTEGER NOT NULL DEFAULT 3,
    last_collected_at TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_projects_account ON projects(account_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_projects_account_name ON projects(account_id, name);

CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER NOT NULL,
    provider TEXT NOT NULL DEFAULT 'manual',
    external_id TEXT,
    amount REAL,
    currency TEXT NOT NULL DEFAULT 'RUB',
    plan TEXT,
    period_months INTEGER,
    status TEXT NOT NULL DEFAULT 'succeeded',
    note TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_payments_account ON payments(account_id);
-- Платёж провайдера зачитывается ровно один раз (защита от двойного вебхука).
-- Частичный индекс: ручные платежи (external_id IS NULL) не ограничиваем.
CREATE UNIQUE INDEX IF NOT EXISTS idx_payments_external ON payments(provider, external_id) WHERE external_id IS NOT NULL;
"""


_INITIALIZED_DBS: set[str] = set()


def connect(db_path: str) -> sqlite3.Connection:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    # Схема и дефолтный админ создаются один раз на процесс, а не на каждый запрос —
    # иначе обычное чтение (рендер страниц) делает лишние записи и упирается в lock SQLite.
    if db_path not in _INITIALIZED_DBS:
        init_database(conn)
        _INITIALIZED_DBS.add(db_path)
    return conn


def init_database(conn: sqlite3.Connection) -> None:
    """Однократная инициализация: схема, миграции колонок, дефолтный админ."""
    conn.executescript(SCHEMA)
    ensure_schema(conn)
    ensure_default_admin(conn)


def backup_database(db_path: str, backup_dir: str, keep: int = 14) -> str:
    source = connect(db_path)
    try:
        target_dir = Path(backup_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        backup_path = target_dir / f"mentions-{stamp}.db"
        dest = sqlite3.connect(str(backup_path))
        try:
            source.backup(dest)
        finally:
            dest.close()
        backups = sorted(target_dir.glob("mentions-*.db"), reverse=True)
        for old in backups[max(int(keep), 1):]:
            try:
                old.unlink()
            except OSError:
                pass
        return str(backup_path)
    finally:
        source.close()


def ensure_schema(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(mentions)").fetchall()}
    for name in ["likes", "reposts", "comments", "views"]:
        if name not in existing:
            conn.execute(f"ALTER TABLE mentions ADD COLUMN {name} INTEGER NOT NULL DEFAULT 0")
    if "sentiment_source" not in existing:
        conn.execute("ALTER TABLE mentions ADD COLUMN sentiment_source TEXT NOT NULL DEFAULT 'rule'")
    if "relevant" not in existing:
        conn.execute("ALTER TABLE mentions ADD COLUMN relevant INTEGER NOT NULL DEFAULT 1")
    if "relevance_source" not in existing:
        conn.execute("ALTER TABLE mentions ADD COLUMN relevance_source TEXT NOT NULL DEFAULT 'pending'")
    audit_cols = {row["name"] for row in conn.execute("PRAGMA table_info(ai_audits)").fetchall()}
    if audit_cols and "details" not in audit_cols:
        conn.execute("ALTER TABLE ai_audits ADD COLUMN details TEXT")
    user_cols = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    if "email" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    if "email_verified" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN email_verified INTEGER NOT NULL DEFAULT 1")
    if "account_id" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN account_id INTEGER")
    if "is_superadmin" not in user_cols:
        conn.execute("ALTER TABLE users ADD COLUMN is_superadmin INTEGER NOT NULL DEFAULT 0")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email ON users(email)")
    # account_id на упоминаниях — для изоляции данных между клиентами (мультитенант)
    if "account_id" not in existing:
        conn.execute("ALTER TABLE mentions ADD COLUMN account_id INTEGER")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_mentions_account ON mentions(account_id)")
    conn.commit()


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def password_hash(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256$120000${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, iterations, salt, digest = stored_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        candidate = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations),
        ).hex()
        return hmac.compare_digest(candidate, digest)
    except Exception:
        return False


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def token_hash(token: str) -> str:
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def ensure_default_admin(conn: sqlite3.Connection) -> None:
    count = conn.execute("SELECT COUNT(*) AS n FROM users").fetchone()["n"]
    if count:
        return
    username = (os.getenv("MENTION_MONITOR_ADMIN_USER") or os.getenv("MENTION_MONITOR_USER") or "admin").strip() or "admin"
    # Никакого предсказуемого дефолта: пароль берётся из окружения, иначе генерируется
    # случайный и однократно пишется в лог — оператор забирает его оттуда.
    password = os.getenv("MENTION_MONITOR_ADMIN_PASSWORD") or os.getenv("MENTION_MONITOR_PASSWORD") or ""
    generated = False
    if not password:
        password = secrets.token_urlsafe(15)
        generated = True
    full_name = os.getenv("MENTION_MONITOR_ADMIN_NAME") or "Администратор"
    conn.execute(
        """
        INSERT INTO users (username, password_hash, role, full_name, is_active, is_superadmin, created_at)
        VALUES (?, ?, 'admin', ?, 1, 1, ?)
        """,
        (username, password_hash(password), full_name, utc_now()),
    )
    conn.commit()
    if generated:
        LOGGER.warning(
            "Создан первичный администратор «%s» со СЛУЧАЙНЫМ паролем: %s — смените после входа. "
            "Чтобы задать свой, укажите MENTION_MONITOR_ADMIN_PASSWORD в окружении.",
            username, password,
        )


def uses_default_admin_password(conn: sqlite3.Connection) -> bool:
    admin = get_user_by_username(conn, "admin")
    if not admin:
        return False
    return verify_password("admin12345", admin["password_hash"])


def get_user_by_username(conn: sqlite3.Connection, username: str):
    return conn.execute("SELECT * FROM users WHERE username = ?", (username.strip(),)).fetchone()


def get_user_by_email(conn: sqlite3.Connection, email: str):
    normalized = normalize_email(email)
    if not normalized:
        return None
    return conn.execute("SELECT * FROM users WHERE lower(COALESCE(email, '')) = ?", (normalized,)).fetchone()


def get_user_by_login(conn: sqlite3.Connection, login: str):
    login = (login or "").strip()
    if not login:
        return None
    return conn.execute(
        """
        SELECT * FROM users
        WHERE lower(username) = lower(?) OR lower(COALESCE(email, '')) = lower(?)
        LIMIT 1
        """,
        (login, login),
    ).fetchone()


def get_user_by_id(conn: sqlite3.Connection, user_id: int):
    return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def authenticate_user(conn: sqlite3.Connection, username: str, password: str):
    user = get_user_by_login(conn, username)
    if not user or not user["is_active"]:
        return None
    if verify_password(password, user["password_hash"]):
        return user
    return None


def list_users(conn: sqlite3.Connection):
    return conn.execute(
        "SELECT id, username, email, email_verified, role, full_name, is_active, created_at FROM users ORDER BY created_at DESC"
    ).fetchall()


def create_user(
    conn: sqlite3.Connection,
    username: str,
    password: str,
    role: str = "user",
    full_name: str = "",
    email: str = "",
    email_verified: bool = True,
) -> int:
    role = role if role in {"admin", "user"} else "user"
    normalized_email = normalize_email(email)
    cursor = conn.execute(
        """
        INSERT INTO users (username, password_hash, email, email_verified, role, full_name, is_active, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 1, ?)
        """,
        (
            username.strip(),
            password_hash(password),
            normalized_email or None,
            1 if email_verified or not normalized_email else 0,
            role,
            full_name.strip(),
            utc_now(),
        ),
    )
    conn.commit()
    return int(cursor.lastrowid)


def create_public_user(conn: sqlite3.Connection, email: str, password: str, full_name: str = "") -> int:
    """Публичная регистрация = новый тенант: создаём триал-аккаунт и делаем
    зарегистрировавшегося его администратором (управляет проектами, биллингом, командой)."""
    normalized_email = normalize_email(email)
    account_id = create_account(conn, (full_name or normalized_email or "Аккаунт"), plan="trial")
    user_id = create_user(
        conn,
        username=normalized_email,
        password=password,
        role="admin",
        full_name=full_name,
        email=normalized_email,
        email_verified=False,
    )
    conn.execute("UPDATE users SET account_id = ? WHERE id = ?", (account_id, user_id))
    conn.commit()
    return user_id


def update_user_profile(conn: sqlite3.Connection, user_id: int, full_name: str = "", email: str = "") -> None:
    normalized_email = normalize_email(email)
    conn.execute(
        """
        UPDATE users
        SET full_name = ?, email = ?, username = COALESCE(NULLIF(username, ''), ?)
        WHERE id = ?
        """,
        (full_name.strip(), normalized_email or None, normalized_email or "", user_id),
    )
    conn.commit()


def update_user(conn: sqlite3.Connection, user_id: int, role: str, is_active: bool) -> None:
    role = role if role in {"admin", "user"} else "user"
    conn.execute(
        "UPDATE users SET role = ?, is_active = ? WHERE id = ?",
        (role, 1 if is_active else 0, user_id),
    )
    conn.commit()


def update_user_password(conn: sqlite3.Connection, user_id: int, password: str) -> None:
    conn.execute("UPDATE users SET password_hash = ? WHERE id = ?", (password_hash(password), user_id))
    conn.commit()


def mark_user_email_verified(conn: sqlite3.Connection, user_id: int) -> None:
    conn.execute("UPDATE users SET email_verified = 1 WHERE id = ?", (user_id,))
    conn.commit()


def _issue_token(
    conn: sqlite3.Connection,
    table: str,
    user_id: int,
    email: str,
    expires_in_hours: int,
) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(hours=max(expires_in_hours, 1))
    conn.execute(f"DELETE FROM {table} WHERE user_id = ? AND consumed_at IS NULL", (user_id,))
    conn.execute(
        f"""
        INSERT INTO {table} (user_id, email, token_hash, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, normalize_email(email), token_hash(token), now.isoformat(), expires_at.isoformat()),
    )
    conn.commit()
    return token


def create_email_verification_token(conn: sqlite3.Connection, user_id: int, email: str, expires_in_hours: int = 72) -> str:
    return _issue_token(conn, "email_verification_tokens", user_id, email, expires_in_hours)


def create_password_reset_token(conn: sqlite3.Connection, user_id: int, email: str, expires_in_hours: int = 2) -> str:
    return _issue_token(conn, "password_reset_tokens", user_id, email, expires_in_hours)


def _consume_token(conn: sqlite3.Connection, table: str, token: str):
    hashed = token_hash(token)
    row = conn.execute(
        f"""
        SELECT t.*, u.username, u.email, u.full_name, u.is_active, u.email_verified
        FROM {table} t
        JOIN users u ON u.id = t.user_id
        WHERE t.token_hash = ? AND t.consumed_at IS NULL AND t.expires_at > ?
        LIMIT 1
        """,
        (hashed, utc_now()),
    ).fetchone()
    if not row:
        return None
    conn.execute(f"UPDATE {table} SET consumed_at = ? WHERE id = ?", (utc_now(), row["id"]))
    conn.commit()
    return row


def consume_email_verification_token(conn: sqlite3.Connection, token: str):
    return _consume_token(conn, "email_verification_tokens", token)


def consume_password_reset_token(conn: sqlite3.Connection, token: str):
    return _consume_token(conn, "password_reset_tokens", token)


def has_valid_password_reset_token(conn: sqlite3.Connection, token: str) -> bool:
    row = conn.execute(
        """
        SELECT 1
        FROM password_reset_tokens
        WHERE token_hash = ? AND consumed_at IS NULL AND expires_at > ?
        LIMIT 1
        """,
        (token_hash(token), utc_now()),
    ).fetchone()
    return bool(row)


def create_session(conn: sqlite3.Connection, user_id: int, days: int = 30) -> str:
    token = secrets.token_urlsafe(32)
    now = datetime.now(timezone.utc).replace(microsecond=0)
    expires_at = now + timedelta(days=days)
    conn.execute(
        "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
        (token, user_id, now.isoformat(), expires_at.isoformat()),
    )
    conn.commit()
    return token


def get_session_user(conn: sqlite3.Connection, token: str):
    if not token:
        return None
    row = conn.execute(
        """
        SELECT users.*
        FROM sessions
        JOIN users ON users.id = sessions.user_id
        WHERE sessions.token = ? AND sessions.expires_at > ? AND users.is_active = 1
        """,
        (token, utc_now()),
    ).fetchone()
    return row


def purge_expired_sessions(conn: sqlite3.Connection) -> int:
    cursor = conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (utc_now(),))
    conn.commit()
    return cursor.rowcount


def reset_stale_collection_runs(conn: sqlite3.Connection, older_than_minutes: int = 180) -> int:
    threshold = (datetime.now(timezone.utc) - timedelta(minutes=max(older_than_minutes, 1))).replace(microsecond=0)
    cursor = conn.execute(
        """
        UPDATE collection_runs
        SET finished_at = COALESCE(finished_at, ?),
            status = 'failed',
            error = COALESCE(error, 'Сбор прерван: процесс завершился до фиксации результата')
        WHERE status = 'running' AND started_at < ?
        """,
        (utc_now(), threshold.isoformat()),
    )
    conn.commit()
    return cursor.rowcount


def delete_session(conn: sqlite3.Connection, token: str) -> None:
    if token:
        conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()


def update_mention_sentiment(
    conn: sqlite3.Connection,
    mention_id: int,
    label: str,
    score: float,
    source: str = "ai",
    relevant: bool | None = None,
) -> None:
    if relevant is None:
        conn.execute(
            "UPDATE mentions SET sentiment = ?, sentiment_score = ?, sentiment_source = ? WHERE id = ?",
            (label, score, source, mention_id),
        )
    else:
        conn.execute(
            "UPDATE mentions SET sentiment = ?, sentiment_score = ?, sentiment_source = ?, "
            "relevant = ?, relevance_source = 'ai' WHERE id = ?",
            (label, score, source, 1 if relevant else 0, mention_id),
        )


def count_pending_sentiment(conn: sqlite3.Connection) -> int:
    # 'rule' = тональность ещё не проверена ИИ. 'pending' = релевантность ещё не проверена ИИ.
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM mentions "
        "WHERE COALESCE(sentiment_source, 'rule') = 'rule' "
        "OR COALESCE(relevance_source, 'pending') = 'pending'"
    ).fetchone()
    return row["n"] if row else 0


def count_irrelevant(conn: sqlite3.Connection) -> int:
    row = conn.execute("SELECT COUNT(*) AS n FROM mentions WHERE COALESCE(relevant, 1) = 0").fetchone()
    return row["n"] if row else 0


def mark_sentiment_kept(conn: sqlite3.Connection, mention_ids: list[int]) -> None:
    """Помечает публикации, которые ИИ отказался размечать — чтобы не перепроверять бесконечно."""
    for mid in mention_ids:
        conn.execute(
            "UPDATE mentions SET "
            "sentiment_source = CASE WHEN sentiment_source = 'rule' THEN 'kept' ELSE sentiment_source END, "
            "relevance_source = 'ai' "
            "WHERE id = ?",
            (mid,),
        )


def save_ai_audit(conn: sqlite3.Connection, data: dict) -> int:
    cursor = conn.execute(
        """
        INSERT INTO ai_audits (run_id, created_at, provider, model, checked, agreement, mismatches, verdict, details, status, message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("run_id"),
            data.get("created_at") or utc_now(),
            data.get("provider"),
            data.get("model"),
            int(data.get("checked", 0) or 0),
            data.get("agreement"),
            json.dumps(data.get("mismatches", []), ensure_ascii=False),
            data.get("verdict"),
            json.dumps(data.get("details", []), ensure_ascii=False),
            data.get("status", "ok"),
            data.get("message"),
        ),
    )
    conn.commit()
    return cursor.lastrowid


def latest_ai_audit(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM ai_audits ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    data = dict(row)
    try:
        data["mismatches"] = json.loads(data.get("mismatches") or "[]")
    except (json.JSONDecodeError, TypeError):
        data["mismatches"] = []
    try:
        data["details"] = json.loads(data.get("details") or "[]")
    except (json.JSONDecodeError, TypeError):
        data["details"] = []
    return data


def save_source_report(conn: sqlite3.Connection, run_id: int | None, report: dict) -> int:
    cursor = conn.execute(
        "INSERT INTO source_reports (run_id, created_at, report) VALUES (?, ?, ?)",
        (run_id, utc_now(), json.dumps(report, ensure_ascii=False)),
    )
    conn.commit()
    return cursor.lastrowid


def latest_source_report(conn: sqlite3.Connection) -> dict | None:
    row = conn.execute("SELECT * FROM source_reports ORDER BY id DESC LIMIT 1").fetchone()
    if not row:
        return None
    data = dict(row)
    try:
        data["report"] = json.loads(data.get("report") or "{}")
    except (json.JSONDecodeError, TypeError):
        data["report"] = {}
    return data


def insert_mention(conn: sqlite3.Connection, mention: dict) -> bool:
    fields = [
        "account_id",
        "project",
        "query",
        "title",
        "snippet",
        "text",
        "url",
        "source",
        "published_at",
        "collected_at",
        "sentiment",
        "sentiment_score",
        "language",
        "entities",
        "raw_path",
        "content_hash",
        "likes",
        "reposts",
        "comments",
        "views",
    ]
    payload = dict(mention)
    payload["entities"] = json.dumps(payload.get("entities", []), ensure_ascii=False)
    try:
        conn.execute(
            f"INSERT INTO mentions ({','.join(fields)}) VALUES ({','.join('?' for _ in fields)})",
            [payload.get(field) for field in fields],
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        conn.execute(
            """
            UPDATE mentions
            SET likes = MAX(COALESCE(likes, 0), ?),
                reposts = MAX(COALESCE(reposts, 0), ?),
                comments = MAX(COALESCE(comments, 0), ?),
                views = MAX(COALESCE(views, 0), ?)
            WHERE content_hash = ?
            """,
            (
                int(payload.get("likes") or 0),
                int(payload.get("reposts") or 0),
                int(payload.get("comments") or 0),
                int(payload.get("views") or 0),
                payload.get("content_hash"),
            ),
        )
        conn.commit()
        return False


def _filters(
    sentiment: str | None = None,
    search: str | None = None,
    collected_from: str | None = None,
    collected_to: str | None = None,
    project: str | None = None,
    account_id: int | None = None,
):
    where = ["COALESCE(relevant, 1) = 1"]
    params = []
    effective_dt = _effective_datetime_expr()
    if account_id is not None:
        where.append("account_id = ?")
        params.append(account_id)
    if project and project != "all":
        where.append("project = ?")
        params.append(project)
    if sentiment and sentiment != "all":
        where.append("sentiment = ?")
        params.append(sentiment)
    if search:
        where.append("(title LIKE ? OR snippet LIKE ? OR text LIKE ? OR source LIKE ?)")
        needle = f"%{search}%"
        params.extend([needle, needle, needle, needle])
    if collected_from:
        where.append(f"{effective_dt} >= ?")
        params.append(f"{collected_from}T00:00:00")
    if collected_to:
        where.append(f"{effective_dt} <= ?")
        params.append(f"{collected_to}T23:59:59")
    return where, params


def _effective_datetime_expr() -> str:
    return """
    CASE
      WHEN published_at GLOB '????-??-??*' THEN published_at
      ELSE collected_at
    END
    """


def latest_mentions(
    conn: sqlite3.Connection,
    limit: int = 100,
    offset: int = 0,
    sentiment: str | None = None,
    search: str | None = None,
    collected_from: str | None = None,
    collected_to: str | None = None,
    project: str | None = None,
    account_id: int | None = None,
):
    where, params = _filters(sentiment, search, collected_from, collected_to, project, account_id)
    sql = "SELECT * FROM mentions"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += f" ORDER BY {_effective_datetime_expr()} DESC LIMIT ? OFFSET ?"
    params.extend([limit, max(offset, 0)])
    return conn.execute(sql, params).fetchall()


def _date_expr() -> str:
    return """
    CASE
      WHEN published_at GLOB '????-??-??*' THEN substr(published_at, 1, 10)
      ELSE substr(collected_at, 1, 10)
    END
    """


def trend_mentions(
    conn: sqlite3.Connection,
    bucket: str = "month",
    months: int = 12,
    sentiment: str | None = None,
    search: str | None = None,
    collected_from: str | None = None,
    collected_to: str | None = None,
    project: str | None = None,
    account_id: int | None = None,
):
    bucket = bucket if bucket in {"day", "week", "month"} else "month"
    months = months if months in {1, 3, 6, 12} else 12
    where, params = _filters(sentiment, search, collected_from, collected_to, project, account_id)
    date_expr = _date_expr()
    if bucket == "day":
        period_expr = date_expr
        order_expr = date_expr
    elif bucket == "week":
        period_expr = "strftime('%Y-W%W', " + date_expr + ")"
        order_expr = period_expr
    else:
        period_expr = "substr(" + date_expr + ", 1, 7)"
        order_expr = period_expr
    if not collected_from:
        where.append(date_expr + " >= date('now', ?)")
        params.append(f"-{months} months")
    sql = (
        f"SELECT {period_expr} AS period, COUNT(*) AS n FROM mentions "
        "WHERE "
        + " AND ".join(where)
        + f" GROUP BY period ORDER BY {order_expr} ASC"
    )
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def dashboard_stats(
    conn: sqlite3.Connection,
    sentiment: str | None = None,
    search: str | None = None,
    collected_from: str | None = None,
    collected_to: str | None = None,
    project: str | None = None,
    trend_bucket: str = "month",
    trend_months: int = 12,
    daily_days: int = 14,
    daily_bucket: str = "day",
    account_id: int | None = None,
) -> dict:
    where, params = _filters(sentiment, search, collected_from, collected_to, project, account_id)
    suffix = ""
    if where:
        suffix = " WHERE " + " AND ".join(where)
    total = conn.execute("SELECT COUNT(*) AS n FROM mentions" + suffix, params).fetchone()["n"]
    by_sentiment = {
        row["sentiment"]: row["n"]
        for row in conn.execute("SELECT sentiment, COUNT(*) AS n FROM mentions" + suffix + " GROUP BY sentiment", params)
    }
    by_source = [dict(r) for r in conn.execute(
        "SELECT COALESCE(source, 'unknown') AS source, COUNT(*) AS n FROM mentions"
        + suffix
        + " GROUP BY source ORDER BY n DESC LIMIT 10",
        params,
    ).fetchall()]
    by_project = [dict(r) for r in conn.execute(
        "SELECT project, COUNT(*) AS n FROM mentions" + suffix + " GROUP BY project ORDER BY n DESC",
        params,
    ).fetchall()]
    by_query = [dict(r) for r in conn.execute(
        "SELECT query, COUNT(*) AS n FROM mentions"
        + suffix
        + " GROUP BY query ORDER BY n DESC LIMIT 10",
        params,
    ).fetchall()]
    by_language = [dict(r) for r in conn.execute(
        "SELECT COALESCE(language, 'unknown') AS language, COUNT(*) AS n FROM mentions"
        + suffix
        + " GROUP BY language ORDER BY n DESC LIMIT 10",
        params,
    ).fetchall()]
    unique_sources = conn.execute(
        "SELECT COUNT(DISTINCT COALESCE(source, 'unknown')) AS n FROM mentions" + suffix,
        params,
    ).fetchone()["n"]
    collected_today = conn.execute(
        "SELECT COUNT(*) AS n FROM mentions"
        + (suffix + " AND " if suffix else " WHERE ")
        + "substr(collected_at, 1, 10) = date('now')",
        params,
    ).fetchone()["n"]
    daily_days = daily_days if daily_days in {7, 14, 30, 60, 90} else 90
    daily_where = list(where)
    daily_params = list(params)
    if not collected_from:
        daily_where.append(_date_expr() + " >= date('now', ?)")
        daily_params.append(f"-{daily_days} days")
    daily_suffix = " WHERE " + " AND ".join(daily_where)
    if daily_bucket == "month":
        daily_period = "substr(" + _date_expr() + ", 1, 7)"
    elif daily_bucket == "week":
        daily_period = "strftime('%Y-W%W', " + _date_expr() + ")"
    else:
        daily_period = _date_expr()
        daily_bucket = "day"
    daily = [dict(r) for r in conn.execute(
        f"""
        SELECT {daily_period} AS day, COUNT(*) AS n
        FROM mentions
        """
        + daily_suffix
        + """
        GROUP BY day
        ORDER BY day ASC
        """,
        daily_params,
    ).fetchall()]
    _last_run_row = conn.execute("SELECT * FROM collection_runs ORDER BY id DESC LIMIT 1").fetchone()
    last_run = dict(_last_run_row) if _last_run_row else None
    trend = trend_mentions(
        conn,
        bucket=trend_bucket,
        months=trend_months,
        sentiment=sentiment,
        search=search,
        collected_from=collected_from,
        collected_to=collected_to,
        project=project,
        account_id=account_id,
    )
    return {
        "total": total,
        "by_sentiment": by_sentiment,
        "by_source": by_source,
        "by_project": by_project,
        "by_query": by_query,
        "by_language": by_language,
        "unique_sources": unique_sources,
        "collected_today": collected_today,
        "daily": daily,
        "trend": trend,
        "last_run": last_run,
    }


# ----------------------------------------------------------------------------
# Аккаунты (тенанты), проекты в БД, платежи — основа коммерциализации.
# ----------------------------------------------------------------------------

_ACCOUNT_UPDATABLE = {
    "name", "plan", "status", "period_end",
    "quota_projects", "quota_queries", "quota_users", "collection_interval_hours",
}


def create_account(
    conn: sqlite3.Connection,
    name: str,
    plan: str = "trial",
    status: str | None = None,
    period_end: str | None = "__auto__",
) -> int:
    from .billing import plan_def, trial_period_end
    plan = plan if plan in {"trial", "start", "business", "agency", "enterprise"} else "trial"
    if status is None:
        status = "trial" if plan == "trial" else "active"
    if period_end == "__auto__":
        if plan == "trial":
            period_end = trial_period_end(int(plan_def("trial").get("trial_days", 14)))
        else:
            period_end = None
    cursor = conn.execute(
        "INSERT INTO accounts (name, plan, status, period_end, created_at) VALUES (?, ?, ?, ?, ?)",
        ((name or "Аккаунт").strip() or "Аккаунт", plan, status, period_end, utc_now()),
    )
    conn.commit()
    return int(cursor.lastrowid)


def get_account(conn: sqlite3.Connection, account_id: int | None) -> dict | None:
    if not account_id:
        return None
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    return dict(row) if row else None


def account_usage(conn: sqlite3.Connection, account_id: int) -> dict:
    rows = conn.execute("SELECT queries FROM projects WHERE account_id = ?", (account_id,)).fetchall()
    projects = len(rows)
    queries = 0
    for r in rows:
        try:
            queries += len(json.loads(r["queries"] or "[]"))
        except (json.JSONDecodeError, TypeError):
            pass
    users = conn.execute(
        "SELECT COUNT(*) AS n FROM users WHERE account_id = ? AND is_active = 1", (account_id,)
    ).fetchone()["n"]
    return {"projects": projects, "queries": queries, "users": users}


def account_quota_state(conn: sqlite3.Connection, account_id: int | None) -> dict:
    """Использование и лимиты по каждой размерности (projects/queries/users)
    плюс флаги reached/ratio — для enforcement и индикаторов в UI."""
    from . import billing
    account = get_account(conn, account_id) if account_id else None
    usage = account_usage(conn, account_id) if account_id else {"projects": 0, "queries": 0, "users": 0}
    state = {"account": account, "dimensions": {}}
    for dim in billing.QUOTA_DIMENSIONS:
        limit = billing.effective_quota(account, dim)
        used = usage.get(dim, 0)
        state["dimensions"][dim] = {
            "used": used,
            "limit": limit,
            "reached": billing.quota_reached(limit, used),
            "ratio": billing.usage_ratio(limit, used),
            "remaining": billing.quota_remaining(limit, used),
        }
    state["active"] = billing.account_is_active(account)
    return state


def list_accounts(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute("SELECT * FROM accounts ORDER BY id").fetchall()
    out = []
    for r in rows:
        acc = dict(r)
        acc["usage"] = account_usage(conn, acc["id"])
        out.append(acc)
    return out


def update_account(conn: sqlite3.Connection, account_id: int, **fields) -> None:
    cols = {k: v for k, v in fields.items() if k in _ACCOUNT_UPDATABLE}
    if not cols:
        return
    assignments = ", ".join(f"{k} = ?" for k in cols)
    conn.execute(
        f"UPDATE accounts SET {assignments} WHERE id = ?",
        [*cols.values(), account_id],
    )
    conn.commit()


def record_payment(
    conn: sqlite3.Connection,
    account_id: int,
    amount: float | None,
    plan: str | None = None,
    provider: str = "manual",
    period_months: int | None = None,
    status: str = "succeeded",
    external_id: str | None = None,
    note: str | None = None,
) -> int:
    cursor = conn.execute(
        """
        INSERT INTO payments (account_id, provider, external_id, amount, currency, plan, period_months, status, note, created_at)
        VALUES (?, ?, ?, ?, 'RUB', ?, ?, ?, ?, ?)
        """,
        (account_id, provider, external_id, amount, plan, period_months, status, note, utc_now()),
    )
    conn.commit()
    return int(cursor.lastrowid)


def list_payments(conn: sqlite3.Connection, account_id: int) -> list[dict]:
    rows = conn.execute(
        "SELECT * FROM payments WHERE account_id = ? ORDER BY id DESC", (account_id,)
    ).fetchall()
    return [dict(r) for r in rows]


def list_all_payments(conn: sqlite3.Connection) -> list[dict]:
    """Все платежи с именем аккаунта — для финансовой аналитики."""
    rows = conn.execute(
        """
        SELECT p.*, a.name AS account_name
        FROM payments p LEFT JOIN accounts a ON a.id = p.account_id
        ORDER BY p.id DESC
        """
    ).fetchall()
    return [dict(r) for r in rows]


# --- Проекты в БД (форма dict совместима с прежним config["projects"]) ---

def _project_row_to_dict(row) -> dict:
    def _loads(value, default):
        try:
            return json.loads(value) if value else default
        except (json.JSONDecodeError, TypeError):
            return default
    return {
        "id": row["id"],
        "account_id": row["account_id"],
        "name": row["name"],
        "queries": _loads(row["queries"], []),
        "control_urls": _loads(row["control_urls"], []),
        "brand": _loads(row["brand"], {}),
        "relevance_hint": row["relevance_hint"] or "",
        "language": row["language"] or "ru",
        "region": row["region"] or "RU",
        "owner": row["owner"] or "",
        "schedule_enabled": bool(row["schedule_enabled"]),
        "schedule_interval_hours": row["schedule_interval_hours"] or 3,
        "last_collected_at": row["last_collected_at"],
    }


def list_projects(conn: sqlite3.Connection, account_id: int | None = None) -> list[dict]:
    if account_id is None:
        rows = conn.execute("SELECT * FROM projects ORDER BY account_id, id").fetchall()
    else:
        rows = conn.execute("SELECT * FROM projects WHERE account_id = ? ORDER BY id", (account_id,)).fetchall()
    return [_project_row_to_dict(r) for r in rows]


def get_project(conn: sqlite3.Connection, project_id: int) -> dict | None:
    row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return _project_row_to_dict(row) if row else None


def get_project_by_name(conn: sqlite3.Connection, account_id: int, name: str) -> dict | None:
    row = conn.execute(
        "SELECT * FROM projects WHERE account_id = ? AND name = ?", (account_id, name)
    ).fetchone()
    return _project_row_to_dict(row) if row else None


def _project_unique_name(conn: sqlite3.Connection, account_id: int, requested: str, exclude_id: int | None = None) -> str:
    base = (requested or "Новый проект").strip() or "Новый проект"
    rows = conn.execute(
        "SELECT name FROM projects WHERE account_id = ?" + (" AND id != ?" if exclude_id else ""),
        (account_id, exclude_id) if exclude_id else (account_id,),
    ).fetchall()
    existing = {r["name"] for r in rows}
    if base not in existing:
        return base
    index = 2
    while f"{base} {index}" in existing:
        index += 1
    return f"{base} {index}"


def create_project_row(
    conn: sqlite3.Connection,
    account_id: int,
    name: str,
    queries: list[str] | None = None,
    owner: str = "",
    control_urls: list[str] | None = None,
    brand: dict | None = None,
    relevance_hint: str = "",
    language: str = "ru",
    region: str = "RU",
) -> dict:
    unique = _project_unique_name(conn, account_id, name)
    cursor = conn.execute(
        """
        INSERT INTO projects
          (account_id, name, queries, control_urls, brand, relevance_hint, language, region, owner, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            account_id,
            unique,
            json.dumps([q for q in (queries or []) if str(q).strip()], ensure_ascii=False),
            json.dumps(control_urls or [], ensure_ascii=False),
            json.dumps(brand, ensure_ascii=False) if brand else None,
            relevance_hint or "",
            language or "ru",
            region or "RU",
            owner or "",
            utc_now(),
        ),
    )
    conn.commit()
    return get_project(conn, int(cursor.lastrowid))


_PROJECT_JSON_FIELDS = {"queries", "control_urls", "brand"}
_PROJECT_UPDATABLE = {
    "name", "queries", "control_urls", "brand", "relevance_hint",
    "language", "region", "owner", "schedule_enabled", "schedule_interval_hours",
    "last_collected_at",
}


def update_project_row(conn: sqlite3.Connection, project_id: int, **fields) -> dict | None:
    cols = {k: v for k, v in fields.items() if k in _PROJECT_UPDATABLE}
    if not cols:
        return get_project(conn, project_id)
    prepared = {}
    for key, value in cols.items():
        if key in _PROJECT_JSON_FIELDS:
            prepared[key] = json.dumps(value, ensure_ascii=False) if value is not None else None
        elif key == "schedule_enabled":
            prepared[key] = 1 if value else 0
        else:
            prepared[key] = value
    assignments = ", ".join(f"{k} = ?" for k in prepared)
    conn.execute(
        f"UPDATE projects SET {assignments} WHERE id = ?",
        [*prepared.values(), project_id],
    )
    conn.commit()
    return get_project(conn, project_id)


def delete_project_row(conn: sqlite3.Connection, project_id: int) -> None:
    conn.execute("DELETE FROM projects WHERE id = ?", (project_id,))
    conn.commit()


def due_projects(conn: sqlite3.Connection, now_iso: str | None = None) -> list[dict]:
    """Проекты, которым пора собирать: автосбор включён, интервал истёк (или ещё не собирали),
    и аккаунт активен. Используется планировщиком воркера."""
    from . import billing
    now_iso = now_iso or utc_now()
    now = datetime.fromisoformat(now_iso)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    active_cache: dict[int, bool] = {}
    out = []
    for row in conn.execute("SELECT * FROM projects WHERE schedule_enabled = 1").fetchall():
        project = _project_row_to_dict(row)
        aid = project.get("account_id")
        if aid is not None:
            if aid not in active_cache:
                active_cache[aid] = billing.account_is_active(get_account(conn, aid))
            if not active_cache[aid]:
                continue
        last = project.get("last_collected_at")
        if not last:
            out.append(project)
            continue
        try:
            last_dt = datetime.fromisoformat(last)
            if last_dt.tzinfo is None:
                last_dt = last_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            out.append(project)
            continue
        interval_h = project.get("schedule_interval_hours") or billing.DEFAULT_COLLECTION_INTERVAL
        if (now - last_dt) >= timedelta(hours=interval_h):
            out.append(project)
    return out


def mark_project_collected(conn: sqlite3.Connection, project_id: int, when: str | None = None) -> None:
    conn.execute(
        "UPDATE projects SET last_collected_at = ? WHERE id = ?",
        (when or utc_now(), project_id),
    )
    conn.commit()


def run_startup_migration(config_path: str = "config.json") -> bool:
    """Однократный хук на старте процесса (server/watch/collect): переносит проекты
    из config.json в БД и очищает их в конфиге. Безопасно вызывать многократно."""
    from .config import load_config, save_config
    try:
        config = load_config(config_path)
    except Exception:
        return False
    conn = connect(config["database"])
    try:
        changed = migrate_to_accounts(conn, config)
    finally:
        conn.close()
    if changed:
        save_config(config, config_path)
    return changed


def migrate_to_accounts(conn: sqlite3.Connection, config: dict) -> bool:
    """Однократная миграция к мультитенанту: создаёт платформенный аккаунт владельца,
    привязывает существующих пользователей, переносит проекты из config.json в БД,
    проставляет account_id историческим упоминаниям. Мутирует config (очищает projects)."""
    have = conn.execute("SELECT COUNT(*) AS n FROM accounts").fetchone()["n"]
    if have:
        return False
    now = utc_now()
    cursor = conn.execute(
        "INSERT INTO accounts (name, plan, status, period_end, created_at) VALUES (?, 'enterprise', 'active', NULL, ?)",
        ("Платформа (Килька маркетинг)", now),
    )
    platform_id = int(cursor.lastrowid)
    # все текущие пользователи — в платформенный аккаунт; админы становятся суперадминами
    conn.execute("UPDATE users SET account_id = ? WHERE account_id IS NULL", (platform_id,))
    conn.execute("UPDATE users SET is_superadmin = 1 WHERE role = 'admin'")
    # переносим проекты из конфига в БД под платформенным аккаунтом
    for project in config.get("projects", []):
        name = (project.get("name") or "Проект").strip() or "Проект"
        create_project_row(
            conn,
            account_id=platform_id,
            name=name,
            queries=project.get("queries") or [],
            owner=project.get("owner") or "",
            control_urls=project.get("control_urls") or [],
            brand=project.get("brand") or None,
            relevance_hint=project.get("relevance_hint") or "",
            language=project.get("language") or "ru",
            region=project.get("region") or "RU",
        )
    # исторические упоминания принадлежат платформенному аккаунту
    conn.execute("UPDATE mentions SET account_id = ? WHERE account_id IS NULL", (platform_id,))
    conn.commit()
    # конфиг больше не источник правды по проектам
    config["projects"] = []
    config["_projects_in_db"] = True
    return True
