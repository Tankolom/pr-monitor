"""
YandexGPT (Yandex Cloud Foundation Models) integration for PR Monitor.
Mirrors claude_api.py / ollama.py interface so webapp.py can use any provider transparently.
"""
from __future__ import annotations

import json

from .config import secret_value
from .fetch import post_json
from .ollama import build_analysis_prompt, build_chat_prompt

COMPLETION_URL = "https://llm.api.cloud.yandex.net/foundationModels/v1/completion"
USER_AGENT = "PR-Monitor/1.0"

DEFAULT_MODEL = "yandexgpt/latest"
AVAILABLE_MODELS = [
    "yandexgpt/latest",
    "yandexgpt-lite/latest",
    "yandexgpt-32k/latest",
]


def yandex_gpt_config(config: dict) -> dict:
    ai = config.get("ai", {})
    return {
        "enabled": bool(ai.get("yandex_gpt_enabled", False)),
        "model": ai.get("yandex_gpt_model") or DEFAULT_MODEL,
        "max_tokens": int(ai.get("yandex_gpt_max_tokens", 2000) or 2000),
        "timeout": int(ai.get("yandex_gpt_timeout", 60) or 60),
    }


def _model_uri(config: dict, model: str) -> str:
    folder_id = secret_value(config, "YANDEX_FOLDER_ID")
    return f"gpt://{folder_id}/{model}"


def _request(config: dict, settings: dict, system_prompt: str, user_prompt: str) -> dict:
    api_key = secret_value(config, "YANDEX_GPT_API_KEY")
    folder_id = secret_value(config, "YANDEX_FOLDER_ID")
    if not api_key:
        raise RuntimeError("API-ключ YANDEX_GPT_API_KEY не задан в настройках.")
    if not folder_id:
        raise RuntimeError("YANDEX_FOLDER_ID не задан в настройках.")

    payload = {
        "modelUri": _model_uri(config, settings["model"]),
        "completionOptions": {
            "stream": False,
            "temperature": 0.3,
            "maxTokens": str(settings["max_tokens"]),
        },
        "messages": [
            {"role": "system", "text": system_prompt},
            {"role": "user", "text": user_prompt},
        ],
    }
    raw, _ = post_json(
        COMPLETION_URL,
        payload,
        USER_AGENT,
        headers={
            "Authorization": f"Api-Key {api_key}",
            "x-folder-id": folder_id,
        },
        timeout=settings["timeout"],
    )
    return json.loads(raw)


def _extract_text_and_usage(data: dict) -> tuple[str, dict]:
    result = data.get("result", {})
    alternatives = result.get("alternatives", [])
    text = ""
    if alternatives:
        text = (alternatives[0].get("message", {}).get("text") or "").strip()
    usage_raw = result.get("usage", {})
    usage = {
        "input": int(usage_raw.get("inputTextTokens", 0) or 0),
        "output": int(usage_raw.get("completionTokens", 0) or 0),
    }
    return text, usage


def complete_yandex_gpt(config: dict, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> dict:
    """Low-level single-turn completion for internal tasks (audit, health checks)."""
    settings = yandex_gpt_config(config)
    if max_tokens:
        settings = {**settings, "max_tokens": max_tokens}
    try:
        data = _request(config, settings, system_prompt, user_prompt)
        text, usage = _extract_text_and_usage(data)
        return {"ok": bool(text), "text": text, "provider": "yandex_gpt", "model": settings["model"], "usage": usage, "message": "Ответ получен" if text else "Пустой ответ"}
    except Exception as exc:
        return {"ok": False, "text": "", "provider": "yandex_gpt", "model": settings["model"], "message": str(exc)}


def yandex_gpt_status(config: dict) -> dict:
    settings = yandex_gpt_config(config)
    api_key = secret_value(config, "YANDEX_GPT_API_KEY")
    folder_id = secret_value(config, "YANDEX_FOLDER_ID")
    if not api_key or not folder_id:
        return {
            "ok": False,
            "enabled": settings["enabled"],
            "model": settings["model"],
            "has_key": bool(api_key),
            "message": "API-ключ YANDEX_GPT_API_KEY или YANDEX_FOLDER_ID не задан в настройках.",
        }
    try:
        data = _request(config, settings, "Ты тестовый пинг.", "ping")
        text, usage = _extract_text_and_usage(data)
        return {
            "ok": True,
            "enabled": settings["enabled"],
            "model": settings["model"],
            "has_key": True,
            "message": f"YandexGPT отвечает · модель {settings['model']} · {usage['input']}+{usage['output']} tokens",
        }
    except Exception as exc:
        return {
            "ok": False,
            "enabled": settings["enabled"],
            "model": settings["model"],
            "has_key": bool(api_key),
            "message": str(exc),
        }


def generate_yandex_gpt_analysis(config: dict, analysis: dict) -> dict:
    settings = yandex_gpt_config(config)
    if not settings["enabled"]:
        return {
            "enabled": False,
            "ok": False,
            "text": "",
            "provider": "yandex_gpt",
            "message": "YandexGPT выключен в настройках.",
        }
    prompt = build_analysis_prompt(analysis)
    try:
        data = _request(
            config,
            settings,
            "Ты опытный PR-аналитик. "
            "Пиши кратко, конкретно, без воды и без выдуманных фактов. "
            "Используй только данные, которые переданы тебе в запросе.",
            prompt,
        )
        text, usage = _extract_text_and_usage(data)
        return {
            "enabled": True,
            "ok": bool(text),
            "text": text,
            "provider": "yandex_gpt",
            "model": settings["model"],
            "usage": usage,
            "message": "Ответ получен" if text else "YandexGPT вернул пустой ответ",
        }
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "provider": "yandex_gpt",
            "model": settings["model"],
            "message": str(exc),
        }


def generate_yandex_gpt_chat(config: dict, analysis: dict, question: str) -> dict:
    settings = yandex_gpt_config(config)
    if not settings["enabled"]:
        return {
            "enabled": False,
            "ok": False,
            "text": "",
            "provider": "yandex_gpt",
            "message": "YandexGPT выключен в настройках.",
        }
    question = (question or "").strip()
    if not question:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "provider": "yandex_gpt",
            "message": "Введите вопрос для ИИ-аналитика.",
        }
    prompt = build_chat_prompt(analysis, question)
    try:
        data = _request(
            config,
            settings,
            "Ты сильный PR-аналитик внутри SaaS-платформы мониторинга СМИ. "
            "Отвечай только по данным из контекста. "
            "Признавай нехватку данных, не выдумывай факты.",
            prompt,
        )
        text, usage = _extract_text_and_usage(data)
        return {
            "enabled": True,
            "ok": bool(text),
            "text": text,
            "provider": "yandex_gpt",
            "model": settings["model"],
            "usage": usage,
            "message": "Ответ получен" if text else "YandexGPT вернул пустой ответ",
        }
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "provider": "yandex_gpt",
            "model": settings["model"],
            "message": str(exc),
        }
