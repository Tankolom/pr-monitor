import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mention_monitor.ai_audit import _project_context, correct_sentiment
from mention_monitor.db import (
    connect,
    create_account,
    create_project_row,
    get_project_by_name,
    insert_mention,
    list_projects,
)
from mention_monitor.pages import _ai_audit_card, handle_dashboard_project_post, handle_topics_post

ADMIN = {"username": "admin", "role": "admin"}


def _mention(**kwargs):
    base = {
        "project": "сфера",
        "query": "сфера калининград",
        "title": "Заголовок",
        "snippet": "Краткое описание",
        "text": "Полный текст",
        "url": "https://example.com/news/1",
        "source": "example.com",
        "published_at": "2026-06-01T10:00:00+00:00",
        "collected_at": "2026-06-01T12:00:00+00:00",
        "sentiment": "neutral",
        "sentiment_score": 0.0,
        "language": "ru",
        "entities": [],
        "raw_path": None,
        "content_hash": "hash-1",
        "likes": 0,
        "reposts": 0,
        "comments": 0,
        "views": 0,
    }
    base.update(kwargs)
    return base


def _detail(relevant=True, changed=False, project="сфера"):
    return {
        "project": project,
        "title": "Публикация",
        "source": "example.com",
        "rule": "neutral",
        "ai": "positive" if changed else "neutral",
        "changed": changed,
        "relevant": relevant,
        "relevance_changed": not relevant,
    }


def _write_config(path, db_path, project=None):
    project = project or {"name": "сфера", "queries": ["сфера калининград"], "owner": "admin"}
    config = {"database": db_path, "projects": [project]}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, ensure_ascii=False)
    return config


class TestAiAuditCardRelevantOnly(unittest.TestCase):
    """Статистика «уточнено из проверенных» должна считаться только по релевантным."""

    def _audit(self, details):
        return {
            "status": "ok",
            "provider": "claude",
            "checked": len([d for d in details if d["relevant"]]),
            "agreement": 50.0,
            "mismatches": [],
            "details": details,
            "verdict": "",
        }

    def test_scoped_counts_exclude_irrelevant(self):
        details = (
            [_detail(relevant=True, changed=True)] * 3
            + [_detail(relevant=True, changed=False)] * 2
            + [_detail(relevant=False, changed=True)] * 154
        )
        html = _ai_audit_card(self._audit(details), "сфера")
        self.assertIn("из 5 проверенных", html)
        self.assertIn(">3</div>", html)  # уточнено 3, а не 157
        self.assertIn("Показать исключённые как нерелевантные (154)", html)

    def test_global_counts_exclude_irrelevant(self):
        details = [_detail(relevant=True, changed=True), _detail(relevant=False, changed=True)]
        html = _ai_audit_card(self._audit(details), "all")
        self.assertIn("из 1 проверенных", html)
        self.assertIn("Показать исправленные оценки (1)", html)

    def test_legacy_audit_without_details(self):
        audit = {"status": "ok", "provider": "claude", "checked": 7,
                 "agreement": 90.0, "mismatches": [], "details": [], "verdict": ""}
        html = _ai_audit_card(audit, "all")
        self.assertIn("из 7 проверенных", html)


class TestTopicsPostBrandProfile(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        fd, self.cfg_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(self.cfg_path, "w", encoding="utf-8") as fh:
            json.dump({"database": self.db_path}, fh)
        self.conn = connect(self.db_path)
        self.account_id = create_account(self.conn, "Клиент")
        create_project_row(self.conn, self.account_id, "сфера", queries=["сфера калининград"], owner="admin")
        self.user = {"username": "admin", "role": "admin",
                     "account_id": self.account_id, "is_superadmin": 0}

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)
        os.unlink(self.cfg_path)

    def _post(self, **fields):
        form = {
            "action": "save",
            "original_project_name": "сфера",
            "project_name": "сфера",
            "queries": "сфера калининград",
            "control_urls": "",
        }
        form.update(fields)
        handle_topics_post(self.cfg_path, urlencode(form).encode(), self.user)
        return get_project_by_name(self.conn, self.account_id, "сфера")

    def test_brand_profile_roundtrip(self):
        project = self._post(
            brand_form="1",
            brand_website="smartoffice39.ru",
            brand_city="Калининград",
            brand_industry="коворкинг",
            brand_social_links="https://vk.com/smartoffice39",
            relevance_hint="подсказка",
        )
        self.assertEqual(project["brand"]["website"], "smartoffice39.ru")
        self.assertEqual(project["brand"]["social_links"], ["https://vk.com/smartoffice39"])
        self.assertEqual(project["relevance_hint"], "подсказка")

    def test_save_without_brand_form_preserves_profile(self):
        self._post(brand_form="1", brand_website="smartoffice39.ru", relevance_hint="подсказка")
        # POST из формы без блока «Профиль бренда» (например, страница до обновления)
        project = self._post()
        self.assertEqual(project["brand"]["website"], "smartoffice39.ru")
        self.assertEqual(project["relevance_hint"], "подсказка")

    def test_emptied_brand_form_clears_profile(self):
        self._post(brand_form="1", brand_website="smartoffice39.ru", relevance_hint="подсказка")
        project = self._post(brand_form="1")
        self.assertEqual(project["brand"], {})
        self.assertEqual(project["relevance_hint"], "")


class TestDashboardProjectCreate(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        fd, self.cfg_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(self.cfg_path, "w", encoding="utf-8") as fh:
            json.dump({"database": self.db_path}, fh)
        self.conn = connect(self.db_path)
        self.account_id = create_account(self.conn, "Клиент")
        self.user = {"username": "admin", "role": "admin", "account_id": self.account_id}

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)
        os.unlink(self.cfg_path)

    def test_dashboard_create_saves_language_and_region(self):
        body = urlencode(
            {
                "project_name": "Global launch",
                "queries": '"Global launch"\nbrand launch',
                "language": "en",
                "region": "GLOBAL",
            }
        ).encode()
        project_name, run_now = handle_dashboard_project_post(self.cfg_path, body, self.user)
        project = get_project_by_name(self.conn, self.account_id, project_name)
        self.assertEqual(project_name, "Global launch")
        self.assertFalse(run_now)
        self.assertEqual(project["language"], "en")
        self.assertEqual(project["region"], "GLOBAL")
        self.assertEqual(project["queries"], ['"Global launch"', "brand launch"])


class TestProjectContextBrand(unittest.TestCase):
    def test_includes_brand_profile(self):
        project = {
            "name": "сфера",
            "queries": ["сфера калининград"],
            "brand": {"industry": "коворкинг", "city": "Калининград",
                      "website": "smartoffice39.ru", "aliases": "smartoffice39"},
            "relevance_hint": "только коворкинг",
        }
        ctx = _project_context(project, "сфера")
        self.assertIn("коворкинг", ctx)
        self.assertIn("smartoffice39.ru", ctx)
        self.assertIn("только коворкинг", ctx)

    def test_unknown_project_safe(self):
        self.assertIn("неизвестный", _project_context(None, "неизвестный"))


class TestCorrectSentimentRelevantOnly(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        fd, self.cfg_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        _write_config(self.cfg_path, self.db_path)
        conn = connect(self.db_path)
        for i in range(1, 6):
            insert_mention(conn, _mention(url=f"https://example.com/{i}", content_hash=f"hash-{i}"))
        conn.commit()
        self.ids = [row["id"] for row in conn.execute("SELECT id FROM mentions ORDER BY id")]
        conn.close()

    def tearDown(self):
        os.unlink(self.db_path)
        os.unlink(self.cfg_path)

    def _run(self, results):
        with patch("mention_monitor.ai_audit.active_provider", return_value="claude"), \
             patch("mention_monitor.ai_audit._classify_batch", return_value=results):
            return correct_sentiment(self.cfg_path, only_pending=True, max_items=10)

    def test_stats_count_relevant_only(self):
        ids = self.ids
        results = {
            ids[0]: {"sentiment": "positive", "relevant": True},   # релевантный, исправлен
            ids[1]: {"sentiment": "neutral", "relevant": True},    # релевантный, совпал
            ids[2]: {"sentiment": "positive", "relevant": False},  # нерелевантные — не в статистике
            ids[3]: {"sentiment": "negative", "relevant": False},
            ids[4]: {"sentiment": "neutral", "relevant": False},
        }
        audit = self._run(results)
        self.assertEqual(audit["status"], "ok")
        self.assertEqual(audit["checked"], 2)
        self.assertEqual(audit["excluded"], 3)
        self.assertEqual(audit["agreement"], 50.0)
        self.assertEqual(len(audit["mismatches"]), 1)  # только релевантные расхождения
        conn = connect(self.db_path)
        relevant_flags = [row["relevant"] for row in conn.execute("SELECT relevant FROM mentions ORDER BY id")]
        sources = {row["relevance_source"] for row in conn.execute("SELECT relevance_source FROM mentions")}
        conn.close()
        self.assertEqual(relevant_flags, [1, 1, 0, 0, 0])
        self.assertEqual(sources, {"ai"})

    def test_all_irrelevant_is_not_failure(self):
        results = {mid: {"sentiment": "neutral", "relevant": False} for mid in self.ids}
        audit = self._run(results)
        self.assertEqual(audit["status"], "ok")
        self.assertEqual(audit["checked"], 0)
        self.assertEqual(audit["excluded"], 5)
        self.assertIsNone(audit["agreement"])


if __name__ == "__main__":
    unittest.main()
