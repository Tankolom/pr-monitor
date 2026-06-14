"""
Single entry point that routes internal AI tasks (audit, source health, etc.)
to whichever provider is enabled, using the same priority as the agent page:
Claude → YandexGPT → Ollama.
"""
from __future__ import annotations

from .claude_api import claude_config, complete_claude
from .ollama import complete_ollama, ollama_config
from .yandex_gpt_api import complete_yandex_gpt, yandex_gpt_config


def active_provider(config: dict) -> str | None:
    if claude_config(config)["enabled"]:
        return "claude"
    if yandex_gpt_config(config)["enabled"]:
        return "yandex_gpt"
    if ollama_config(config)["enabled"]:
        return "ollama"
    return None


def provider_label(config: dict) -> str:
    provider = active_provider(config)
    if provider == "claude":
        return f"Claude · {claude_config(config)['model']}"
    if provider == "yandex_gpt":
        return f"YandexGPT · {yandex_gpt_config(config)['model']}"
    if provider == "ollama":
        return f"Ollama · {ollama_config(config)['model']}"
    return "ИИ не подключён"


def ai_complete(config: dict, system_prompt: str, user_prompt: str, max_tokens: int | None = None) -> dict:
    """Run a single-turn completion on the active provider. Returns
    {ok, text, provider, model?, usage?, message}."""
    provider = active_provider(config)
    if provider == "claude":
        return complete_claude(config, system_prompt, user_prompt, max_tokens)
    if provider == "yandex_gpt":
        return complete_yandex_gpt(config, system_prompt, user_prompt, max_tokens)
    if provider == "ollama":
        return complete_ollama(config, system_prompt, user_prompt, max_tokens)
    return {"ok": False, "text": "", "provider": None, "message": "Ни один ИИ-провайдер не включён в настройках."}
