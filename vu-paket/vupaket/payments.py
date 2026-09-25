"""
ЮKassa: создание платежа, проверка статуса и обработка уведомлений.

Уведомлению не доверяем: по id из тела запрашиваем платёж у API и проверяем
статус, сумму, валюту и привязку к заказу. Повторные уведомления безопасны.
"""
from __future__ import annotations

import base64
import json
import logging
import urllib.error
import urllib.request
import uuid

from .config import Settings
from .db import Store

API_BASE = "https://api.yookassa.ru/v3"
LOG = logging.getLogger("vupaket.payments")


class PaymentError(Exception):
    pass


def _auth(s: Settings) -> str:
    raw = f"{s.yookassa_shop_id}:{s.yookassa_secret_key}".encode()
    return "Basic " + base64.b64encode(raw).decode()


def _request(s: Settings, method: str, path: str, payload: dict | None = None, idem_key: str | None = None) -> dict:
    headers = {"Authorization": _auth(s), "Content-Type": "application/json"}
    if idem_key:
        headers["Idempotence-Key"] = idem_key
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(payload).encode() if payload is not None else None,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        LOG.warning("YooKassa %s %s -> HTTP %s: %s", method, path, exc.code, body)
        raise PaymentError(f"ЮKassa вернула ошибку {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        LOG.warning("YooKassa %s %s failed: %s", method, path, exc)
        raise PaymentError("Не удалось связаться с ЮKassa") from exc


def create_payment(s: Settings, order: dict, return_url: str) -> tuple[str, str]:
    """Создаёт платёж. Возвращает (payment_id, confirmation_url)."""
    amount = f"{order['price_rub']:.2f}"
    description = f"Пакет документов по воинскому учёту, заказ {order['id']}"
    payload: dict = {
        "amount": {"value": amount, "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": description[:128],
        "metadata": {"order_token": order["token"]},
    }
    if s.yookassa_receipt:
        payload["receipt"] = {
            "customer": {"email": order["email"]},
            "items": [{
                "description": "Пакет документов по воинскому учёту (электронные шаблоны)",
                "quantity": "1.00",
                "amount": {"value": amount, "currency": "RUB"},
                "vat_code": s.yookassa_vat_code,
                "payment_mode": "full_payment",
                "payment_subject": "service",
            }],
        }
    data = _request(s, "POST", "/payments", payload, idem_key=str(uuid.uuid4()))
    url = (data.get("confirmation") or {}).get("confirmation_url")
    if not data.get("id") or not url:
        raise PaymentError("ЮKassa не вернула ссылку на оплату")
    return data["id"], url


def fetch_payment(s: Settings, payment_id: str) -> dict:
    return _request(s, "GET", f"/payments/{payment_id}")


def reusable_confirmation(s: Settings, order: dict, fetch=None) -> str | None:
    """Повторный клик «Оплатить»: если прошлый платёж ещё ждёт оплаты — ведём на него же."""
    if not order.get("payment_id"):
        return None
    try:
        payment = (fetch or fetch_payment)(s, order["payment_id"])
    except PaymentError:
        return None
    if payment.get("status") == "pending":
        return (payment.get("confirmation") or {}).get("confirmation_url")
    return None


def apply_payment(store: Store, payment: dict) -> str:
    """Проверяет платёж из API и помечает заказ. Возвращает короткий статус для логов."""
    if payment.get("status") != "succeeded" or not payment.get("paid"):
        return f"ignored:{payment.get('status')}"
    token = (payment.get("metadata") or {}).get("order_token")
    if not token:
        return "no-order"
    order = store.get_order(token)
    if not order:
        return "order-not-found"
    amount = payment.get("amount") or {}
    try:
        value = float(amount.get("value") or 0)
    except (TypeError, ValueError):
        value = 0.0
    if amount.get("currency") != "RUB" or abs(value - order["price_rub"]) > 0.009:
        LOG.warning("Amount mismatch for order %s: %s", order["id"], amount)
        return "amount-mismatch"
    applied = store.mark_paid(token, "yookassa", payment["id"], value)
    if applied:
        store.log_event("payment_succeeded", token, order)
    return "applied" if applied else "already"


def process_webhook(s: Settings, store: Store, body: bytes, fetch=fetch_payment) -> str:
    try:
        event = json.loads(body.decode())
    except (ValueError, UnicodeDecodeError):
        return "bad-json"
    payment_id = (event.get("object") or {}).get("id")
    if not payment_id or not isinstance(payment_id, str) or len(payment_id) > 64:
        return "no-id"
    payment = fetch(s, payment_id)
    return apply_payment(store, payment)


def refresh_order(s: Settings, store: Store, order: dict, fetch=fetch_payment) -> dict:
    """Если вебхук задержался — спрашиваем статус сами (при возврате со страницы оплаты)."""
    if order["status"] != "pending" or not order.get("payment_id") or not s.payments_ready:
        return order
    try:
        result = apply_payment(store, fetch(s, order["payment_id"]))
    except PaymentError:
        return order
    if result == "ignored:canceled":
        # Платёж отменён или истёк — возвращаем заказ к оплате, чтобы не ждать вечно.
        store.reset_payment(order["token"])
    return store.get_order(order["token"]) or order
