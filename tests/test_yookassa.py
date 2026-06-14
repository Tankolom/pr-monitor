import io
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mention_monitor import yookassa
from mention_monitor.billing import account_is_active, plan_amount
from mention_monitor.db import connect, create_account, get_account, list_payments


def _cfg(db_path, with_keys=True):
    cfg = {"database": db_path}
    if with_keys:
        cfg["_secrets"] = {}
    return cfg


class TestPlanAmount(unittest.TestCase):
    def test_monthly_and_annual(self):
        self.assertEqual(plan_amount("start", 1), 3900)
        self.assertEqual(plan_amount("start", 12), int(3900 * 12 * 0.8))
        self.assertEqual(plan_amount("trial", 1), 0)
        self.assertEqual(plan_amount("enterprise", 3), 0)


class TestCreatePayment(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db"); os.close(fd)

    def tearDown(self):
        os.unlink(self.db)

    def test_not_configured(self):
        with patch("mention_monitor.yookassa.yookassa_settings", return_value={"shop_id": "", "secret_key": ""}):
            ok, msg = yookassa.create_payment({"database": self.db}, 1, "start", 1, "https://x/return")
        self.assertFalse(ok)
        self.assertIn("не настроена", msg.lower())

    def test_creates_and_returns_confirmation_url(self):
        fake_resp = io.BytesIO(json.dumps({
            "id": "pay_1", "status": "pending",
            "confirmation": {"type": "redirect", "confirmation_url": "https://yoomoney.ru/checkout/pay_1"},
        }).encode())
        fake_resp.__enter__ = lambda s: s
        fake_resp.__exit__ = lambda *a: False
        with patch("mention_monitor.yookassa.yookassa_settings", return_value={"shop_id": "123", "secret_key": "key"}), \
             patch("mention_monitor.yookassa.urllib.request.urlopen", return_value=fake_resp):
            ok, url = yookassa.create_payment({"database": self.db}, 1, "business", 12, "https://x/return")
        self.assertTrue(ok)
        self.assertEqual(url, "https://yoomoney.ru/checkout/pay_1")


class TestWebhook(unittest.TestCase):
    def setUp(self):
        fd, self.db = tempfile.mkstemp(suffix=".db"); os.close(fd)
        self.conn = connect(self.db)
        self.aid = create_account(self.conn, "Клиент", plan="trial")

    def tearDown(self):
        self.conn.close()
        os.unlink(self.db)

    def _succeeded_payment(self):
        return {
            "id": "pay_42", "status": "succeeded", "paid": True,
            "amount": {"value": "11900.00", "currency": "RUB"},
            "metadata": {"account_id": str(self.aid), "plan": "business", "months": "1"},
        }

    def test_succeeded_applies_and_is_idempotent(self):
        body = json.dumps({"event": "payment.succeeded", "object": {"id": "pay_42"}}).encode()
        with patch("mention_monitor.yookassa.fetch_payment", return_value=self._succeeded_payment()):
            ok, msg = yookassa.process_webhook({"database": self.db}, body)
            self.assertTrue(ok)
            self.assertEqual(msg, "applied")
            acc = get_account(self.conn, self.aid)
            self.assertEqual(acc["plan"], "business")
            self.assertEqual(acc["status"], "active")
            self.assertTrue(account_is_active(acc))
            self.assertEqual(len(list_payments(self.conn, self.aid)), 1)
            # повторная доставка того же платежа — не дублируется
            ok2, msg2 = yookassa.process_webhook({"database": self.db}, body)
            self.assertTrue(ok2)
            self.assertEqual(msg2, "already processed")
            self.assertEqual(len(list_payments(self.conn, self.aid)), 1)

    def test_pending_payment_ignored(self):
        body = json.dumps({"object": {"id": "pay_99"}}).encode()
        pending = self._succeeded_payment()
        pending["status"] = "pending"
        pending["paid"] = False
        with patch("mention_monitor.yookassa.fetch_payment", return_value=pending):
            ok, msg = yookassa.process_webhook({"database": self.db}, body)
        self.assertTrue(ok)  # отвечаем 200
        self.assertIn("ignored", msg)
        acc = get_account(self.conn, self.aid)
        self.assertEqual(acc["plan"], "trial")  # ничего не применили
        self.assertEqual(len(list_payments(self.conn, self.aid)), 0)

    def test_bad_json_rejected(self):
        ok, msg = yookassa.process_webhook({"database": self.db}, b"not-json")
        self.assertFalse(ok)


if __name__ == "__main__":
    unittest.main()
