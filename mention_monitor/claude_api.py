"""
Claude API (Anthropic) integration for PR Monitor.
Mirrors ollama.py interface so webapp.py can use either provider transparently.
"""
from __future__ import annotations

from .config import secret_value
from .ollama import build_analysis_prompt, build_chat_prompt

DEFAULT_MODEL = "claude-sonnet-4-6"
AVAILABLE_MODELS = [
    "claude-opus-4-6",
    "claude-sonnet-4-6",
    "claude-haiku-4-5-20251001",
]


def claude_config(config: dict) -> dict:
    ai = config.get("ai", {})
    return {
        "enabled": bool(ai.get("claude_enabled", False)),
        "model": ai.get("claude_model") or DEFAULT_MODEL,
        "max_tokens": int(ai.get("claude_max_tokens", 1024) or 1024),
        "timeout": int(ai.get("claude_timeout", 60) or 60),
    }


def _get_client(config: dict):
    """Returns an Anthropic client or raises RuntimeError if key is missing."""
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError("Пакет anthropic не установлен. Выполните: pip install anthropic") from exc

    api_key = secret_value(config, "ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("API-ключ ANTHROPIC_API_KEY не задан в настройках.")
    return anthropic.Anthropic(api_key=api_key)


def complete_claude(config: dict, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> dict:
    """Low-level single-turn completion for internal tasks (audit, health checks)."""
    settings = claude_config(config)
    tokens = max_tokens or settings["max_tokens"]
    try:
        client = _get_client(config)
        msg = client.messages.create(
            model=settings["model"],
            max_tokens=tokens,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        text = msg.content[0].text.strip() if msg.content else ""
        return {"ok": bool(text), "text": text, "provider": "claude", "model": settings["model"], "usage": {"input": msg.usage.input_tokens, "output": msg.usage.output_tokens}, "message": "Ответ получен" if text else "Пустой ответ"}
    except Exception as exc:
        return {"ok": False, "text": "", "provider": "claude", "model": settings["model"], "message": str(exc)}


def claude_status(config: dict) -> dict:
    settings = claude_config(config)
    api_key = secret_value(config, "ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "ok": False,
            "enabled": settings["enabled"],
            "model": settings["model"],
            "has_key": False,
            "message": "API-ключ ANTHROPIC_API_KEY не задан в настройках.",
        }
    try:
        client = _get_client(config)
        # Minimal ping — avoid wasting tokens
        msg = client.messages.create(
            model=settings["model"],
            max_tokens=5,
            messages=[{"role": "user", "content": "ping"}],
        )
        return {
            "ok": True,
            "enabled": settings["enabled"],
            "model": settings["model"],
            "has_key": True,
            "message": f"Claude API отвечает · модель {settings['model']} · {msg.usage.input_tokens}+{msg.usage.output_tokens} tokens",
        }
    except Exception as exc:
        return {
            "ok": False,
            "enabled": settings["enabled"],
            "model": settings["model"],
            "has_key": bool(api_key),
            "message": str(exc),
        }


def generate_claude_analysis(config: dict, analysis: dict) -> dict:
    settings = claude_config(config)
    if not settings["enabled"]:
        return {
            "enabled": False,
            "ok": False,
            "text": "",
            "provider": "claude",
            "message": "Claude API выключен в настройках.",
        }
    prompt = build_analysis_prompt(analysis)
    try:
        client = _get_client(config)
        msg = client.messages.create(
            model=settings["model"],
            max_tokens=settings["max_tokens"],
            system=(
                "Ты опытный PR-аналитик. "
                "Пиши кратко, конкретно, без воды и без выдуманных фактов. "
                "Используй только данные, которые переданы тебе в запросе."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip() if msg.content else ""
        return {
            "enabled": True,
            "ok": bool(text),
            "text": text,
            "provider": "claude",
            "model": settings["model"],
            "usage": {
                "input": msg.usage.input_tokens,
                "output": msg.usage.output_tokens,
            },
            "message": "Ответ получен" if text else "Claude вернул пустой ответ",
        }
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "provider": "claude",
            "model": settings["model"],
            "message": str(exc),
        }


def generate_claude_chat(config: dict, analysis: dict, question: str) -> dict:
    settings = claude_config(config)
    if not settings["enabled"]:
        return {
            "enabled": False,
            "ok": False,
            "text": "",
            "provider": "claude",
            "message": "Claude API выключен в настройках.",
        }
    question = (question or "").strip()
    if not question:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "provider": "claude",
            "message": "Введите вопрос для ИИ-аналитика.",
        }
    prompt = build_chat_prompt(analysis, question)
    try:
        client = _get_client(config)
        msg = client.messages.create(
            model=settings["model"],
            max_tokens=settings["max_tokens"],
            system=(
                "Ты сильный PR-аналитик внутри SaaS-платформы мониторинга СМИ. "
                "Отвечай только по данным из контекста. "
                "Признавай нехватку данных, не выдумывай факты."
            ),
            messages=[{"role": "user", "content": prompt}],
        )
        text = msg.content[0].text.strip() if msg.content else ""
        return {
            "enabled": True,
            "ok": bool(text),
            "text": text,
            "provider": "claude",
            "model": settings["model"],
            "usage": {
                "input": msg.usage.input_tokens,
                "output": msg.usage.output_tokens,
            },
            "message": "Ответ получен" if text else "Claude вернул пустой ответ",
        }
    except Exception as exc:
        return {
            "enabled": True,
            "ok": False,
            "text": "",
            "provider": "claude",
            "model": settings["model"],
            "message": str(exc),
        }
