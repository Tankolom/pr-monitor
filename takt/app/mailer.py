"""Письма покупателю (ссылки на скачивание, код пакета). Без SMTP-настроек письма пишутся в лог."""
from __future__ import annotations

import logging
import smtplib
import ssl
from email.message import EmailMessage

from . import config

log = logging.getLogger(__name__)


def send(to: str, subject: str, text: str) -> bool:
    s = config.settings
    if not (s.smtp_host and s.mail_from):
        log.info("MAIL (smtp not configured) to=%s subject=%s\n%s", to, subject, text)
        return False
    msg = EmailMessage()
    msg["From"] = s.mail_from
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(text)
    try:
        if s.smtp_port == 465:
            with smtplib.SMTP_SSL(s.smtp_host, s.smtp_port, context=ssl.create_default_context(), timeout=20) as c:
                if s.smtp_user:
                    c.login(s.smtp_user, s.smtp_password)
                c.send_message(msg)
        else:
            with smtplib.SMTP(s.smtp_host, s.smtp_port, timeout=20) as c:
                c.starttls(context=ssl.create_default_context())
                if s.smtp_user:
                    c.login(s.smtp_user, s.smtp_password)
                c.send_message(msg)
        return True
    except Exception:  # письмо — не критичный путь, покупатель уже видит ссылки на странице
        log.exception("mail send failed to=%s", to)
        return False
