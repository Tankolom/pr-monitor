"""
Telegram relay — запускается на VPS за пределами РФ.
Читает публичные каналы через MTProto (Telethon) и отправляет посты
на основной сервер через /api/tg-ingest.

Установка:
    pip install telethon httpx

Первый запуск (интерактивная авторизация):
    python tg_relay.py --auth

Обычный запуск:
    python tg_relay.py

Переменные окружения (или файл .env):
    TG_API_ID        — из my.telegram.org
    TG_API_HASH      — из my.telegram.org
    INGEST_URL       — https://your-server.ru/api/tg-ingest
    INGEST_TOKEN     — секретный токен (тот же что в data/secrets.json → TG_RELAY_TOKEN)
    INTERVAL_MINUTES — интервал сбора (по умолчанию 30)
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import timezone
from pathlib import Path

STATE_FILE = Path("tg_relay_state.json")
SESSION_FILE = "tg_session"


def _env(key: str, default: str | None = None) -> str:
    val = os.environ.get(key, default)
    if not val:
        print(f"[relay] Переменная окружения {key} не задана", file=sys.stderr)
        sys.exit(1)
    return val


def _load_state() -> dict:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


async def _collect(channels: list[str], api_id: int, api_hash: str, ingest_url: str, token: str) -> None:
    try:
        from telethon import TelegramClient
        from telethon.errors import ChannelPrivateError, UsernameNotOccupiedError
    except ImportError:
        print("[relay] Установите telethon: pip install telethon", file=sys.stderr)
        sys.exit(1)

    try:
        import httpx
    except ImportError:
        print("[relay] Установите httpx: pip install httpx", file=sys.stderr)
        sys.exit(1)

    state = _load_state()

    async with TelegramClient(SESSION_FILE, api_id, api_hash) as client:
        for channel in channels:
            min_id = state.get(channel, 0)
            posts: list[dict] = []

            try:
                async for msg in client.iter_messages(channel, min_id=min_id, limit=100):
                    text = msg.text or msg.message or ""
                    if not text.strip():
                        continue
                    posts.append({
                        "channel": channel,
                        "message_id": msg.id,
                        "text": text,
                        "date": msg.date.astimezone(timezone.utc).isoformat(),
                        "views": msg.views or 0,
                        "forwards": msg.forwards or 0,
                        "url": f"https://t.me/{channel}/{msg.id}",
                    })

            except (ChannelPrivateError, UsernameNotOccupiedError) as exc:
                print(f"[relay] {channel}: {exc}")
                continue
            except Exception as exc:
                print(f"[relay] {channel}: ошибка сбора — {exc}")
                continue

            if not posts:
                continue

            try:
                delivered_max_id = max((post["message_id"] for post in posts), default=min_id)
                resp = httpx.post(
                    ingest_url,
                    json={"posts": posts},
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=30,
                )
                resp.raise_for_status()
                result = resp.json()
                if not result.get("ok"):
                    raise RuntimeError(result.get("error") or "ingest rejected the batch")
                state[channel] = max(state.get(channel, 0), delivered_max_id)
                _save_state(state)
                inserted = result.get("inserted", 0)
                print(f"[relay] {channel}: {len(posts)} постов → {inserted} новых")
            except Exception as exc:
                print(f"[relay] {channel}: ошибка отправки — {exc}")

def _load_channels_from_config(config_path: str) -> list[str]:
    """Читает список Telegram-каналов из config.json основного приложения."""
    import re
    try:
        data = json.loads(Path(config_path).read_text())
    except Exception:
        return []
    channels = []
    for source in data.get("sources", []):
        url = source.get("url", "")
        m = re.search(r"/telegram/channel/([^/\"]+)", url)
        if m:
            channels.append(m.group(1))
    return channels


async def main(channels: list[str]) -> None:
    api_id = int(_env("TG_API_ID"))
    api_hash = _env("TG_API_HASH")
    ingest_url = _env("INGEST_URL")
    token = _env("INGEST_TOKEN")
    interval = int(os.environ.get("INTERVAL_MINUTES", "30")) * 60

    print(f"[relay] Каналов: {len(channels)}, интервал: {interval // 60} мин")
    print(f"[relay] Ingest URL: {ingest_url}")

    while True:
        print("[relay] Запуск сбора...")
        try:
            await _collect(channels, api_id, api_hash, ingest_url, token)
        except Exception as exc:
            print(f"[relay] Критическая ошибка: {exc}")
        print(f"[relay] Следующий сбор через {interval // 60} мин")
        await asyncio.sleep(interval)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--auth", action="store_true", help="Интерактивная авторизация Telegram")
    parser.add_argument("--config", default="config.json", help="Путь к config.json основного приложения")
    parser.add_argument("--channels", nargs="*", help="Список каналов (переопределяет config)")
    args = parser.parse_args()

    if args.channels:
        channels = args.channels
    else:
        channels = _load_channels_from_config(args.config)

    if not channels:
        print("[relay] Нет каналов для сбора. Укажите --channels или передайте --config с путём к config.json")
        sys.exit(1)

    if args.auth:
        # Первый запуск: авторизоваться интерактивно
        async def auth() -> None:
            from telethon import TelegramClient
            api_id = int(_env("TG_API_ID"))
            api_hash = _env("TG_API_HASH")
            async with TelegramClient(SESSION_FILE, api_id, api_hash) as client:
                me = await client.get_me()
                print(f"[relay] Авторизован как {me.username or me.first_name}")
        asyncio.run(auth())
    else:
        asyncio.run(main(channels))
