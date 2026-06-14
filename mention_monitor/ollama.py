from __future__ import annotations

import json

from .fetch import fetch_url, post_json


DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "qwen2.5:1.5b"


def ollama_config(config: dict) -> dict:
    ai = config.setdefault("ai", {})
    return {
        "enabled": bool(ai.get("ollama_enabled", False)),
        "base_url": (ai.get("ollama_base_url") or DEFAULT_BASE_URL).rstrip("/"),
        "model": ai.get("ollama_model") or DEFAULT_MODEL,
        "timeout": int(ai.get("ollama_timeout", 45) or 45),
    }


def ollama_status(config: dict) -> dict:
    settings = ollama_config(config)
    try:
        payload, _ = fetch_url(settings["base_url"] + "/api/tags", config.get("user_agent", "MentionMonitor"), timeout=5)
        parsed = json.loads(payload)
        models = [item.get("name", "") for item in parsed.get("models", [])]
        model_ready = settings["model"] in models or any(name.startswith(settings["model"] + ":") for name in models)
        return {
            "ok": True,
            "enabled": settings["enabled"],
            "base_url": settings["base_url"],
            "model": settings["model"],
            "model_ready": model_ready,
            "models": models[:20],
            "message": "Ollama отвечает" if model_ready else "Ollama отвечает, но выбранная модель не найдена",
        }
    except Exception as exc:
        return {
            "ok": False,
            "enabled": settings["enabled"],
            "base_url": settings["base_url"],
            "model": settings["model"],
            "model_ready": False,
            "models": [],
            "message": str(exc),
        }


def build_analysis_prompt(analysis: dict) -> str:
    current = analysis["current"]
    previous = analysis["previous"]
    risk = analysis["risk"]
    themes = ", ".join(f"{item['word']} ({item['n']})" for item in analysis["themes"][:10]) or "нет явных тем"
    sources = ", ".join(f"{item['source']} ({item['n']})" for item in current["top_sources"][:8]) or "нет источников"
    queries = ", ".join(f"{item['query']} ({item['n']})" for item in current["top_queries"][:8]) or "нет запросов"
    latest = "\n".join(
        f"- {item.get('title') or 'без заголовка'} | {item.get('source') or 'unknown'} | {item.get('sentiment')} | {item.get('date_value') or 'нет даты'}"
        for item in current["latest"][:10]
    )
    context_queries = "\n".join(f"- {query}" for query in analysis["context"].get("queries", [])[:10]) or "- не заданы"
    return f"""
Ты — старший стратег по коммуникациям и медиа-аналитик уровня «Медиалогии» / Brandwatch.
Твоя задача — дать экспертный разбор медиаполя проекта на русском языке, как для брифинга
руководителю пресс-службы или владельцу репутации. Думай как профессионал: за цифрами видь
смысл, репутационную динамику, расстановку источников и сигналы раннего предупреждения.

ПРИНЦИПЫ:
- Опирайся ТОЛЬКО на данные ниже. Ни одного выдуманного факта, имени, цитаты или числа.
- Если данных не хватает для вывода — прямо скажи об этом, не додумывай.
- Не пиши банальности («поддерживать позитив», «работать с аудиторией»). Каждое утверждение
  должно опираться на конкретный показатель, источник или публикацию из выборки.
- Тональность здесь размечена автоматическим словарным алгоритмом — относись к ней критически,
  отмечай, где разметка может быть ненадёжной (ирония, цитаты, нейтральные перепечатки).

Проект: {analysis['project']}
Период анализа: {analysis['filters']['current_start']} — {analysis['filters']['current_end']}
Запросы проекта (по ним собрана выборка):
{context_queries}

Текущий период:
- упоминаний: {current['total']}
- уникальных источников: {current['unique_sources']}
- позитив: {current['positive']} ({current['positive_share']}%)
- нейтрально: {current['neutral']}
- негатив: {current['negative']} ({current['negative_share']}%)

Предыдущий сопоставимый период:
- упоминаний: {previous['total']}
- источников: {previous['unique_sources']}

Динамика и риск:
- упоминания: {analysis['growth']['mentions']}
- источники: {analysis['growth']['sources']}
- системный риск: {risk['level']} ({risk['reason']})
- концентрация главного источника: {risk['source_concentration']}%

Ключевые темы/слова: {themes}
Топ источников: {sources}
Сработавшие запросы: {queries}

Последние публикации (заголовок | источник | тональность | дата):
{latest}

Выдай структурированный разбор ровно по этим блокам (без Markdown-звёздочек):

РЕЗЮМЕ ДЛЯ РУКОВОДИТЕЛЯ
2–4 предложения с ключевыми цифрами: что произошло с медиаполем за период и насколько это
важно для репутации. Дай явную оценку: фон позитивный / нейтральный / тревожный и почему.

ЧТО ГОВОРЯТ ДАННЫЕ
4–5 пунктов глубокого разбора: динамика объёма и её вероятная причина (инфоповод?), структура
тональности и её интерпретация, картина источников (федеральные/региональные/отраслевые,
концентрация, есть ли единый драйвер перепечаток), какие сюжеты/темы доминируют.

РЕПУТАЦИОННЫЙ ВЗГЛЯД
2–3 пункта: как эта картина читается с точки зрения восприятия проекта/персоны. Где сильные
стороны нарратива, где уязвимости. Есть ли негативные сюжеты, требующие реакции.

СИГНАЛЫ И РИСКИ
2–3 пункта: риски интерпретации данных (дубли, перекос источников, слабая разметка тональности,
узкий охват) И репутационные риски, если они видны в выборке. Отдели одно от другого.

РЕКОМЕНДАЦИИ
3–4 конкретных действия: что сделать в системе мониторинга (расширить источники, проверить
дубли, уточнить запросы) и какие коммуникационные шаги напрашиваются по данным выборки.
""".strip()


def build_chat_prompt(analysis: dict, question: str) -> str:
    current = analysis["current"]
    previous = analysis["previous"]
    themes = ", ".join(f"{item['word']} ({item['n']})" for item in analysis["themes"][:12]) or "нет явных тем"
    sources = "\n".join(f"- {item['source']}: {item['n']}" for item in current["top_sources"][:10]) or "- нет источников"
    queries = "\n".join(f"- {item['query']}: {item['n']}" for item in current["top_queries"][:10]) or "- нет сработавших запросов"
    latest = "\n".join(
        f"- {item.get('title') or 'без заголовка'} | {item.get('source') or 'unknown'} | {item.get('sentiment')} | {item.get('date_value') or 'нет даты'} | {item.get('snippet') or ''}"
        for item in current["latest"][:14]
    ) or "- публикаций в выборке нет"
    context_queries = "\n".join(f"- {query}" for query in analysis["context"].get("queries", [])[:14]) or "- не заданы"
    return f"""
Ты — старший PR-аналитик и медиа-стратег внутри SaaS-платформы мониторинга СМИ.
Пользователь задаёт вопрос по уже собранной выборке. Отвечай как эксперт: не просто
пересказывай цифры, а объясняй, что они значат для репутации и какие выводы из них следуют.

ПРИНЦИПЫ:
- Отвечай ТОЛЬКО по данным ниже. Если данных мало — прямо скажи, каких именно не хватает и
  какой фильтр или сбор запустить, чтобы ответить точнее.
- Не выдумывай факты, имена, цитаты и числа. Нет данных — так и говори.
- У тебя нет доступа в интернет, только контекст системы. Не предлагай «погуглить».
- Тональность размечена автоматическим алгоритмом — учитывай возможные ошибки разметки.
- Пиши по-русски, конкретно, по делу. Без Markdown-заголовков со звёздочками.

Проект: {analysis['project']}
Период выборки: {analysis['filters']['current_start']} — {analysis['filters']['current_end']}
Фильтр тональности: {analysis['filters']['sentiment']}
Поиск внутри выборки: {analysis['filters']['search'] or 'нет'}

Запросы проекта:
{context_queries}

Текущий период:
- упоминаний: {current['total']}
- источников: {current['unique_sources']}
- позитив: {current['positive']} ({current['positive_share']}%)
- нейтрально: {current['neutral']}
- негатив: {current['negative']} ({current['negative_share']}%)

Предыдущий сопоставимый период:
- упоминаний: {previous['total']}
- источников: {previous['unique_sources']}
- динамика упоминаний: {analysis['growth']['mentions']}
- динамика источников: {analysis['growth']['sources']}

История проекта:
- всего публикаций в базе: {analysis['context']['history_total']}
- всего источников в базе: {analysis['context']['history_sources']}
- первый день: {analysis['context']['history_first_day']}
- последний день: {analysis['context']['history_last_day']}

Риск системы: {analysis['risk']['level']} ({analysis['risk']['reason']})
Концентрация главного источника: {analysis['risk']['source_concentration']}%
Темы: {themes}

Топ источников:
{sources}

Сработавшие запросы:
{queries}

Последние публикации:
{latest}

Вопрос пользователя:
{question}

Структура ответа:
1. Прямой и содержательный ответ на вопрос — с опорой на конкретные цифры и источники.
2. Экспертная интерпретation: что это значит для репутации/медиаполя, а не только «сколько».
3. Доказательства из выборки (источники, публикации, показатели).
4. Ограничения данных и оговорки (надёжность тональности, охват, дубли).
5. Что сделать в системе или в коммуникациях дальше, если нужно уточнение или реакция.
""".strip()


def complete_ollama(config: dict, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> dict:
    """Low-level single-turn completion for internal tasks (audit, health checks)."""
    settings = ollama_config(config)
    payload = {
        "model": settings["model"],
        "stream": False,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "options": {"temperature": 0.1, "num_predict": max_tokens or 700},
    }
    try:
        raw, _ = post_json(
            settings["base_url"] + "/api/chat",
            payload,
            config.get("user_agent", "MentionMonitor"),
            timeout=settings["timeout"],
        )
        parsed = json.loads(raw)
        text = (parsed.get("message") or {}).get("content", "").strip()
        return {"ok": bool(text), "text": text, "provider": "ollama", "model": settings["model"], "message": "Ответ получен" if text else "Пустой ответ"}
    except Exception as exc:
        return {"ok": False, "text": "", "provider": "ollama", "model": settings["model"], "message": str(exc)}


def generate_ollama_analysis(config: dict, analysis: dict) -> dict:
    settings = ollama_config(config)
    if not settings["enabled"]:
        return {"enabled": False, "ok": False, "text": "", "message": "Локальная ИИ выключена в настройках."}

    prompt = build_analysis_prompt(analysis)
    payload = {
        "model": settings["model"],
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "Ты опытный PR-аналитик. Пиши кратко, конкретно, без воды и без выдуманных фактов.",
            },
            {"role": "user", "content": prompt},
        ],
        "options": {"temperature": 0.2, "num_predict": 420},
    }
    try:
        raw, _ = post_json(
            settings["base_url"] + "/api/chat",
            payload,
            config.get("user_agent", "MentionMonitor"),
            timeout=settings["timeout"],
        )
        parsed = json.loads(raw)
        text = (parsed.get("message") or {}).get("content", "").strip()
        return {
            "enabled": True,
            "ok": bool(text),
            "text": text,
            "message": "Ответ получен" if text else "Ollama ответила без текста",
            "model": settings["model"],
            "base_url": settings["base_url"],
        }
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "message": str(exc),
            "model": settings["model"],
            "base_url": settings["base_url"],
        }


def generate_ollama_chat(config: dict, analysis: dict, question: str) -> dict:
    settings = ollama_config(config)
    if not settings["enabled"]:
        return {"enabled": False, "ok": False, "text": "", "message": "Локальная ИИ выключена в настройках."}
    question = (question or "").strip()
    if not question:
        return {"enabled": True, "ok": False, "text": "", "message": "Введите вопрос для ИИ-аналитика."}

    payload = {
        "model": settings["model"],
        "stream": False,
        "messages": [
            {
                "role": "system",
                "content": "Ты сильный PR-аналитик. Отвечай только по контексту системы, признавай нехватку данных, не выдумывай факты.",
            },
            {"role": "user", "content": build_chat_prompt(analysis, question)},
        ],
        "options": {"temperature": 0.15, "num_predict": 520},
    }
    try:
        raw, _ = post_json(
            settings["base_url"] + "/api/chat",
            payload,
            config.get("user_agent", "MentionMonitor"),
            timeout=settings["timeout"],
        )
        parsed = json.loads(raw)
        text = (parsed.get("message") or {}).get("content", "").strip()
        return {
            "enabled": True,
            "ok": bool(text),
            "text": text,
            "message": "Ответ получен" if text else "Ollama ответила без текста",
            "model": settings["model"],
            "base_url": settings["base_url"],
        }
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "message": str(exc),
            "model": settings["model"],
            "base_url": settings["base_url"],
        }
