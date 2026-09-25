"""Проверка анкеты компании. Возвращает очищенные данные и ошибки по полям."""
from __future__ import annotations

import re
from datetime import date

FIELDS = {
    # имя: (обязательное, максимальная длина)
    "org_full": (True, 250),
    "org_short": (True, 120),
    "inn": (True, 12),
    "address": (False, 300),
    "city": (True, 80),
    "head_position": (True, 100),
    "head_name": (True, 120),
    "mode": (True, 10),
    "resp_position": (False, 100),
    "resp_name": (False, 120),
    "deputy_position": (False, 100),
    "deputy_name": (False, 120),
    "staff_total": (True, 5),
    "commissariat": (True, 250),
    "year": (True, 4),
    "sverka_month": (True, 2),
    "submit_method": (True, 10),
    "email": (True, 120),
}

EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,120}\.[^@\s]{2,24}$")
NAME_RE = re.compile(r"^[А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\-']+(\s+[А-ЯЁA-Z][А-ЯЁа-яёA-Za-z\-'.]*){1,3}$")


def inn_is_valid(inn: str) -> bool:
    """Контрольные суммы ИНН (10 цифр — организация, 12 — физлицо/ИП)."""
    if not inn.isdigit() or len(inn) not in (10, 12):
        return False
    d = [int(c) for c in inn]

    def check(weights: list[int], upto: int) -> int:
        return sum(w * d[i] for i, w in enumerate(weights[:upto])) % 11 % 10

    if len(inn) == 10:
        return check([2, 4, 10, 3, 5, 9, 4, 6, 8], 9) == d[9]
    return (
        check([7, 2, 4, 10, 3, 5, 9, 4, 6, 8], 10) == d[10]
        and check([3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8], 11) == d[11]
    )


def allowed_years(today: date | None = None) -> list[int]:
    today = today or date.today()
    return [today.year, today.year + 1]


def default_year(today: date | None = None) -> int:
    today = today or date.today()
    # С сентября готовят план на следующий год.
    return today.year + 1 if today.month >= 9 else today.year


def _clean(value: str) -> str:
    value = (value or "").replace("\r", " ").replace("\n", " ").replace("\t", " ")
    value = re.sub(r"\s{2,}", " ", value).strip()
    # Прямые кавычки -> ёлочки, чтобы документы выглядели аккуратно.
    if value.count('"') == 2:
        value = value.replace('"', "«", 1).replace('"', "»", 1)
    return value


def validate(form: dict[str, str], today: date | None = None) -> tuple[dict, dict[str, str]]:
    data: dict = {}
    errors: dict[str, str] = {}
    for name, (required, max_len) in FIELDS.items():
        value = _clean(form.get(name, ""))
        if len(value) > max_len:
            errors[name] = f"Не длиннее {max_len} символов"
        elif required and not value:
            errors[name] = "Заполните поле"
        data[name] = value[:max_len]

    if data["inn"] and "inn" not in errors and not inn_is_valid(data["inn"]):
        errors["inn"] = "ИНН не проходит проверку контрольной суммы — проверьте цифры"

    if data["mode"] not in ("self", "appoint"):
        errors["mode"] = "Выберите, кто ведёт воинский учёт"
    if data["mode"] == "appoint":
        for f in ("resp_position", "resp_name"):
            if not data[f]:
                errors[f] = "Укажите ответственного"
    for f in ("head_name", "resp_name", "deputy_name"):
        if data.get(f) and f not in errors and not NAME_RE.match(data[f]):
            errors[f] = "Укажите фамилию, имя и отчество полностью"
    if bool(data["deputy_name"]) != bool(data["deputy_position"]):
        errors["deputy_name" if not data["deputy_name"] else "deputy_position"] = "Заполните и должность, и ФИО замещающего"

    try:
        staff = int(data["staff_total"])
        if staff < 1:
            errors["staff_total"] = "Не меньше 1"
        elif staff >= 500:
            errors["staff_total"] = (
                "При 500 и более гражданах на учёте нужен освобождённый работник (п. 12 Положения № 719) — "
                "этот пакет рассчитан на небольшие организации"
            )
        data["staff_total"] = staff
    except ValueError:
        errors["staff_total"] = "Введите число"

    try:
        year = int(data["year"])
        if year not in allowed_years(today):
            raise ValueError
        data["year"] = year
    except ValueError:
        errors["year"] = "Выберите год из списка"

    try:
        month = int(data["sverka_month"])
        if not 1 <= month <= 12:
            raise ValueError
        data["sverka_month"] = month
    except ValueError:
        errors["sverka_month"] = "Выберите месяц"

    if data["submit_method"] not in ("epgu", "paper"):
        errors["submit_method"] = "Выберите способ"

    if data["email"] and not EMAIL_RE.match(data["email"]):
        errors["email"] = "Проверьте адрес почты"

    if form.get("consent") != "yes":
        errors["consent"] = "Нужно согласие с офертой и политикой обработки данных"

    return data, errors
