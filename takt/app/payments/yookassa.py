"""ЮKassa API v3: создание платежа с редиректом и проверка статуса.

Уведомления (webhook) ЮKassa не подписывает, поэтому статус всегда перепроверяем
запросом GET /v3/payments/{id} — подделать успешную оплату нельзя.
Документация: https://yookassa.ru/developers/api
"""
from __future__ import annotations

import uuid

import httpx

from .. import config
from . import Created, PaymentError

API = "https://api.yookassa.ru/v3"


class YooKassa:
    name = "yookassa"

    def __init__(self, transport: httpx.BaseTransport | None = None):
        s = config.settings
        if not (s.yookassa_shop_id and s.yookassa_secret):
            raise PaymentError("YOOKASSA_SHOP_ID / YOOKASSA_SECRET_KEY не заданы")
        self.client = httpx.Client(base_url=API, auth=(s.yookassa_shop_id, s.yookassa_secret),
                                   timeout=20, transport=transport)

    def create(self, order: dict, description: str, return_url: str) -> Created:
        s = config.settings
        body = {
            "amount": {"value": f"{order['amount']:.2f}", "currency": "RUB"},
            "capture": True,
            "confirmation": {"type": "redirect", "return_url": return_url},
            "description": description[:128],
            "metadata": {"order_id": order["id"]},
        }
        if s.yookassa_receipt:
            if not order.get("email"):
                raise PaymentError("Для чека нужен e-mail покупателя")
            body["receipt"] = {
                **({"tax_system_code": s.yookassa_tax_system_code} if s.yookassa_tax_system_code else {}),
                "customer": {"email": order["email"]},
                "items": [{
                    "description": description[:128],
                    "quantity": "1.00",
                    "amount": {"value": f"{order['amount']:.2f}", "currency": "RUB"},
                    "vat_code": s.yookassa_vat_code,
                    "payment_mode": "full_payment",
                    "payment_subject": "service",
                }],
            }
        # один и тот же заказ → один платёж даже при повторе запроса
        r = self.client.post("/payments", json=body, headers={"Idempotence-Key": str(uuid.uuid5(uuid.NAMESPACE_URL, "takt-order-" + order["id"]))})
        if r.status_code >= 400:
            raise PaymentError(f"ЮKassa {r.status_code}: {r.text[:300]}")
        data = r.json()
        url = (data.get("confirmation") or {}).get("confirmation_url")
        if not url:
            raise PaymentError("ЮKassa не вернула ссылку на оплату")
        return Created(payment_id=data["id"], confirmation_url=url)

    def status(self, payment_id: str) -> str:
        r = self.client.get(f"/payments/{payment_id}")
        if r.status_code == 404:
            return "canceled"
        if r.status_code >= 400:
            raise PaymentError(f"ЮKassa {r.status_code}: {r.text[:300]}")
        return r.json().get("status", "pending")   # pending | waiting_for_capture | succeeded | canceled
