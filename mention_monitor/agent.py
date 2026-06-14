from __future__ import annotations

import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlparse

import sqlite3


STOP_WORDS = {
    "это",
    "как",
    "что",
    "для",
    "или",
    "при",
    "про",
    "над",
    "под",
    "без",
    "уже",
    "еще",
    "ещё",
    "после",
    "будет",
    "были",
    "был",
    "была",
    "его",
    "она",
    "они",
    "все",
    "всё",
    "россии",
    "россия",
    "российский",
    "российские",
    "российских",
    "новости",
    "фото",
    "видео",
    "года",
    "году",
}


def _date_expr() -> str:
    return """
    CASE
      WHEN published_at GLOB '????-??-??*' THEN substr(published_at, 1, 10)
      ELSE substr(collected_at, 1, 10)
    END
    """


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value[:10]).date()
    except Exception:
        return None


def _fmt_date(value: date | None) -> str:
    return value.isoformat() if value else "нет даты"


def _pct(part: int, total: int) -> int:
    return round(part / total * 100) if total else 0


def _delta(current: int, previous: int, no_history: bool = False) -> tuple[int, str]:
    if previous == 0:
        if current == 0:
            return 0, "без изменений"
        if no_history:
            # First collection — no comparable previous period exists
            return 0, "первый сбор"
        return 100, "новый всплеск"
    if previous < 5 and current > previous:
        return 100, "резкий рост"
    value = round((current - previous) / previous * 100)
    if value > 0:
        return value, f"+{value}%"
    if value < 0:
        return value, f"{value}%"
    return 0, "без изменений"


def _where(project: str, start: date | None = None, end: date | None = None, sentiment: str = "all", search: str = "", account_id: int | None = None):
    where = ["COALESCE(relevant, 1) = 1"]
    params: list[str] = []
    if account_id is not None:
        where.append("account_id = ?")
        params.append(account_id)
    if project and project != "all":
        where.append("project = ?")
        params.append(project)
    date_expr = _date_expr()
    if start:
        where.append(date_expr + " >= ?")
        params.append(start.isoformat())
    if end:
        where.append(date_expr + " <= ?")
        params.append(end.isoformat())
    if sentiment and sentiment != "all":
        where.append("sentiment = ?")
        params.append(sentiment)
    if search:
        where.append("(title LIKE ? OR snippet LIKE ? OR text LIKE ? OR source LIKE ?)")
        needle = f"%{search}%"
        params.extend([needle, needle, needle, needle])
    return (" WHERE " + " AND ".join(where)) if where else "", params


def _scalar(conn: sqlite3.Connection, sql: str, params: list[str]) -> int:
    return int(conn.execute(sql, params).fetchone()["n"] or 0)


def _window_stats(
    conn: sqlite3.Connection,
    project: str,
    start: date | None,
    end: date | None,
    sentiment: str = "all",
    search: str = "",
    account_id: int | None = None,
) -> dict:
    suffix, params = _where(project, start, end, sentiment, search, account_id)
    total = _scalar(conn, "SELECT COUNT(*) AS n FROM mentions" + suffix, params)
    unique_sources = _scalar(conn, "SELECT COUNT(DISTINCT COALESCE(source, 'unknown')) AS n FROM mentions" + suffix, params)
    tone = {
        row["sentiment"]: int(row["n"])
        for row in conn.execute(
            "SELECT sentiment, COUNT(*) AS n FROM mentions" + suffix + " GROUP BY sentiment",
            params,
        )
    }
    top_sources = [
        dict(row)
        for row in conn.execute(
            "SELECT COALESCE(source, 'unknown') AS source, COUNT(*) AS n FROM mentions"
            + suffix
            + " GROUP BY source ORDER BY n DESC LIMIT 8",
            params,
        )
    ]
    top_queries = [
        dict(row)
        for row in conn.execute(
            "SELECT query, COUNT(*) AS n FROM mentions" + suffix + " GROUP BY query ORDER BY n DESC LIMIT 8",
            params,
        )
    ]
    latest = [
        dict(row)
        for row in conn.execute(
            "SELECT title, snippet, url, source, sentiment, COALESCE(published_at, collected_at) AS date_value FROM mentions"
            + suffix
            + " ORDER BY date_value DESC LIMIT 12",
            params,
        )
    ]
    return {
        "total": total,
        "unique_sources": unique_sources,
        "tone": tone,
        "positive": tone.get("positive", 0),
        "neutral": tone.get("neutral", 0),
        "negative": tone.get("negative", 0),
        "negative_share": _pct(tone.get("negative", 0), total),
        "positive_share": _pct(tone.get("positive", 0), total),
        "top_sources": top_sources,
        "top_queries": top_queries,
        "latest": latest,
    }


def _project_date_bounds(conn: sqlite3.Connection, project: str, account_id: int | None = None) -> tuple[date | None, date | None]:
    where = ["COALESCE(relevant, 1) = 1"]
    params: list = []
    if account_id is not None:
        where.append("account_id = ?")
        params.append(account_id)
    if project and project != "all":
        where.append("project = ?")
        params.append(project)
    row = conn.execute(
        f"SELECT MIN({_date_expr()}) AS first_day, MAX({_date_expr()}) AS last_day FROM mentions "
        "WHERE " + " AND ".join(where),
        params,
    ).fetchone()
    return _parse_date(row["first_day"]), _parse_date(row["last_day"])


def _source_domain(source_or_url: str) -> str:
    parsed = urlparse(source_or_url or "")
    if parsed.netloc:
        return parsed.netloc.replace("www.", "")
    return source_or_url or "unknown"


def _theme_words(rows: list[dict], limit: int = 12) -> list[dict]:
    counts: dict[str, int] = {}
    for row in rows:
        text = " ".join([row.get("title") or "", row.get("snippet") or ""]).lower().replace("ё", "е")
        for word in re.findall(r"[а-яa-z0-9-]{4,}", text):
            if word in STOP_WORDS:
                continue
            counts[word] = counts.get(word, 0) + 1
    return [{"word": word, "n": n} for word, n in sorted(counts.items(), key=lambda item: item[1], reverse=True)[:limit]]


def _risk_level(current: dict, source_concentration: int, growth_value: int) -> tuple[str, str]:
    if current["negative_share"] >= 25:
        return "Высокий", "существенная доля негатива"
    if growth_value >= 80 and current["total"] >= 15:
        return "Средний", "резкий рост упоминаний"
    if source_concentration >= 55 and current["total"] >= 10:
        return "Средний", "обсуждение сконцентрировано в узком круге источников"
    if current["total"] == 0:
        return "Нет данных", "сначала нужен сбор по проекту"
    return "Низкий", "критичных сигналов в выборке нет"


def _recommendations(current: dict, previous: dict, growth_value: int, themes: list[dict]) -> list[str]:
    items = []
    if current["total"] == 0:
        return [
            "Запустить срез новостей по проекту и оставить расширение запроса включенным.",
            "Проверить, что подключены Google News, Яндекс или Serper и федеральные/региональные RSS.",
        ]
    if growth_value > 30:
        items.append("Разобрать причины всплеска: какие источники первыми дали публикации и какие сюжеты пошли в перепечатку.")
    elif growth_value < -30:
        items.append("Проверить, не выдохся ли инфоповод: для PR-кампании стоит поддержать вторую волну публикаций.")
    else:
        items.append("Держать текущий режим сбора и сравнивать новые запуски с этим периодом как с базовой линией.")
    if current["negative_share"] > 0:
        items.append("Просмотреть негативные публикации вручную и отметить ошибочные тональности для будущего дообучения.")
    if current["unique_sources"] < max(5, current["total"] // 4):
        items.append("Расширить поисковые формулировки и подключить дополнительные новостные агрегаторы, чтобы повысить разнообразие источников.")
    if themes:
        items.append(f"Использовать ведущую тему “{themes[0]['word']}” для уточнения запросов и группировки сюжетов.")
    if previous["total"] == 0 and current["total"] > 0:
        items.append("Зафиксировать этот запуск как стартовую ретро-точку проекта.")
    return items[:5]


def analyze_project(
    conn: sqlite3.Connection,
    config: dict,
    project: str,
    sentiment: str = "all",
    search: str = "",
    collected_from: str = "",
    collected_to: str = "",
    account_id: int | None = None,
) -> dict:
    first_day, last_day = _project_date_bounds(conn, project, account_id)
    requested_start = _parse_date(collected_from)
    requested_end = _parse_date(collected_to)
    if requested_start or requested_end:
        current_start = requested_start or first_day
        current_end = requested_end or last_day
    else:
        current_end = last_day or datetime.now(timezone.utc).date()
        current_start = current_end - timedelta(days=29)
    if current_start and current_end and current_start > current_end:
        current_start, current_end = current_end, current_start

    window_days = 30
    if current_start and current_end:
        window_days = max(1, (current_end - current_start).days + 1)
    previous_end = current_start - timedelta(days=1) if current_start else None
    previous_start = previous_end - timedelta(days=window_days - 1) if previous_end else None

    current = _window_stats(conn, project, current_start, current_end, sentiment, search, account_id)
    previous = _window_stats(conn, project, previous_start, previous_end, sentiment, search, account_id)
    history = _window_stats(conn, project, first_day, last_day, "all", "", account_id)

    # no_history: previous period has no data because ALL data was collected in the current window
    no_history = previous["total"] == 0 and (first_day is None or (current_start is not None and first_day >= current_start))
    growth_value, growth_label = _delta(current["total"], previous["total"], no_history=no_history)
    source_growth_value, source_growth_label = _delta(current["unique_sources"], previous["unique_sources"], no_history=no_history)
    top_source_count = int(current["top_sources"][0]["n"]) if current["top_sources"] else 0
    source_concentration = _pct(top_source_count, current["total"])
    themes = _theme_words(current["latest"], limit=12)
    risk_level, risk_reason = _risk_level(current, source_concentration, growth_value)

    if project == "all":
        context_queries = []
        for item in config.get("projects", []):
            context_queries.extend(item.get("queries", []))
        project_context = {"queries": context_queries, "owner": "все пользователи"}
    else:
        project_context = next((item for item in config.get("projects", []) if item.get("name") == project), {})
    return {
        "project": project,
        "filters": {
            "sentiment": sentiment,
            "search": search,
            "current_start": _fmt_date(current_start),
            "current_end": _fmt_date(current_end),
            "previous_start": _fmt_date(previous_start),
            "previous_end": _fmt_date(previous_end),
        },
        "context": {
            "queries": project_context.get("queries", []),
            "owner": project_context.get("owner", ""),
            "history_first_day": _fmt_date(first_day),
            "history_last_day": _fmt_date(last_day),
            "history_total": history["total"],
            "history_sources": history["unique_sources"],
        },
        "current": current,
        "previous": previous,
        "growth": {
            "mentions": growth_label,
            "mentions_value": growth_value,
            "sources": source_growth_label,
            "sources_value": source_growth_value,
        },
        "risk": {
            "level": risk_level,
            "reason": risk_reason,
            "source_concentration": source_concentration,
        },
        "themes": themes,
        "recommendations": _recommendations(current, previous, growth_value, themes),
    }
