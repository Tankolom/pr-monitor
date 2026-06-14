"""
AI sentiment correction. After each срез the active LLM re-classifies the sentiment
of freshly collected mentions and OVERWRITES the rule-based label in the database,
so the dashboard shows accurate tonality (not just an accuracy estimate).

- run_collection_audit(): called automatically after a срез — corrects new mentions.
- correct_all_pending(): manual backfill — corrects everything not yet AI-verified.
"""
from __future__ import annotations

import json
import time

from .ai_provider import active_provider, ai_complete
from .config import load_config
from .db import connect, list_projects, mark_sentiment_kept, save_ai_audit, update_mention_sentiment, utc_now
from .logging_utils import get_logger

LOGGER = get_logger(__name__)

VALID_LABELS = {"positive", "neutral", "negative"}
SCORE = {"positive": 0.6, "neutral": 0.0, "negative": -0.6}
BATCH = 15

SYSTEM_PROMPT = (
    "Ты — эксперт по медиамониторингу и анализу тональности. Тебе присылают публикации, "
    "найденные автоматическим поиском по запросам проекта мониторинга. Для каждой "
    "публикации нужно сделать два вывода.\n"
    "1) relevant — действительно ли публикация говорит об объекте мониторинга (компании, "
    "персоне, проекте), а не о чём-то постороннем, что просто содержит совпадающие слова "
    "запроса в другом, обычном/общем значении (например, искомое слово — обычное "
    "существительное вроде «сфера», «расцвет», «горизонт» и обозначает не объект "
    "мониторинга, а отрасль/область/время года/другую сущность; или речь о другом "
    "человеке/компании с похожим именем). Если сомневаешься, но публикация в целом по "
    "теме и региону проекта — считай relevant=true.\n"
    "2) sentiment — тональность ПО ОТНОШЕНИЮ к объекту мониторинга: positive "
    "(благоприятная, успех, достижение, похвала), negative (критика, проблема, скандал, "
    "провал) или neutral (факт, анонс, нейтральное сообщение без оценки). Если "
    "relevant=false, ставь neutral.\n"
    "Отвечай строго JSON, без текста вне JSON."
)


def _parse_items(text: str) -> list | None:
    """Достаёт список оценок из ответа ИИ, устойчиво к формату:
    объект {"items":[...]}, голый массив [...], обёртка в ```json```."""
    if not text:
        return None
    cleaned = text.strip()
    # снять markdown-ограждения
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```", 2)[1] if cleaned.count("```") >= 2 else cleaned.strip("`")
        if cleaned.lstrip().lower().startswith("json"):
            cleaned = cleaned.lstrip()[4:]

    def _try(s: str):
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            return None

    candidates = [cleaned]
    # объект {...}
    ob, oe = cleaned.find("{"), cleaned.rfind("}")
    if ob != -1 and oe > ob:
        candidates.append(cleaned[ob : oe + 1])
    # массив [...]
    ab, ae = cleaned.find("["), cleaned.rfind("]")
    if ab != -1 and ae > ab:
        candidates.append(cleaned[ab : ae + 1])

    for cand in candidates:
        parsed = _try(cand)
        if parsed is None:
            continue
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            for key in ("items", "results", "data"):
                if isinstance(parsed.get(key), list):
                    return parsed[key]
            # один объект-оценка
            if "sentiment" in parsed:
                return [parsed]
    return None


def _project_context(project: dict | None, project_name: str) -> str:
    """Краткое описание проекта для ИИ: что мониторим и какие запросы используются —
    нужно, чтобы отличать упоминания объекта мониторинга от случайных совпадений слов.
    project — dict проекта из БД (или None, если проект уже удалён)."""
    if not project:
        return f"Проект мониторинга: «{project_name}»"
    lines = [f"Проект мониторинга: «{project_name}»"]
    queries = project.get("queries") or []
    if queries:
        lines.append("Поисковые запросы проекта: " + "; ".join(str(q) for q in queries[:8]))
    brand = project.get("brand") or {}
    brand_bits = []
    if brand.get("industry"):
        brand_bits.append(f"сфера деятельности — {brand['industry']}")
    if brand.get("city"):
        brand_bits.append(f"город/регион — {brand['city']}")
    if brand.get("website"):
        brand_bits.append(f"сайт — {brand['website']}")
    if brand.get("aliases"):
        brand_bits.append(f"другие названия/варианты — {brand['aliases']}")
    if brand_bits:
        lines.append("Профиль бренда: " + "; ".join(brand_bits))
    hint = (project.get("relevance_hint") or "").strip()
    if hint:
        lines.append("Пояснение, что считать релевантным: " + hint)
    return "\n".join(lines)


def _classify_batch(config: dict, project_ctx: str, rows: list[dict]) -> dict:
    """Возвращает {id публикации: {"sentiment": label, "relevant": bool}} для батча."""
    lines = []
    for item in rows:
        ctx = (item.get("snippet") or item.get("text") or "").strip().replace("\n", " ")
        title = (item.get("title") or "без заголовка").strip().replace("\n", " ")
        src = (item.get("source") or "").strip()
        lines.append(f'{item["id"]}. [{src}] Заголовок: {title[:200]} | Фрагмент: {ctx[:300]}')
    listing = "\n".join(lines)
    user_prompt = (
        f"{project_ctx}\n\n"
        "Для каждой публикации из списка определи relevant и sentiment (см. инструкцию). "
        "Верни строго JSON:\n"
        '{"items":[{"id":<id публикации>,"relevant":true|false,"sentiment":"positive|neutral|negative"}, ...]}\n\n'
        f"Публикации:\n{listing}"
    )
    # Сеть до облачного API бывает нестабильной — пара повторов на временные сбои.
    result = {"ok": False}
    for attempt in range(3):
        result = ai_complete(config, SYSTEM_PROMPT, user_prompt, max_tokens=1500)
        if result.get("ok"):
            break
        msg = (result.get("message") or "").lower()
        transient = any(s in msg for s in ("unreachable", "timed out", "timeout", "reset", "temporarily", "connection"))
        if not transient:
            break
        time.sleep(1.5)
    if not result.get("ok"):
        return {"_error": result.get("message", "ИИ не ответил")}
    items = _parse_items(result.get("text", ""))
    if items is None:
        return {"_error": "Не удалось разобрать ответ ИИ как JSON."}
    out = {}
    for entry in items:
        if not isinstance(entry, dict):
            continue
        try:
            mid = int(entry.get("id"))
        except (TypeError, ValueError):
            continue
        label = str(entry.get("sentiment", "")).strip().lower()
        if label not in VALID_LABELS:
            label = "neutral"
        relevant = entry.get("relevant", True)
        if isinstance(relevant, str):
            relevant = relevant.strip().lower() not in ("false", "0", "no", "нет", "")
        out[mid] = {"sentiment": label, "relevant": bool(relevant)}
    return out


def _fetch_targets(conn, since_iso: str | None, only_pending: bool, max_items: int) -> list[dict]:
    if since_iso:
        sql = ("SELECT id, project, title, snippet, text, source, sentiment, relevant FROM mentions "
               "WHERE collected_at >= ? ORDER BY id DESC LIMIT ?")
        params = (since_iso, max_items)
    elif only_pending:
        sql = ("SELECT id, project, title, snippet, text, source, sentiment, relevant FROM mentions "
               "WHERE COALESCE(sentiment_source,'rule') = 'rule' "
               "OR COALESCE(relevance_source,'pending') = 'pending' "
               "ORDER BY id DESC LIMIT ?")
        params = (max_items,)
    else:
        sql = ("SELECT id, project, title, snippet, text, source, sentiment, relevant FROM mentions "
               "ORDER BY id DESC LIMIT ?")
        params = (max_items,)
    return [dict(r) for r in conn.execute(sql, params).fetchall()]


def correct_sentiment(
    config_path: str = "config.json",
    run_id: int | None = None,
    since_iso: str | None = None,
    only_pending: bool = False,
    max_items: int = 80,
) -> dict:
    """Переразмечает тональность выбранных публикаций силами ИИ и пишет результат в БД.
    Никогда не бросает исключений — возвращает dict со статусом."""
    try:
        config = load_config(config_path)
    except Exception as exc:  # pragma: no cover
        return {"status": "failed", "message": f"Не удалось загрузить конфиг: {exc}"}

    provider = active_provider(config)
    if not provider:
        return {"status": "skipped", "message": "ИИ-провайдер не включён — коррекция пропущена."}

    conn = connect(config["database"])
    try:
        targets = _fetch_targets(conn, since_iso, only_pending, max_items)
        if not targets:
            return {"status": "skipped", "message": "Нет публикаций для проверки тональности."}

        # Группируем по проекту — так каждой пачке публикаций можно дать контекст
        # о том, что именно мониторим, и ИИ сможет отличить объект мониторинга от
        # случайных совпадений слов запроса (например, «Сфера» — коворкинг, а не
        # «сфера деятельности»).
        by_project: dict[str, list[dict]] = {}
        for item in targets:
            by_project.setdefault(item.get("project") or "", []).append(item)

        # карта проектов из БД (для контекста ИИ: бренд, запросы, подсказка релевантности)
        projects_by_name = {p["name"]: p for p in list_projects(conn)}

        # checked/agree/corrected считаются ТОЛЬКО по релевантным публикациям —
        # тональность нерелевантных публикаций не входит в статистику дашборда,
        # поэтому её "уточнение" не должно фигурировать в метрике коррекции.
        total_processed = checked = agree = corrected = kept = excluded = 0
        details = []
        last_error = None
        for project_name, items in by_project.items():
            project_ctx = _project_context(projects_by_name.get(project_name), project_name)
            for start in range(0, len(items), BATCH):
                batch = items[start : start + BATCH]
                results = _classify_batch(config, project_ctx, batch)
                if "_error" in results:
                    last_error = results["_error"]
                    # Часто весь батч отклоняется из-за одной чувствительной публикации.
                    # Пробуем поштучно, чтобы спасти остальные.
                    results = {}
                    for one in batch:
                        single = _classify_batch(config, project_ctx, [one])
                        if "_error" not in single:
                            results.update(single)
                    unresolved = [it["id"] for it in batch if it["id"] not in results]
                    if unresolved:
                        mark_sentiment_kept(conn, unresolved)
                        kept += len(unresolved)
                        conn.commit()
                    if not results:
                        continue
                for item in batch:
                    res = results.get(item["id"])
                    if not res:
                        continue
                    ai_label = res["sentiment"]
                    ai_relevant = res["relevant"]
                    old = (item.get("sentiment") or "neutral").lower()
                    old_relevant = bool(item.get("relevant", 1))
                    total_processed += 1
                    changed = ai_label != old
                    if ai_relevant:
                        checked += 1
                        if changed:
                            corrected += 1
                        else:
                            agree += 1
                    else:
                        excluded += 1
                    # помечаем как проверенное ИИ (тональность + релевантность), чтобы не перепроверять
                    update_mention_sentiment(conn, item["id"], ai_label, SCORE[ai_label], "ai", relevant=ai_relevant)
                    details.append({
                        "project": project_name,
                        "title": (item.get("title") or "без заголовка")[:160],
                        "source": item.get("source") or "",
                        "rule": old,
                        "ai": ai_label,
                        "changed": changed,
                        "relevant": ai_relevant,
                        "relevance_changed": ai_relevant != old_relevant,
                    })
                conn.commit()  # фиксируем после каждого батча — короче блокировки, частичный прогресс сохраняется

        if total_processed == 0:
            status = "ok" if kept else "failed"
            audit = {
                "run_id": run_id, "created_at": utc_now(), "provider": provider,
                "checked": 0, "agreement": None, "mismatches": [], "details": [],
                "verdict": "", "status": status,
                "message": (f"ИИ отказался размечать {kept} публикаций (контент-фильтр) — оставлены со словарной оценкой."
                            if kept else (last_error or "ИИ не вернул ни одной оценки.")),
            }
            save_ai_audit(conn, audit)
            return audit

        agreement = round(100 * agree / checked, 1) if checked else None
        mismatches = [d for d in details if d["changed"] and d["relevant"]]
        verdict = (
            f"ИИ проверил {total_processed} публикаций"
            + (f", из них {excluded} признаны нерелевантными выборке и исключены из статистики" if excluded else "")
            + f". Среди {checked} релевантных тональность уточнена у {corrected}"
            + (f" (авторазметка совпала с ИИ в {agreement}% случаев)" if agreement is not None else "")
            + " — цифры на дашборде теперь отражают экспертную оценку ИИ."
        )
        audit = {
            "run_id": run_id, "created_at": utc_now(), "provider": provider,
            "checked": checked, "agreement": agreement,
            "mismatches": mismatches[:20], "details": details,
            "excluded": excluded,
            "verdict": verdict, "status": "ok",
            "message": (f"Проверено {total_processed}, релевантных {checked} (уточнено {corrected})"
                         + (f", исключено как нерелевантные {excluded}" if excluded else "")
                         + (f", пропущено {kept}" if kept else "")),
        }
        save_ai_audit(conn, audit)
        LOGGER.info("AI correction: provider=%s checked=%s corrected=%s excluded=%s", provider, checked, corrected, excluded)
        return audit
    except Exception as exc:  # pragma: no cover
        LOGGER.exception("AI sentiment correction failed")
        return {"status": "failed", "message": str(exc)}
    finally:
        conn.close()


def run_collection_audit(config_path: str = "config.json", run_id: int | None = None,
                         since_iso: str | None = None, sample_size: int = 80) -> dict:
    """Хук после среза: корректирует тональность новых публикаций этого среза."""
    return correct_sentiment(config_path, run_id=run_id, since_iso=since_iso, max_items=sample_size)


def correct_all_pending(config_path: str = "config.json", max_items: int = 200) -> dict:
    """Ручной бэкафилл: уточнить тональность всех ещё не проверенных ИИ публикаций."""
    return correct_sentiment(config_path, only_pending=True, max_items=max_items)
