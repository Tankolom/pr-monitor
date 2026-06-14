"""
Интеграция с ЮKassa (self-serve оплата подписки).

Поток: клиент выбирает тариф на /upgrade → создаём платёж в ЮKassa и редиректим
на страницу оплаты → ЮKassa зовёт вебхук /yookassa-webhook → мы перепроверяем
платёж напрямую через API и продлеваем подписку.

Провайдер изолирован в этом модуле — биллинг (db/billing) о нём не знает,
поэтому позже легко добавить Freedom Pay/Kaspi для KZ по тому же контракту.
"""
from __future__ import annotations

import base64
import json
import sqlite3
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone

from .billing import period_end_after, plan_amount, plan_title
from .config import secret_value
from .logging_utils import get_logger

LOGGER = get_logger(__name__)
API_BASE = "https://api.yookassa.ru/v3"


def yookassa_settings(config: dict) -> dict:
    return {
        "shop_id": (secret_value(config, "YOOKASSA_SHOP_ID") or "").strip(),
        "secret_key": (secret_value(config, "YOOKASSA_SECRET_KEY") or "").strip(),
    }


def yookassa_status(config: dict) -> dict:
    s = yookassa_settings(config)
    ready = bool(s["shop_id"] and s["secret_key"])
    return {
        "ready": ready,
        "message": "ЮKassa подключена — приём онлайн-оплат работает."
        if ready else "Не заданы YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY.",
        "settings": s,
    }


def _auth_header(s: dict) -> str:
    raw = f"{s['shop_id']}:{s['secret_key']}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def create_payment(config: dict, account_id: int, plan: str, months: int, return_url: str,
                   description: str | None = None) -> tuple[bool, str]:
    """Создаёт платёж в ЮKassa. Возвращает (ok, confirmation_url | текст ошибки)."""
    s = yookassa_settings(config)
    if not (s["shop_id"] and s["secret_key"]):
        return False, "ЮKassa не настроена (нет shopId/secretKey)."
    amount = plan_amount(plan, months)
    if amount <= 0:
        return False, "Для этого тарифа онлайн-оплата недоступна."
    payload = {
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "capture": True,
        "confirmation": {"type": "redirect", "return_url": return_url},
        "description": (description or f"PR Monitor — тариф «{plan_title(plan)}», {months} мес.")[:128],
        "metadata": {"account_id": str(account_id), "plan": plan, "months": str(months)},
    }
    req = urllib.request.Request(
        f"{API_BASE}/payments",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": _auth_header(s),
            "Idempotence-Key": str(uuid.uuid4()),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")[:300]
        LOGGER.warning("YooKassa create_payment HTTP %s: %s", exc.code, body)
        return False, f"ЮKassa вернула ошибку {exc.code}."
    except Exception as exc:  # pragma: no cover - сетевые сбои
        LOGGER.warning("YooKassa create_payment failed: %s", exc)
        return False, "Не удалось связаться с ЮKassa, попробуйте позже."
    url = (data.get("confirmation") or {}).get("confirmation_url")
    if not url:
        return False, "ЮKassa не вернула ссылку на оплату."
    return True, url


def fetch_payment(config: dict, payment_id: str) -> dict:
    """Получает платёж из ЮKassa по id — для проверки подлинности уведомления."""
    s = yookassa_settings(config)
    req = urllib.request.Request(
        f"{API_BASE}/payments/{payment_id}",
        headers={"Authorization": _auth_header(s)},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def process_webhook(config: dict, body_bytes: bytes) -> tuple[bool, str]:
    """Обрабатывает уведомление ЮKassa. Перепроверяет платёж через API (не доверяет телу),
    идемпотентно продлевает подписку. Возвращает (ok, message)."""
    from .db import connect, get_account, list_payments, record_payment, update_account
    try:
        event = json.loads(body_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return False, "bad json"
    obj = event.get("object") or {}
    payment_id = obj.get("id")
    if not payment_id:
        return False, "no payment id"
    # Перепроверяем статус напрямую у ЮKassa — защита от поддельных уведомлений.
    try:
        payment = fetch_payment(config, payment_id)
    except Exception as exc:  # pragma: no cover
        LOGGER.warning("YooKassa fetch_payment failed: %s", exc)
        return False, "fetch failed"
    if payment.get("status") != "succeeded" or not payment.get("paid"):
        return True, f"ignored status={payment.get('status')}"  # отвечаем 200, но не применяем
    meta = payment.get("metadata") or {}
    try:
        account_id = int(meta.get("account_id"))
        months = max(1, int(meta.get("months") or 1))
    except (TypeError, ValueError):
        return False, "bad metadata"
    plan = meta.get("plan")
    try:
        amount = float((payment.get("amount") or {}).get("value") or 0)
    except (TypeError, ValueError):
        amount = 0.0
    conn = connect(config["database"])
    try:
        # быстрый путь: тот же платёж уже зачтён?
        if any(p.get("external_id") == payment_id for p in list_payments(conn, account_id)):
            return True, "already processed"
        account = get_account(conn, account_id)
        if not account:
            return False, "account not found"
        from .billing import _parse_iso
        current_end = _parse_iso(account.get("period_end"))
        now = datetime.now(timezone.utc)
        start = current_end if (current_end and current_end > now) else now
        new_end = period_end_after(months, start=start)
        # Атомарная защита: вставка платежа — единственный «шлюз». При гонке двух
        # вебхуков уникальный индекс (provider, external_id) пропустит только один;
        # проигравший словит IntegrityError и НЕ продлит подписку повторно.
        try:
            record_payment(conn, account_id, amount=amount, plan=plan, provider="yookassa",
                           period_months=months, status="succeeded", external_id=payment_id,
                           note="онлайн-оплата ЮKassa")
        except sqlite3.IntegrityError:
            return True, "already processed"
        update_account(conn, account_id, plan=plan, status="active", period_end=new_end)
        LOGGER.info("YooKassa payment %s applied: account=%s plan=%s months=%s", payment_id, account_id, plan, months)
        return True, "applied"
    finally:
        conn.close()
