"""
Тарифы и квоты PR Monitor (чистая логика, без БД).

Ось тарифа: число проектов + поисковых запросов + пользователей.
ИИ-анализ включён на всех платных тарифах одинаково.
Квоту можно переопределить индивидуально на уровне аккаунта (поля quota_* в accounts);
None означает «безлимит» (для Enterprise или индивидуальных договорённостей).
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

# Размерности квот: ключ в PLANS -> поле-override в accounts -> поле потребления в usage
QUOTA_DIMENSIONS = ("projects", "queries", "users")

PLANS: dict[str, dict] = {
    "trial": {
        "key": "trial", "title": "Trial", "projects": 1, "queries": 5, "users": 1,
        "price": 0, "trial_days": 14,
        "blurb": "14 дней бесплатно — попробовать на одном бренде.",
    },
    "start": {
        "key": "start", "title": "Старт", "projects": 1, "queries": 30, "users": 1,
        "price": 3900,
        "blurb": "Один бренд, полный ИИ-анализ. Для ИП и небольших компаний.",
    },
    "business": {
        "key": "business", "title": "Бизнес", "projects": 5, "queries": 200, "users": 3,
        "price": 11900,
        "blurb": "До 5 брендов, командный доступ, отчёты. Ядро для среднего бизнеса.",
    },
    "agency": {
        "key": "agency", "title": "Агентство", "projects": 20, "queries": 500, "users": 10,
        "price": 29900,
        "blurb": "До 20 проектов и API — для агентств, ведущих клиентов.",
    },
    "enterprise": {
        "key": "enterprise", "title": "Enterprise", "projects": None, "queries": None, "users": None,
        "price": None,
        "blurb": "Без ограничений, по договору.",
    },
}

# Порядок тарифов (для апгрейда/даунгрейда и сортировки в UI)
PLAN_ORDER = ["trial", "start", "business", "agency", "enterprise"]

# Тарифы, которые клиент может купить сам (без Enterprise/Trial — их назначает админ)
SELLABLE_PLANS = ["start", "business", "agency"]

ACCOUNT_STATUSES = {
    "trial": "Пробный период",
    "active": "Активна",
    "past_due": "Просрочена оплата",
    "suspended": "Заморожена",
    "canceled": "Отменена",
}

# Скидка при оплате за год (12 мес).
ANNUAL_DISCOUNT = 0.20

# Частоты автоматического сбора (часы). Пол — не чаще 3 часов.
COLLECTION_INTERVALS = [3, 6, 12, 24, 48]
DEFAULT_COLLECTION_INTERVAL = 3
MIN_COLLECTION_INTERVAL = 3


def plan_def(plan: str) -> dict:
    """Определение тарифа; неизвестный план трактуем как trial."""
    return PLANS.get(plan or "trial", PLANS["trial"])


def plan_title(plan: str) -> str:
    return plan_def(plan).get("title", plan or "—")


def plan_limit(plan: str, dimension: str):
    """Лимит тарифа по размерности (projects/queries/users). None = безлимит."""
    return plan_def(plan).get(dimension)


def plan_amount(plan: str, months: int) -> int:
    """Сумма к оплате (₽) за N месяцев тарифа. За год (12 мес) — скидка ANNUAL_DISCOUNT.
    Возвращает 0 для тарифов без цены (trial/enterprise)."""
    price = plan_def(plan).get("price") or 0
    months = max(1, int(months))
    total = price * months
    if months >= 12:
        total = total * (1 - ANNUAL_DISCOUNT)
    return int(round(total))


def effective_quota(account: dict | None, dimension: str):
    """Действующий лимит аккаунта: индивидуальный override, иначе лимит тарифа.
    Возвращает int или None (None = безлимит)."""
    if not account:
        return plan_limit("trial", dimension)
    override = account.get(f"quota_{dimension}")
    if override is not None:
        return override
    return plan_limit(account.get("plan", "trial"), dimension)


def effective_quotas(account: dict | None) -> dict:
    return {dim: effective_quota(account, dim) for dim in QUOTA_DIMENSIONS}


def quota_reached(limit, used: int) -> bool:
    """Достигнут ли потолок. limit=None означает безлимит."""
    if limit is None:
        return False
    return used >= limit


def quota_remaining(limit, used: int):
    if limit is None:
        return None
    return max(0, limit - used)


def usage_ratio(limit, used: int) -> float:
    """Доля использования 0..1 (для индикаторов и предупреждений на 80%)."""
    if limit is None or limit <= 0:
        return 0.0
    return min(1.0, used / limit)


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def account_is_active(account: dict | None, now: datetime | None = None) -> bool:
    """Аккаунт может пользоваться сервисом: статус trial/active и срок не истёк."""
    if not account:
        return False
    status = account.get("status", "trial")
    if status not in ("trial", "active"):
        return False
    period_end = _parse_iso(account.get("period_end"))
    if period_end is None:
        # trial без срока считаем активным; active без срока — тоже (бессрочный/договор)
        return True
    return period_end > (now or datetime.now(timezone.utc))


def account_days_left(account: dict | None, now: datetime | None = None) -> int | None:
    period_end = _parse_iso((account or {}).get("period_end"))
    if period_end is None:
        return None
    delta = period_end - (now or datetime.now(timezone.utc))
    return max(0, delta.days)


def period_end_after(months: int, start: datetime | None = None) -> str:
    """ISO-дата окончания периода через N месяцев (приблизительно, 30 дней/мес)."""
    base = start or datetime.now(timezone.utc)
    return (base + timedelta(days=30 * max(1, months))).replace(microsecond=0).isoformat()


def trial_period_end(days: int = 14, start: datetime | None = None) -> str:
    base = start or datetime.now(timezone.utc)
    return (base + timedelta(days=max(1, days))).replace(microsecond=0).isoformat()


def _amount(p: dict) -> float:
    try:
        return float(p.get("amount") or 0)
    except (TypeError, ValueError):
        return 0.0


def finance_summary(accounts: list[dict], payments: list[dict], now: datetime | None = None) -> dict:
    """Сводный финансовый отчёт по платформе (чистая функция, без БД).
    accounts/payments — списки dict из БД."""
    now = now or datetime.now(timezone.utc)
    cutoff = now - timedelta(days=30)
    succeeded = [p for p in payments if (p.get("status") or "succeeded") == "succeeded"]

    total_revenue = sum(_amount(p) for p in succeeded)
    revenue_30d = sum(_amount(p) for p in succeeded if (_parse_iso(p.get("created_at")) or now) >= cutoff
                      and _parse_iso(p.get("created_at")) is not None)

    # выручка по месяцам — последние 12
    ym: dict[str, float] = {}
    for p in succeeded:
        d = _parse_iso(p.get("created_at"))
        if d:
            ym[d.strftime("%Y-%m")] = ym.get(d.strftime("%Y-%m"), 0.0) + _amount(p)
    keys, y, m = [], now.year, now.month
    for _ in range(12):
        keys.append(f"{y:04d}-{m:02d}")
        m -= 1
        if m == 0:
            m, y = 12, y - 1
    revenue_by_month = [{"month": k, "amount": round(ym.get(k, 0.0))} for k in reversed(keys)]

    paying = [a for a in accounts if account_is_active(a, now) and a.get("plan") in SELLABLE_PLANS]
    paying_active = len(paying)
    mrr = sum(plan_def(a.get("plan")).get("price") or 0 for a in paying)
    arpu = round(mrr / paying_active) if paying_active else 0

    by_plan: dict[str, int] = {}
    for a in accounts:
        if account_is_active(a, now):
            by_plan[a.get("plan", "trial")] = by_plan.get(a.get("plan", "trial"), 0) + 1

    # новые платящие за 30 дней — по первому успешному платежу аккаунта
    first_payment: dict = {}
    for p in sorted(succeeded, key=lambda x: x.get("created_at") or ""):
        aid = p.get("account_id")
        if aid not in first_payment:
            first_payment[aid] = _parse_iso(p.get("created_at"))
    new_paying_30d = sum(1 for d in first_payment.values() if d and d >= cutoff)

    # отток за 30 дней — платный аккаунт, который перестал быть активным
    churned = 0
    for a in accounts:
        if a.get("plan") not in SELLABLE_PLANS or account_is_active(a, now):
            continue
        pe = _parse_iso(a.get("period_end"))
        if a.get("status") == "canceled" or (pe and cutoff <= pe <= now):
            churned += 1

    return {
        "total_revenue": round(total_revenue),
        "revenue_30d": round(revenue_30d),
        "revenue_by_month": revenue_by_month,
        "paying_active": paying_active,
        "mrr": mrr,
        "arpu": arpu,
        "by_plan": by_plan,
        "new_paying_30d": new_paying_30d,
        "churn_30d": churned,
        "total_accounts": len(accounts),
        "payments_count": len(succeeded),
    }


def normalize_collection_interval(hours) -> int:
    """Приводит выбор частоты к допустимому значению (пол — 3 часа)."""
    try:
        value = int(hours)
    except (TypeError, ValueError):
        return DEFAULT_COLLECTION_INTERVAL
    if value < MIN_COLLECTION_INTERVAL:
        return MIN_COLLECTION_INTERVAL
    # ближайшее допустимое значение из списка, не меньше выбранного
    for allowed in COLLECTION_INTERVALS:
        if value <= allowed:
            return allowed
    return COLLECTION_INTERVALS[-1]
