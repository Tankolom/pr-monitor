"""Настройки из переменных окружения. Секреты живут только на сервере."""
from __future__ import annotations

import os
from dataclasses import dataclass


def _bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class Settings:
    host: str
    port: int
    public_url: str
    db_path: str
    price_rub: int
    demo_payments: bool
    yookassa_shop_id: str
    yookassa_secret_key: str
    yookassa_receipt: bool
    yookassa_vat_code: int
    admin_key: str
    metrika_id: str
    seller_name: str
    seller_inn: str
    seller_email: str
    trust_proxy: bool
    order_ttl_days: int

    @property
    def payments_ready(self) -> bool:
        return bool(self.yookassa_shop_id and self.yookassa_secret_key)

    @property
    def seller_ready(self) -> bool:
        return bool(self.seller_name and self.seller_inn and self.seller_email)


def load_settings() -> Settings:
    return Settings(
        host=os.environ.get("VU_HOST", "127.0.0.1"),
        port=_int("VU_PORT", 8080),
        public_url=os.environ.get("VU_PUBLIC_URL", "http://127.0.0.1:8080").rstrip("/"),
        db_path=os.environ.get("VU_DB_PATH", "data/vu.db"),
        price_rub=_int("VU_PRICE_RUB", 2490),
        demo_payments=_bool("VU_DEMO_PAYMENTS", False),
        yookassa_shop_id=os.environ.get("YOOKASSA_SHOP_ID", "").strip(),
        yookassa_secret_key=os.environ.get("YOOKASSA_SECRET_KEY", "").strip(),
        yookassa_receipt=_bool("YOOKASSA_RECEIPT", True),
        yookassa_vat_code=_int("YOOKASSA_VAT_CODE", 1),
        admin_key=os.environ.get("VU_ADMIN_KEY", "").strip(),
        metrika_id=os.environ.get("VU_METRIKA_ID", "").strip(),
        seller_name=os.environ.get("VU_SELLER_NAME", "").strip(),
        seller_inn=os.environ.get("VU_SELLER_INN", "").strip(),
        seller_email=os.environ.get("VU_SELLER_EMAIL", "").strip(),
        trust_proxy=_bool("VU_TRUST_PROXY", False),
        order_ttl_days=_int("VU_ORDER_TTL_DAYS", 30),
    )
