"""Настройки из переменных окружения (см. .env.example)."""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def _int(name: str, default: int) -> int:
    try:
        return int(_env(name, str(default)))
    except ValueError:
        return default


@dataclass
class Settings:
    base_url: str = field(default_factory=lambda: _env("BASE_URL", "http://localhost:8000").rstrip("/"))
    data_dir: str = field(default_factory=lambda: _env("DATA_DIR", os.path.abspath("data")))
    brand: str = field(default_factory=lambda: _env("BRAND", "Такт"))

    price_single: int = field(default_factory=lambda: _int("PRICE_SINGLE", 490))
    price_pack: int = field(default_factory=lambda: _int("PRICE_PACK", 1490))
    pack_size: int = field(default_factory=lambda: _int("PACK_SIZE", 5))

    payment_provider: str = field(default_factory=lambda: _env("PAYMENT_PROVIDER", "mock"))  # mock | yookassa
    yookassa_shop_id: str = field(default_factory=lambda: _env("YOOKASSA_SHOP_ID"))
    yookassa_secret: str = field(default_factory=lambda: _env("YOOKASSA_SECRET_KEY"))
    # чек 54-ФЗ через ЮKassa (нужно ИП/ООО с «Чеками от ЮKassa»); самозанятым оставить 0
    yookassa_receipt: bool = field(default_factory=lambda: _env("YOOKASSA_SEND_RECEIPT", "0") == "1")
    yookassa_vat_code: int = field(default_factory=lambda: _int("YOOKASSA_VAT_CODE", 1))

    smtp_host: str = field(default_factory=lambda: _env("SMTP_HOST"))
    smtp_port: int = field(default_factory=lambda: _int("SMTP_PORT", 465))
    smtp_user: str = field(default_factory=lambda: _env("SMTP_USER"))
    smtp_password: str = field(default_factory=lambda: _env("SMTP_PASSWORD"))
    mail_from: str = field(default_factory=lambda: _env("MAIL_FROM"))

    admin_token: str = field(default_factory=lambda: _env("ADMIN_TOKEN"))
    metrika_id: str = field(default_factory=lambda: _env("METRIKA_ID"))

    seller_name: str = field(default_factory=lambda: _env("SELLER_NAME", "[ФИО или наименование продавца]"))
    seller_inn: str = field(default_factory=lambda: _env("SELLER_INN", "[ИНН]"))
    seller_status: str = field(default_factory=lambda: _env("SELLER_STATUS", "самозанятый (плательщик НПД)"))
    contact_email: str = field(default_factory=lambda: _env("CONTACT_EMAIL", "support@example.com"))
    contact_telegram: str = field(default_factory=lambda: _env("CONTACT_TELEGRAM"))

    max_upload_mb: int = field(default_factory=lambda: _int("MAX_UPLOAD_MB", 25))
    free_jobs_per_day: int = field(default_factory=lambda: _int("FREE_JOBS_PER_DAY", 6))
    free_jobs_per_hour: int = field(default_factory=lambda: _int("FREE_JOBS_PER_HOUR", 4))
    retention_days: int = field(default_factory=lambda: _int("RETENTION_DAYS", 7))
    rebuilds_per_order: int = field(default_factory=lambda: _int("REBUILDS_PER_ORDER", 3))
    trust_proxy: bool = field(default_factory=lambda: _env("TRUST_PROXY", "1") == "1")

    @property
    def db_path(self) -> str:
        return os.path.join(self.data_dir, "takt.sqlite3")

    @property
    def jobs_dir(self) -> str:
        return os.path.join(self.data_dir, "jobs")


settings = Settings()


def reload() -> Settings:
    """Для тестов: перечитать окружение."""
    global settings
    settings = Settings()
    return settings
