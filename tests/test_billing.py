import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mention_monitor import billing
from mention_monitor.db import (
    account_usage,
    connect,
    create_account,
    create_project_row,
    create_public_user,
    create_user,
    delete_project_row,
    due_projects,
    get_account,
    get_project_by_name,
    get_user_by_email,
    insert_mention,
    list_accounts,
    list_payments,
    list_projects,
    mark_project_collected,
    migrate_to_accounts,
    record_payment,
    update_account,
    update_project_row,
)


def _now():
    return datetime.now(timezone.utc)


class TestBillingLogic(unittest.TestCase):
    def test_plan_limits(self):
        self.assertEqual(billing.plan_limit("start", "queries"), 30)
        self.assertEqual(billing.plan_limit("business", "projects"), 5)
        self.assertIsNone(billing.plan_limit("enterprise", "projects"))  # безлимит
        self.assertEqual(billing.plan_limit("неизвестный", "users"), 1)  # как trial

    def test_effective_quota_override(self):
        acc = {"plan": "start", "quota_queries": 100, "quota_projects": None}
        self.assertEqual(billing.effective_quota(acc, "queries"), 100)  # override
        self.assertEqual(billing.effective_quota(acc, "projects"), 1)   # от тарифа
        self.assertEqual(billing.effective_quota(None, "projects"), 1)  # дефолт trial

    def test_quota_reached_and_unlimited(self):
        self.assertTrue(billing.quota_reached(5, 5))
        self.assertFalse(billing.quota_reached(5, 4))
        self.assertFalse(billing.quota_reached(None, 9999))  # безлимит
        self.assertIsNone(billing.quota_remaining(None, 10))
        self.assertEqual(billing.quota_remaining(5, 3), 2)

    def test_account_is_active(self):
        future = (_now() + timedelta(days=3)).isoformat()
        past = (_now() - timedelta(days=1)).isoformat()
        self.assertTrue(billing.account_is_active({"status": "active", "period_end": future}))
        self.assertTrue(billing.account_is_active({"status": "trial", "period_end": None}))
        self.assertFalse(billing.account_is_active({"status": "active", "period_end": past}))
        self.assertFalse(billing.account_is_active({"status": "suspended", "period_end": future}))
        self.assertFalse(billing.account_is_active(None))

    def test_normalize_collection_interval(self):
        self.assertEqual(billing.normalize_collection_interval(1), 3)   # пол 3 часа
        self.assertEqual(billing.normalize_collection_interval(3), 3)
        self.assertEqual(billing.normalize_collection_interval(5), 6)   # округление вверх к допустимому
        self.assertEqual(billing.normalize_collection_interval(48), 48)
        self.assertEqual(billing.normalize_collection_interval(999), 48)
        self.assertEqual(billing.normalize_collection_interval("abc"), 3)


class TestAccountsLayer(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_create_account_trial_defaults(self):
        aid = create_account(self.conn, "Клиент")
        acc = get_account(self.conn, aid)
        self.assertEqual(acc["plan"], "trial")
        self.assertEqual(acc["status"], "trial")
        self.assertIsNotNone(acc["period_end"])  # триал получает срок

    def test_create_account_paid_no_period(self):
        aid = create_account(self.conn, "Платный", plan="business")
        acc = get_account(self.conn, aid)
        self.assertEqual(acc["status"], "active")
        self.assertIsNone(acc["period_end"])

    def test_update_account_whitelist(self):
        aid = create_account(self.conn, "Клиент")
        update_account(self.conn, aid, plan="agency", quota_queries=999, bogus="x")
        acc = get_account(self.conn, aid)
        self.assertEqual(acc["plan"], "agency")
        self.assertEqual(acc["quota_queries"], 999)
        self.assertNotIn("bogus", acc)

    def test_usage_counts(self):
        aid = create_account(self.conn, "Клиент")
        create_project_row(self.conn, aid, "П1", queries=["a", "b"])
        create_project_row(self.conn, aid, "П2", queries=["c"])
        create_user(self.conn, "u1", "pw12345678")
        # привяжем пользователя к аккаунту вручную (create_user не знает про аккаунт)
        self.conn.execute("UPDATE users SET account_id = ? WHERE username = 'u1'", (aid,))
        self.conn.commit()
        usage = account_usage(self.conn, aid)
        self.assertEqual(usage["projects"], 2)
        self.assertEqual(usage["queries"], 3)
        self.assertEqual(usage["users"], 1)

    def test_payments(self):
        aid = create_account(self.conn, "Клиент")
        record_payment(self.conn, aid, amount=11900, plan="business", period_months=1, note="ручная оплата")
        pays = list_payments(self.conn, aid)
        self.assertEqual(len(pays), 1)
        self.assertEqual(pays[0]["amount"], 11900)
        self.assertEqual(pays[0]["provider"], "manual")


class TestProjectsLayer(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = connect(self.db_path)
        self.aid = create_account(self.conn, "Клиент")

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_create_and_roundtrip(self):
        p = create_project_row(
            self.conn, self.aid, "Сфера",
            queries=["сфера калининград", " "],  # пустые отсекаются
            owner="admin",
            brand={"website": "smartoffice39.ru", "city": "Калининград"},
            relevance_hint="только коворкинг",
        )
        self.assertEqual(p["queries"], ["сфера калининград"])
        self.assertEqual(p["brand"]["website"], "smartoffice39.ru")
        self.assertEqual(p["relevance_hint"], "только коворкинг")
        self.assertFalse(p["schedule_enabled"])
        self.assertEqual(p["schedule_interval_hours"], 3)

    def test_unique_name_within_account(self):
        create_project_row(self.conn, self.aid, "Дубль")
        p2 = create_project_row(self.conn, self.aid, "Дубль")
        self.assertEqual(p2["name"], "Дубль 2")

    def test_same_name_different_accounts_ok(self):
        other = create_account(self.conn, "Другой")
        create_project_row(self.conn, self.aid, "Сфера")
        p = create_project_row(self.conn, other, "Сфера")
        self.assertEqual(p["name"], "Сфера")  # имена не конфликтуют между аккаунтами

    def test_update_and_delete(self):
        p = create_project_row(self.conn, self.aid, "П")
        update_project_row(self.conn, p["id"], queries=["x", "y"], schedule_enabled=True, schedule_interval_hours=6)
        upd = get_project_by_name(self.conn, self.aid, "П")
        self.assertEqual(upd["queries"], ["x", "y"])
        self.assertTrue(upd["schedule_enabled"])
        self.assertEqual(upd["schedule_interval_hours"], 6)
        delete_project_row(self.conn, p["id"])
        self.assertEqual(list_projects(self.conn, self.aid), [])

    def test_list_scoped_by_account(self):
        other = create_account(self.conn, "Другой")
        create_project_row(self.conn, self.aid, "Мой")
        create_project_row(self.conn, other, "Чужой")
        mine = list_projects(self.conn, self.aid)
        self.assertEqual([p["name"] for p in mine], ["Мой"])


class TestAccountScopedReads(unittest.TestCase):
    """Изоляция упоминаний: dashboard_stats/latest_mentions с account_id видят только свой аккаунт."""

    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = connect(self.db_path)
        self.a1 = create_account(self.conn, "A1")
        self.a2 = create_account(self.conn, "A2")
        for i, aid in enumerate([self.a1, self.a1, self.a2]):
            insert_mention(self.conn, {
                "account_id": aid, "project": "P", "query": "q", "title": "t",
                "snippet": "s", "text": "x", "url": f"https://e.com/{i}", "source": "e.com",
                "published_at": None, "collected_at": "2026-06-01T00:00:00+00:00",
                "sentiment": "neutral", "sentiment_score": 0.0, "language": "ru",
                "entities": [], "raw_path": None, "content_hash": f"h{i}",
                "likes": 0, "reposts": 0, "comments": 0, "views": 0,
            })

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_dashboard_stats_scoped(self):
        from mention_monitor.db import dashboard_stats, latest_mentions
        self.assertEqual(dashboard_stats(self.conn, account_id=self.a1)["total"], 2)
        self.assertEqual(dashboard_stats(self.conn, account_id=self.a2)["total"], 1)
        self.assertEqual(dashboard_stats(self.conn)["total"], 3)  # без account_id — всё (обратная совместимость)
        self.assertEqual(len(latest_mentions(self.conn, account_id=self.a2)), 1)


class TestRegistrationCreatesTenant(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_public_registration_provisions_account(self):
        uid = create_public_user(self.conn, "client@company.ru", "pw12345678", "Компания")
        user = get_user_by_email(self.conn, "client@company.ru")
        self.assertEqual(user["id"], uid)
        self.assertIsNotNone(user["account_id"])
        self.assertEqual(user["role"], "admin")        # владелец своего аккаунта
        self.assertEqual(user["is_superadmin"], 0)      # но не платформенный суперадмин
        acc = get_account(self.conn, user["account_id"])
        self.assertEqual(acc["plan"], "trial")
        self.assertEqual(acc["status"], "trial")


class TestQuotaEnforcement(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        fd, self.cfg_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(self.cfg_path, "w", encoding="utf-8") as fh:
            json.dump({"database": self.db_path}, fh)
        self.conn = connect(self.db_path)
        # тариф «Старт»: 1 проект, 30 запросов, 1 пользователь
        self.account_id = create_account(self.conn, "Клиент", plan="start")
        create_project_row(self.conn, self.account_id, "П1", queries=["a"], owner="admin")
        self.user = {"username": "admin", "role": "admin",
                     "account_id": self.account_id, "is_superadmin": 0}

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)
        os.unlink(self.cfg_path)

    def _post(self, **fields):
        from mention_monitor.pages import handle_topics_post
        return handle_topics_post(self.cfg_path, urlencode(fields).encode(), self.user)

    def test_quota_state(self):
        from mention_monitor.db import account_quota_state
        st = account_quota_state(self.conn, self.account_id)
        self.assertEqual(st["dimensions"]["projects"]["used"], 1)
        self.assertEqual(st["dimensions"]["projects"]["limit"], 1)
        self.assertTrue(st["dimensions"]["projects"]["reached"])
        self.assertEqual(st["dimensions"]["queries"]["limit"], 30)

    def test_project_quota_blocks_create(self):
        msg = self._post(action="create")
        self.assertIn("лимит проектов", msg.lower())
        self.assertEqual(len(list_projects(self.conn, self.account_id)), 1)  # не создан

    def test_query_quota_blocks_save(self):
        many = "\n".join(f"q{i}" for i in range(31))  # 31 > 30
        msg = self._post(action="save", original_project_name="П1", project_name="П1",
                         queries=many, control_urls="")
        self.assertIn("лимит запросов", msg.lower())
        # изменения не сохранены — остался исходный единственный запрос
        proj = get_project_by_name(self.conn, self.account_id, "П1")
        self.assertEqual(proj["queries"], ["a"])

    def test_query_within_quota_saves(self):
        ok_list = "\n".join(f"q{i}" for i in range(30))
        msg = self._post(action="save", original_project_name="П1", project_name="П1",
                         queries=ok_list, control_urls="")
        self.assertIn("сохран", msg.lower())
        proj = get_project_by_name(self.conn, self.account_id, "П1")
        self.assertEqual(len(proj["queries"]), 30)


class TestBillingPanel(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        fd, self.cfg_path = tempfile.mkstemp(suffix=".json")
        os.close(fd)
        with open(self.cfg_path, "w", encoding="utf-8") as fh:
            json.dump({"database": self.db_path}, fh)
        self.conn = connect(self.db_path)
        self.aid = create_account(self.conn, "Клиент", plan="start")
        self.su = {"username": "admin", "role": "admin", "account_id": 1, "is_superadmin": 1}

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)
        os.unlink(self.cfg_path)

    def _post(self, **f):
        from mention_monitor.pages import handle_billing_post
        return handle_billing_post(self.cfg_path, urlencode(f).encode(), self.su)

    def test_save_account_changes_plan_and_status(self):
        self._post(action="save_account", account_id=self.aid, name="Клиент",
                   plan="business", status="suspended", period_end="",
                   quota_projects="", quota_queries="", quota_users="")
        acc = get_account(self.conn, self.aid)
        self.assertEqual(acc["plan"], "business")
        self.assertEqual(acc["status"], "suspended")

    def test_individual_quota_override(self):
        self._post(action="save_account", account_id=self.aid, name="Клиент",
                   plan="start", status="active", period_end="",
                   quota_projects="", quota_queries="999", quota_users="")
        acc = get_account(self.conn, self.aid)
        self.assertEqual(acc["quota_queries"], 999)
        self.assertEqual(billing.effective_quota(acc, "queries"), 999)

    def test_record_payment_activates_and_extends(self):
        msg = self._post(action="record_payment", account_id=self.aid,
                         amount="11900", plan="business", period_months="2", note="счёт 1")
        self.assertIn("Бизнес", msg)
        acc = get_account(self.conn, self.aid)
        self.assertEqual(acc["status"], "active")
        self.assertEqual(acc["plan"], "business")
        self.assertIsNotNone(acc["period_end"])
        self.assertEqual(len(list_payments(self.conn, self.aid)), 1)
        self.assertTrue(billing.account_is_active(acc))


class TestFinanceSummary(unittest.TestCase):
    def test_summary_metrics(self):
        now = _now()
        accounts = [
            {"id": 1, "plan": "business", "status": "active",
             "period_end": (now + timedelta(days=20)).isoformat()},
            {"id": 2, "plan": "start", "status": "active",
             "period_end": (now + timedelta(days=5)).isoformat()},
            {"id": 3, "plan": "start", "status": "canceled", "period_end": None},   # отток
            {"id": 4, "plan": "trial", "status": "trial", "period_end": None},       # не платящий
        ]
        payments = [
            {"account_id": 1, "amount": 11900, "status": "succeeded", "plan": "business",
             "created_at": (now - timedelta(days=3)).isoformat()},
            {"account_id": 2, "amount": 3900, "status": "succeeded", "plan": "start",
             "created_at": (now - timedelta(days=10)).isoformat()},
            {"account_id": 1, "amount": 11900, "status": "succeeded", "plan": "business",
             "created_at": (now - timedelta(days=400)).isoformat()},  # старый
        ]
        fin = billing.finance_summary(accounts, payments, now=now)
        self.assertEqual(fin["total_revenue"], 27700)
        self.assertEqual(fin["revenue_30d"], 15800)        # 11900 + 3900
        self.assertEqual(fin["paying_active"], 2)           # accounts 1 и 2
        self.assertEqual(fin["mrr"], 11900 + 3900)
        self.assertEqual(fin["arpu"], round((11900 + 3900) / 2))
        self.assertEqual(fin["new_paying_30d"], 1)          # только account 2 — новый (у 1 первый платёж 400д назад)
        self.assertEqual(fin["churn_30d"], 1)               # account 3 canceled
        self.assertEqual(len(fin["revenue_by_month"]), 12)
        self.assertEqual(fin["by_plan"].get("business"), 1)


class TestScheduler(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = connect(self.db_path)
        self.aid = create_account(self.conn, "Клиент", plan="business")

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_schedule_off_not_due(self):
        create_project_row(self.conn, self.aid, "P", queries=["a"])
        self.assertEqual(due_projects(self.conn), [])  # автосбор выключен по умолчанию

    def test_enabled_never_collected_is_due(self):
        p = create_project_row(self.conn, self.aid, "P", queries=["a"])
        update_project_row(self.conn, p["id"], schedule_enabled=True, schedule_interval_hours=3)
        due = due_projects(self.conn)
        self.assertEqual([d["name"] for d in due], ["P"])

    def test_recently_collected_not_due(self):
        p = create_project_row(self.conn, self.aid, "P", queries=["a"])
        update_project_row(self.conn, p["id"], schedule_enabled=True, schedule_interval_hours=6)
        recent = (_now() - timedelta(hours=1)).replace(microsecond=0).isoformat()
        mark_project_collected(self.conn, p["id"], when=recent)
        self.assertEqual(due_projects(self.conn), [])  # 1ч < 6ч

    def test_interval_elapsed_is_due(self):
        p = create_project_row(self.conn, self.aid, "P", queries=["a"])
        update_project_row(self.conn, p["id"], schedule_enabled=True, schedule_interval_hours=3)
        old = (_now() - timedelta(hours=5)).replace(microsecond=0).isoformat()
        mark_project_collected(self.conn, p["id"], when=old)
        self.assertEqual([d["name"] for d in due_projects(self.conn)], ["P"])  # 5ч >= 3ч

    def test_inactive_account_not_due(self):
        p = create_project_row(self.conn, self.aid, "P", queries=["a"])
        update_project_row(self.conn, p["id"], schedule_enabled=True, schedule_interval_hours=3)
        update_account(self.conn, self.aid, status="suspended")
        self.assertEqual(due_projects(self.conn), [])  # аккаунт заморожен


class TestSecurityHardening(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_default_admin_no_predictable_password(self):
        from mention_monitor.db import verify_password
        # без env-переменных — пароль не должен быть предсказуемым «admin12345»
        for var in ("MENTION_MONITOR_ADMIN_PASSWORD", "MENTION_MONITOR_PASSWORD"):
            os.environ.pop(var, None)
        conn = connect(self.db_path)
        try:
            row = conn.execute("SELECT password_hash, is_superadmin FROM users WHERE username='admin'").fetchone()
            self.assertIsNotNone(row)
            self.assertFalse(verify_password("admin12345", row["password_hash"]))
            self.assertEqual(row["is_superadmin"], 1)  # первый админ — суперадмин платформы
        finally:
            conn.close()

    def test_env_password_respected(self):
        from mention_monitor.db import verify_password
        os.environ["MENTION_MONITOR_ADMIN_PASSWORD"] = "MyStrongPass123"
        try:
            conn = connect(self.db_path)
            row = conn.execute("SELECT password_hash FROM users WHERE username='admin'").fetchone()
            self.assertTrue(verify_password("MyStrongPass123", row["password_hash"]))
            conn.close()
        finally:
            os.environ.pop("MENTION_MONITOR_ADMIN_PASSWORD", None)

    def test_payment_external_id_unique_per_provider(self):
        conn = connect(self.db_path)
        aid = create_account(conn, "Клиент")
        record_payment(conn, aid, amount=100, provider="yookassa", external_id="pay_1")
        with self.assertRaises(__import__("sqlite3").IntegrityError):
            record_payment(conn, aid, amount=100, provider="yookassa", external_id="pay_1")
        conn.close()

    def test_manual_payments_allow_null_external_id(self):
        conn = connect(self.db_path)
        aid = create_account(conn, "Клиент")
        record_payment(conn, aid, amount=100, provider="manual")
        record_payment(conn, aid, amount=200, provider="manual")  # дубли ручных оплат допустимы
        self.assertEqual(len(list_payments(conn, aid)), 2)
        conn.close()


class TestMigration(unittest.TestCase):
    def setUp(self):
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        self.conn = connect(self.db_path)

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db_path)

    def test_migrates_projects_users_mentions(self):
        # existing admin user уже создан ensure_default_admin
        # добавим историческое упоминание без account_id
        insert_mention(self.conn, {
            "account_id": None, "project": "Старый", "query": "q", "title": "t",
            "snippet": "s", "text": "x", "url": "https://e.com/1", "source": "e.com",
            "published_at": None, "collected_at": "2026-06-01T00:00:00+00:00",
            "sentiment": "neutral", "sentiment_score": 0.0, "language": "ru",
            "entities": [], "raw_path": None, "content_hash": "h1",
            "likes": 0, "reposts": 0, "comments": 0, "views": 0,
        })
        config = {"projects": [
            {"name": "Альфа", "queries": ["a"], "owner": "admin", "relevance_hint": "h"},
            {"name": "Бета", "queries": ["b", "c"]},
        ]}
        self.assertTrue(migrate_to_accounts(self.conn, config))
        accs = list_accounts(self.conn)
        self.assertEqual(len(accs), 1)
        self.assertEqual(accs[0]["plan"], "enterprise")
        self.assertEqual(accs[0]["usage"]["projects"], 2)
        # упоминание получило account_id
        row = self.conn.execute("SELECT account_id FROM mentions WHERE content_hash='h1'").fetchone()
        self.assertEqual(row["account_id"], accs[0]["id"])
        # админ — суперадмин и привязан к аккаунту
        admin = self.conn.execute("SELECT is_superadmin, account_id FROM users WHERE role='admin'").fetchone()
        self.assertEqual(admin["is_superadmin"], 1)
        self.assertEqual(admin["account_id"], accs[0]["id"])
        # конфиг очищен
        self.assertEqual(config["projects"], [])
        # идемпотентность
        self.assertFalse(migrate_to_accounts(self.conn, config))


if __name__ == "__main__":
    unittest.main()
