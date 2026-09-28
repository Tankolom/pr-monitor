"""Платёжные провайдеры: ЮKassa (боевой) и mock (для разработки и тестов)."""
from __future__ import annotations

from dataclasses import dataclass

from .. import config


@dataclass
class Created:
    payment_id: str
    confirmation_url: str


class PaymentError(Exception):
    pass


def provider():
    name = config.settings.payment_provider
    if name == "yookassa":
        from .yookassa import YooKassa

        return YooKassa()
    if name == "mock":
        from .mock import MockProvider

        return MockProvider()
    raise PaymentError(f"Unknown PAYMENT_PROVIDER={name}")
