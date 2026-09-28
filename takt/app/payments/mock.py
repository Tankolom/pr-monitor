"""Тестовая оплата: страница /mock-pay/<order> с кнопками «Оплатить» / «Отменить». Только для разработки."""
from __future__ import annotations

from .. import config, db
from . import Created


class MockProvider:
    name = "mock"

    def create(self, order: dict, description: str, return_url: str) -> Created:
        pid = "mock_" + order["id"]
        url = f"{config.settings.base_url}/mock-pay/{order['id']}?token={order['token']}"
        return Created(payment_id=pid, confirmation_url=url)

    def status(self, payment_id: str) -> str:
        row = db.one("SELECT status FROM orders WHERE provider_payment_id=?", payment_id)
        if row is None:
            return "canceled"
        return {"paid": "succeeded", "canceled": "canceled"}.get(row["status"], "pending")
