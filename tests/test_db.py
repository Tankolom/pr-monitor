import unittest
import sys
import os
import tempfile
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mention_monitor.db import (
    backup_database,
    connect,
    create_session,
    dashboard_stats,
    delete_session,
    latest_mentions,
    insert_mention,
    password_hash,
    purge_expired_sessions,
    reset_stale_collection_runs,
    verify_password,
    authenticate_user,
    get_user_by_username,
)


def _mention(**kwargs):
    base = {
        "project": "Тест",
        "query": "тест",
        "title": "Заголовок теста",
        "snippet": "Краткое описание",
        "text": "Полный текст новости для теста",
        "url": "https://example.com/news/1",
        "source": "example.com",
        "published_at": "2026-06-01T10:00:00+00:00",
        "collected_at": "2026-06-01T12:00:00+00:00",
        "sentiment": "neutral",
        "sentiment_score": 0.0,
        "language": "ru",
        "entities": [],
        "raw_path": None,
        "content_hash": "abc123",
        "likes": 0,
        "reposts": 0,
        "comments": 0,
        "views": 0,
    }
    base.update(kwargs)
    return base


class TestConnect(unittest.TestCase):
    def test_creates_tables(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            conn = connect(db_path)
            tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
            self.assertIn("mentions", tables)
            self.assertIn("users", tables)
            self.assertIn("sessions", tables)
            conn.close()
        finally:
            os.unlink(db_path)


class TestInsertMention(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.conn = connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_insert_new(self):
        result = insert_mention(self.conn, _mention())
        self.assertTrue(result)
        count = self.conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
        self.assertEqual(count, 1)

    def test_deduplication_by_content_hash(self):
        m = _mention(content_hash="unique-hash-xyz")
        first = insert_mention(self.conn, m)
        second = insert_mention(self.conn, m)
        self.assertTrue(first)
        self.assertFalse(second)
        count = self.conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
        self.assertEqual(count, 1)

    def test_dedup_updates_engagement(self):
        insert_mention(self.conn, _mention(content_hash="hash1", views=10))
        insert_mention(self.conn, _mention(content_hash="hash1", views=500))
        row = self.conn.execute("SELECT views FROM mentions WHERE content_hash='hash1'").fetchone()
        self.assertEqual(row[0], 500)

    def test_different_hashes_both_inserted(self):
        insert_mention(self.conn, _mention(content_hash="hash-a", url="https://example.com/1"))
        insert_mention(self.conn, _mention(content_hash="hash-b", url="https://example.com/2"))
        count = self.conn.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
        self.assertEqual(count, 2)


class TestPasswordAuth(unittest.TestCase):
    def test_hash_and_verify(self):
        h = password_hash("secret123")
        self.assertTrue(verify_password("secret123", h))

    def test_wrong_password_fails(self):
        h = password_hash("secret123")
        self.assertFalse(verify_password("wrongpass", h))

    def test_authenticate_default_admin(self):
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        try:
            conn = connect(db_path)
            # default admin создаётся в ensure_default_admin
            user = get_user_by_username(conn, "admin")
            self.assertIsNotNone(user)
            self.assertEqual(user["role"], "admin")
            conn.close()
        finally:
            os.unlink(db_path)


class TestMaintenanceHelpers(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.tmp.name
        self.conn = connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_backup_database_creates_copy(self):
        insert_mention(self.conn, _mention(content_hash="backup-check"))
        with tempfile.TemporaryDirectory() as tmpdir:
            path = backup_database(self.db_path, tmpdir, keep=2)
            self.assertTrue(os.path.exists(path))
            copy = sqlite3.connect(path)
            try:
                count = copy.execute("SELECT COUNT(*) FROM mentions").fetchone()[0]
                self.assertEqual(count, 1)
            finally:
                copy.close()

    def test_purge_expired_sessions_removes_only_old(self):
        user = get_user_by_username(self.conn, "admin")
        token = create_session(self.conn, user["id"], days=1)
        self.conn.execute(
            "INSERT INTO sessions (token, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            ("expired-token", user["id"], "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"),
        )
        self.conn.commit()
        removed = purge_expired_sessions(self.conn)
        self.assertEqual(removed, 1)
        self.assertIsNotNone(self.conn.execute("SELECT token FROM sessions WHERE token=?", (token,)).fetchone())
        self.assertIsNone(self.conn.execute("SELECT token FROM sessions WHERE token='expired-token'").fetchone())

    def test_reset_stale_collection_runs_marks_old_running_failed(self):
        self.conn.execute(
            "INSERT INTO collection_runs (started_at, status) VALUES (?, ?)",
            ("2026-01-01T00:00:00+00:00", "running"),
        )
        self.conn.commit()
        updated = reset_stale_collection_runs(self.conn, older_than_minutes=1)
        self.assertEqual(updated, 1)
        row = self.conn.execute("SELECT status, error, finished_at FROM collection_runs ORDER BY id DESC LIMIT 1").fetchone()
        self.assertEqual(row["status"], "failed")
        self.assertTrue(row["error"])
        self.assertTrue(row["finished_at"])

    def test_latest_mentions_supports_offset(self):
        insert_mention(self.conn, _mention(content_hash="page-1", url="https://example.com/1", title="1"))
        insert_mention(self.conn, _mention(content_hash="page-2", url="https://example.com/2", title="2", collected_at="2026-06-01T12:01:00+00:00"))
        first = latest_mentions(self.conn, limit=1, offset=0)
        second = latest_mentions(self.conn, limit=1, offset=1)
        self.assertEqual(len(first), 1)
        self.assertEqual(len(second), 1)
        self.assertNotEqual(first[0]["content_hash"], second[0]["content_hash"])

    def test_period_filter_uses_published_at_when_available(self):
        insert_mention(
            self.conn,
            _mention(
                content_hash="old-published-new-collected",
                url="https://example.com/old",
                title="old",
                published_at="2019-05-10T10:00:00+00:00",
                collected_at="2026-06-10T12:00:00+00:00",
            ),
        )
        insert_mention(
            self.conn,
            _mention(
                content_hash="fresh-published",
                url="https://example.com/fresh",
                title="fresh",
                published_at="2026-06-09T10:00:00+00:00",
                collected_at="2026-06-10T12:01:00+00:00",
            ),
        )
        rows = latest_mentions(
            self.conn,
            collected_from="2026-06-01",
            collected_to="2026-06-30",
        )
        hashes = {row["content_hash"] for row in rows}
        self.assertIn("fresh-published", hashes)
        self.assertNotIn("old-published-new-collected", hashes)

    def test_dashboard_stats_total_uses_effective_publication_date(self):
        insert_mention(
            self.conn,
            _mention(
                content_hash="stats-old",
                url="https://example.com/stats-old",
                published_at="2019-01-01T00:00:00+00:00",
                collected_at="2026-06-10T12:00:00+00:00",
            ),
        )
        insert_mention(
            self.conn,
            _mention(
                content_hash="stats-new",
                url="https://example.com/stats-new",
                published_at="2026-06-12T00:00:00+00:00",
                collected_at="2026-06-12T10:00:00+00:00",
            ),
        )
        stats = dashboard_stats(
            self.conn,
            collected_from="2026-06-01",
            collected_to="2026-06-30",
        )
        self.assertEqual(stats["total"], 1)


if __name__ == "__main__":
    unittest.main()
