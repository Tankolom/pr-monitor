from __future__ import annotations

import smtplib
import ssl
from email.message import EmailMessage
from urllib.parse import urlencode

from .config import secret_value


def smtp_settings(config: dict) -> dict:
    mode = (secret_value(config, "SMTP_SECURITY") or "starttls").strip().lower()
    if mode not in {"plain", "starttls", "ssl"}:
        mode = "starttls"
    try:
        port = int(secret_value(config, "SMTP_PORT") or ("465" if mode == "ssl" else "587"))
    except ValueError:
        port = 465 if mode == "ssl" else 587
    return {
        "host": (secret_value(config, "SMTP_HOST") or "").strip(),
        "port": port,
        "username": (secret_value(config, "SMTP_USERNAME") or "").strip(),
        "password": secret_value(config, "SMTP_PASSWORD"),
        "from_email": (secret_value(config, "SMTP_FROM_EMAIL") or "").strip(),
        "from_name": (secret_value(config, "SMTP_FROM_NAME") or "PR Monitor").strip() or "PR Monitor",
        "security": mode,
        "public_base_url": (secret_value(config, "PUBLIC_BASE_URL") or "").rstrip("/"),
    }


def smtp_status(config: dict) -> dict:
    settings = smtp_settings(config)
    missing = [
        name for name, value in {
            "SMTP_HOST": settings["host"],
            "SMTP_FROM_EMAIL": settings["from_email"],
            "PUBLIC_BASE_URL": settings["public_base_url"],
        }.items()
        if not value
    ]
    ready = not missing
    if settings["username"] and not settings["password"]:
        ready = False
        missing.append("SMTP_PASSWORD")
    return {
        "ready": ready,
        "message": "Письма готовы к отправке." if ready else f"Не хватает настроек: {', '.join(missing)}",
        "settings": settings,
    }


def build_public_url(config: dict, path: str, **params) -> str:
    base = smtp_settings(config)["public_base_url"]
    if not base:
        return path
    query = urlencode({k: v for k, v in params.items() if v is not None})
    return f"{base}{path}" + (f"?{query}" if query else "")


def _send_message(config: dict, subject: str, to_email: str, text_body: str, html_body: str | None = None) -> tuple[bool, str]:
    status = smtp_status(config)
    settings = status["settings"]
    if not status["ready"]:
        return False, status["message"]

    msg = EmailMessage()
    msg["Subject"] = subject
    from_header = settings["from_email"]
    if settings["from_name"]:
        from_header = f'{settings["from_name"]} <{settings["from_email"]}>'
    msg["From"] = from_header
    msg["To"] = to_email
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")

    try:
        if settings["security"] == "ssl":
            server = smtplib.SMTP_SSL(settings["host"], settings["port"], context=ssl.create_default_context(), timeout=20)
        else:
            server = smtplib.SMTP(settings["host"], settings["port"], timeout=20)
        with server:
            server.ehlo()
            if settings["security"] == "starttls":
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            if settings["username"]:
                server.login(settings["username"], settings["password"])
            server.send_message(msg)
        return True, "Письмо отправлено"
    except Exception as exc:
        return False, str(exc)


def send_verification_email(config: dict, to_email: str, full_name: str, password: str, verify_url: str) -> tuple[bool, str]:
    intro_name = full_name or to_email
    text_body = (
        f"Здравствуйте, {intro_name}!\n\n"
        "Для вас создан кабинет в PR Monitor.\n\n"
        f"Логин: {to_email}\n"
        f"Временный пароль: {password}\n\n"
        "Чтобы активировать кабинет, подтвердите почту по ссылке:\n"
        f"{verify_url}\n\n"
        "После входа рекомендуем сразу сменить пароль."
    )
    html_body = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1d1d1f;line-height:1.6">
      <h2 style="margin:0 0 12px">Добро пожаловать в PR Monitor</h2>
      <p>Здравствуйте, <b>{intro_name}</b>!</p>
      <p>Для вас создан кабинет в сервисе мониторинга публикаций.</p>
      <p><b>Логин:</b> {to_email}<br><b>Временный пароль:</b> {password}</p>
      <p><a href="{verify_url}" style="display:inline-block;background:#28457A;color:#fff;text-decoration:none;padding:12px 18px;border-radius:12px">Подтвердить почту</a></p>
      <p style="color:#6e6e73">После входа рекомендуем сразу сменить пароль.</p>
    </div>
    """
    return _send_message(config, "Подтвердите почту в PR Monitor", to_email, text_body, html_body)


def send_password_reset_email(config: dict, to_email: str, full_name: str, reset_url: str) -> tuple[bool, str]:
    intro_name = full_name or to_email
    text_body = (
        f"Здравствуйте, {intro_name}!\n\n"
        "Вы запросили восстановление пароля в PR Monitor.\n\n"
        "Перейдите по ссылке, чтобы задать новый пароль:\n"
        f"{reset_url}\n\n"
        "Если это были не вы, просто проигнорируйте это письмо."
    )
    html_body = f"""
    <div style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;color:#1d1d1f;line-height:1.6">
      <h2 style="margin:0 0 12px">Восстановление пароля</h2>
      <p>Здравствуйте, <b>{intro_name}</b>!</p>
      <p>Нажмите на кнопку ниже, чтобы задать новый пароль.</p>
      <p><a href="{reset_url}" style="display:inline-block;background:#28457A;color:#fff;text-decoration:none;padding:12px 18px;border-radius:12px">Сменить пароль</a></p>
      <p style="color:#6e6e73">Если это были не вы, просто проигнорируйте это письмо.</p>
    </div>
    """
    return _send_message(config, "Сброс пароля в PR Monitor", to_email, text_body, html_body)
