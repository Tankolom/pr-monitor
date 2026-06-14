from __future__ import annotations

import base64
import hashlib
import json
import os
import secrets as stdlib_secrets
import time
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import load_secrets, save_secrets


VK_ID_DOMAIN = "id.vk.ru"
VK_ID_SDK_VERSION = "2.6.1"
VK_API_VERSION = "5.199"


def callback_url() -> str:
    return os.getenv(
        "VK_REDIRECT_URI",
        "https://109-235-117-6.sslip.io/vk-oauth-callback",
    )


def _post_form(url: str, body: dict[str, str], timeout: int = 20) -> dict:
    request = Request(
        url,
        data=urlencode(body).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def begin_vk_id_connection(config: dict) -> str:
    stored = load_secrets(config)
    app_id = str(stored.get("VK_APP_ID") or os.getenv("VK_APP_ID") or "").strip()
    if not app_id:
        raise ValueError("Сначала сохраните VK_APP_ID.")

    state = stdlib_secrets.token_urlsafe(32)
    verifier = stdlib_secrets.token_urlsafe(64)
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode("ascii")).digest()
    ).rstrip(b"=").decode("ascii")

    stored["VK_ID_PENDING_STATE"] = state
    stored["VK_ID_CODE_VERIFIER"] = verifier
    stored["VK_ID_PENDING_AT"] = int(time.time())
    save_secrets(config, stored)

    params = {
        "response_type": "code",
        "client_id": app_id,
        "app_id": app_id,
        "redirect_uri": callback_url(),
        "code_challenge": challenge,
        "code_challenge_method": "s256",
        "state": state,
        "v": VK_ID_SDK_VERSION,
        "sdk_type": "vkid",
    }
    return f"https://{VK_ID_DOMAIN}/authorize?{urlencode(params)}"


def _validate_vk_search(access_token: str) -> tuple[bool, str]:
    url = "https://api.vk.com/method/newsfeed.search?" + urlencode(
        {
            "q": "Россия",
            "count": 1,
            "access_token": access_token,
            "v": VK_API_VERSION,
        }
    )
    try:
        with urlopen(url, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return False, f"VK API недоступен: {exc}"
    if "response" in payload:
        return True, "Поиск публичных публикаций доступен."
    error = payload.get("error", {})
    return False, error.get("error_msg") or str(error or payload)


def finish_vk_id_connection(
    config: dict,
    *,
    code: str,
    device_id: str,
    state: str,
) -> tuple[bool, str]:
    stored = load_secrets(config)
    expected_state = str(stored.get("VK_ID_PENDING_STATE") or "")
    verifier = str(stored.get("VK_ID_CODE_VERIFIER") or "")
    pending_at = int(stored.get("VK_ID_PENDING_AT") or 0)
    app_id = str(stored.get("VK_APP_ID") or os.getenv("VK_APP_ID") or "").strip()

    if not expected_state or not verifier or state != expected_state:
        return False, "Проверка безопасности VK ID не пройдена. Запустите подключение заново."
    if time.time() - pending_at > 15 * 60:
        return False, "Подключение устарело. Нажмите кнопку ещё раз."

    query = urlencode(
        {
            "grant_type": "authorization_code",
            "redirect_uri": callback_url(),
            "client_id": app_id,
            "code_verifier": verifier,
            "state": state,
            "device_id": device_id,
        }
    )
    try:
        result = _post_form(
            f"https://{VK_ID_DOMAIN}/oauth2/auth?{query}",
            {"code": code},
        )
    except Exception as exc:
        return False, f"VK ID не выдал токен: {exc}"

    access_token = str(result.get("access_token") or "")
    refresh_token = str(result.get("refresh_token") or "")
    if not access_token or not refresh_token:
        return False, result.get("error_description") or str(result)

    search_ok, search_message = _validate_vk_search(access_token)
    if not search_ok:
        # Do not replace the current token until the candidate proves that it
        # can call the exact API method used by the collector.
        stored["VK_ID_LAST_ERROR"] = search_message
        stored.pop("VK_ID_PENDING_STATE", None)
        stored.pop("VK_ID_CODE_VERIFIER", None)
        stored.pop("VK_ID_PENDING_AT", None)
        save_secrets(config, stored)
        return False, (
            "Авторизация VK ID выполнена, но этот токен не допущен к "
            f"newsfeed.search: {search_message}"
        )

    stored["VK_ACCESS_TOKEN"] = access_token
    stored["VK_REFRESH_TOKEN"] = refresh_token
    stored["VK_DEVICE_ID"] = device_id
    stored["VK_TOKEN_EXPIRES_AT"] = int(time.time()) + int(result.get("expires_in") or 3600)
    stored["VK_TOKEN_MODE"] = "vk_id_refresh"
    stored.pop("VK_ID_LAST_ERROR", None)
    stored.pop("VK_ID_PENDING_STATE", None)
    stored.pop("VK_ID_CODE_VERIFIER", None)
    stored.pop("VK_ID_PENDING_AT", None)
    save_secrets(config, stored)
    return True, "VK подключён. Токен будет обновляться автоматически."


def refresh_vk_access_token(config: dict, force: bool = False) -> tuple[str, str]:
    stored = load_secrets(config)
    current = str(stored.get("VK_ACCESS_TOKEN") or os.getenv("VK_ACCESS_TOKEN") or "")
    refresh_token = str(stored.get("VK_REFRESH_TOKEN") or "")
    device_id = str(stored.get("VK_DEVICE_ID") or "")
    expires_at = int(stored.get("VK_TOKEN_EXPIRES_AT") or 0)
    app_id = str(stored.get("VK_APP_ID") or os.getenv("VK_APP_ID") or "").strip()

    if not refresh_token or not device_id or not app_id:
        return current, "manual"
    if not force and current and expires_at > int(time.time()) + 300:
        return current, "vk_id_refresh"

    state = stdlib_secrets.token_urlsafe(24)
    query = urlencode(
        {
            "grant_type": "refresh_token",
            "redirect_uri": callback_url(),
            "client_id": app_id,
            "device_id": device_id,
            "state": state,
        }
    )
    try:
        result = _post_form(
            f"https://{VK_ID_DOMAIN}/oauth2/auth?{query}",
            {"refresh_token": refresh_token},
        )
    except Exception:
        return current, "refresh_failed"

    new_access = str(result.get("access_token") or "")
    if not new_access or result.get("state") != state:
        return current, "refresh_failed"
    search_ok, _ = _validate_vk_search(new_access)
    if not search_ok:
        return current, "refresh_failed"

    stored["VK_ACCESS_TOKEN"] = new_access
    stored["VK_REFRESH_TOKEN"] = str(result.get("refresh_token") or refresh_token)
    stored["VK_TOKEN_EXPIRES_AT"] = int(time.time()) + int(result.get("expires_in") or 3600)
    stored["VK_TOKEN_MODE"] = "vk_id_refresh"
    save_secrets(config, stored)
    return new_access, "vk_id_refresh"
