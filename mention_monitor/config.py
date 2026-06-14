import json
from pathlib import Path

SECRET_ALIASES = {
    "YANDEX_SEARCH_API_KEY": ("YANDEX_API_KEY",),
    "GOOGLE_SEARCH_API_KEY": ("GOOGLE_API_KEY",),
    "GOOGLE_SEARCH_CX": ("GOOGLE_CSE_ID",),
}


def load_config(path: str = "config.json") -> dict:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")
    with config_path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def save_config(config: dict, path: str = "config.json") -> None:
    config_path = Path(path)
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")


def load_secrets(config: dict) -> dict:
    path = Path(config.get("secrets_file", "data/secrets.json"))
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_secrets(config: dict, secrets: dict) -> None:
    path = Path(config.get("secrets_file", "data/secrets.json"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(secrets, ensure_ascii=False, indent=2), encoding="utf-8")
    try:
        path.chmod(0o600)
    except OSError:
        pass


def secret_value(config: dict, env_name: str) -> str:
    import os

    secrets = load_secrets(config)
    direct = os.getenv(env_name) or secrets.get(env_name, "")
    if direct:
        return direct
    for alias in SECRET_ALIASES.get(env_name, ()):
        fallback = os.getenv(alias) or secrets.get(alias, "")
        if fallback:
            return fallback
    return ""
