"""HTTP-сервер на стандартной библиотеке: лендинг, анкета, предпросмотр, оплата, скачивание."""
from __future__ import annotations

import logging
import re
import secrets
import threading
import time
from collections import defaultdict, deque
from http import cookies
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlparse

from . import pages
from .config import Settings, load_settings
from .db import Store
from .documents import SAMPLE_DATA, build_documents
from .payments import PaymentError, create_payment, process_webhook, refresh_order, reusable_confirmation
from .render import build_zip, to_html
from .validation import validate

LOG = logging.getLogger("vupaket")
MAX_BODY = 20_000
TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
UTM_KEYS = ("utm_source", "utm_medium", "utm_campaign")


class RateLimiter:
    """Скользящее окно в памяти: достаточно для одного процесса за Caddy."""

    def __init__(self):
        self.hits: dict[tuple[str, str], deque] = defaultdict(deque)
        self.lock = threading.Lock()

    def allow(self, key: str, bucket: str, limit: int, window: int) -> bool:
        now = time.monotonic()
        with self.lock:
            q = self.hits[(bucket, key)]
            while q and now - q[0] > window:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(now)
            return True


LIMITS = {"order": (15, 3600), "pay": (20, 3600), "download": (60, 3600), "webhook": (300, 60)}


def make_handler(settings: Settings, store: Store, limiter: RateLimiter, fetch=None, create=None):
    from .payments import fetch_payment as _fetch
    fetch = fetch or _fetch
    create = create or create_payment

    class Handler(BaseHTTPRequestHandler):
        server_version = "vu-paket"
        sys_version = ""

        # --- утилиты ------------------------------------------------------
        def log_message(self, fmt, *args):  # без токенов заказов в логах
            path = re.sub(r"/order/[^/?]+", "/order/<token>", self.path)
            LOG.info("%s %s %s", self.command, path, args[1] if len(args) > 1 else "")

        def client_ip(self) -> str:
            if settings.trust_proxy:
                fwd = self.headers.get("X-Forwarded-For", "")
                if fwd:
                    return fwd.split(",")[0].strip()
            return self.client_address[0]

        def send(self, status: int, body: str | bytes, ctype: str = "text/html; charset=utf-8", headers: dict | None = None):
            data = body.encode() if isinstance(body, str) else body
            self.send_response(status)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")  # токен заказа в URL не должен утечь
            self.send_header("X-Frame-Options", "DENY")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline' https://mc.yandex.ru; "
                "img-src 'self' data: https://mc.yandex.ru; connect-src 'self' https://mc.yandex.ru; frame-ancestors 'none'; "
                "form-action 'self' https://yoomoney.ru https://*.yoomoney.ru",
            )
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(data)

        def redirect(self, location: str, headers: dict | None = None):
            self.send(303, "", headers={"Location": location, **(headers or {})})

        def page_error(self, status: int, title: str, text: str):
            self.send(status, pages.message_page(settings, title, text))

        def utm(self) -> dict:
            jar = cookies.SimpleCookie(self.headers.get("Cookie", ""))
            raw = jar["vu_utm"].value if "vu_utm" in jar else ""
            parsed = parse_qs(unquote(raw))
            return {k: parsed[k][0][:80] for k in UTM_KEYS if k in parsed}

        def read_form(self) -> dict[str, str] | None:
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                return None
            if length > MAX_BODY:
                return None
            raw = self.rfile.read(length).decode("utf-8", "replace")
            return {k: v[0] for k, v in parse_qs(raw, keep_blank_values=True).items()}

        def order_or_404(self, token: str) -> dict | None:
            if not TOKEN_RE.match(token):
                self.page_error(404, "Заказ не найден", "Проверьте ссылку.")
                return None
            order = store.get_order(token)
            if not order:
                self.page_error(404, "Заказ не найден", "Проверьте ссылку. Неоплаченные заказы удаляются через 30 дней.")
                return None
            return order

        # --- маршруты -----------------------------------------------------
        def do_HEAD(self):
            self.do_GET()

        def do_GET(self):
            url = urlparse(self.path)
            path = url.path.rstrip("/") or "/"
            query = parse_qs(url.query)
            try:
                if path == "/":
                    headers = {}
                    utm = {k: query[k][0][:80] for k in UTM_KEYS if k in query}
                    if utm:
                        value = quote("&".join(f"{k}={quote(v)}" for k, v in utm.items()), safe="")
                        headers["Set-Cookie"] = f"vu_utm={value}; Max-Age=2592000; Path=/; SameSite=Lax; HttpOnly"
                    store.log_event("view_landing", utm=utm or self.utm())
                    return self.send(200, pages.landing(settings), headers=headers)
                if path == "/form":
                    store.log_event("view_form", utm=self.utm())
                    return self.send(200, pages.form_page(settings, {}, {}))
                if path == "/sample":
                    store.log_event("view_sample", utm=self.utm())
                    docs = build_documents(SAMPLE_DATA)
                    # Полностью показываем приказ и памятку, план — первые строки.
                    html_docs = "".join(to_html(d) for d in docs[:1]) + "".join(
                        f'<div class="fade">{to_html(d)}</div>' for d in docs[1:3])
                    return self.send(200, pages.sample_page(settings, html_docs))
                if path == "/offer":
                    return self.send(200, pages.offer_page(settings))
                if path == "/privacy":
                    return self.send(200, pages.privacy_page(settings))
                if path == "/healthz":
                    state = "payments=ready" if settings.payments_ready else ("payments=demo" if settings.demo_payments else "payments=off")
                    return self.send(200, f"ok {state} seller={'ok' if settings.seller_ready else 'missing'}", "text/plain; charset=utf-8")
                if path == "/admin":
                    key = (query.get("key") or [""])[0]
                    if not settings.admin_key or not secrets.compare_digest(key, settings.admin_key):
                        return self.page_error(404, "Страница не найдена", "")
                    days = 30
                    return self.send(200, pages.admin_page(settings, store.funnel(days), store.recent_orders(), store.revenue(days), days))
                m = re.fullmatch(r"/order/([^/]+)(/edit|/download)?", path)
                if m:
                    return self.get_order(m.group(1), m.group(2) or "", query)
                return self.page_error(404, "Страница не найдена", "Такой страницы нет.")
            except Exception:  # pragma: no cover - последняя линия обороны
                LOG.exception("GET failed")
                return self.page_error(500, "Ошибка", "Что-то пошло не так. Попробуйте ещё раз через минуту.")

        def get_order(self, token: str, action: str, query: dict):
            order = self.order_or_404(token)
            if not order:
                return
            if action == "/edit":
                if order["status"] == "paid":
                    return self.redirect(f"/order/{token}")
                return self.send(200, pages.form_page(settings, {**order["data"], "consent": "yes"}, {},
                                                      action=f"/order/{token}/edit", edit=True))
            if action == "/download":
                if order["status"] != "paid":
                    return self.redirect(f"/order/{token}")
                if not limiter.allow(self.client_ip(), "download", *LIMITS["download"]):
                    return self.page_error(429, "Слишком много запросов", "Подождите немного и попробуйте снова.")
                data = build_zip(order["data"], uid_seed=str(order["id"]))
                store.count_download(token)
                store.log_event("download", token, order)
                fname = quote(f"Воинский_учёт_{order['data']['year']}.zip")
                return self.send(200, data, "application/zip",
                                 {"Content-Disposition": f"attachment; filename=\"vu-paket.zip\"; filename*=UTF-8''{fname}"})
            order = refresh_order(settings, store, order, fetch=fetch)
            if order["status"] == "paid":
                return self.send(200, pages.paid_page(settings, order))
            if order["status"] == "pending" and "retry" not in query:
                return self.send(200, pages.pending_page(settings, order))
            docs = build_documents(order["data"])
            preview = to_html(docs[0], limit_blocks=11)
            store.log_event("view_preview", token, order)
            return self.send(200, pages.preview_page(settings, order, preview, [d.title for d in docs],
                                                     pay_error=(query.get("err") or [""])[0][:200]))

        def do_POST(self):
            path = urlparse(self.path).path.rstrip("/")
            try:
                if path == "/yookassa/webhook":
                    return self.webhook()
                if path == "/order":
                    return self.post_order(None)
                m = re.fullmatch(r"/order/([^/]+)/(edit|pay)", path)
                if m and m.group(2) == "edit":
                    return self.post_order(m.group(1))
                if m and m.group(2) == "pay":
                    return self.post_pay(m.group(1))
                return self.page_error(404, "Страница не найдена", "")
            except Exception:  # pragma: no cover
                LOG.exception("POST failed")
                return self.page_error(500, "Ошибка", "Что-то пошло не так. Попробуйте ещё раз через минуту.")

        def post_order(self, token: str | None):
            if not limiter.allow(self.client_ip(), "order", *LIMITS["order"]):
                return self.page_error(429, "Слишком много запросов", "Подождите час или напишите нам.")
            form = self.read_form()
            if form is None:
                return self.page_error(413, "Слишком большой запрос", "Сократите текст в полях.")
            data, errors = validate(form)
            action = f"/order/{token}/edit" if token else "/order"
            if errors:
                store.log_event("form_invalid", utm=self.utm())
                return self.send(422, pages.form_page(settings, {**form}, errors, action=action, edit=bool(token)))
            if token:
                order = self.order_or_404(token)
                if not order:
                    return
                if not store.update_order_data(token, data):
                    return self.redirect(f"/order/{token}")
                store.log_event("order_updated", token, order)
                return self.redirect(f"/order/{token}?retry=1")
            token = secrets.token_urlsafe(18)
            utm = self.utm()
            demo = (not settings.payments_ready) and settings.demo_payments
            store.create_order(token, data, settings.price_rub, utm, demo)
            store.log_event("order_created", token, utm)
            return self.redirect(f"/order/{token}")

        def post_pay(self, token: str):
            order = self.order_or_404(token)
            if not order:
                return
            if order["status"] == "paid":
                return self.redirect(f"/order/{token}")
            if not limiter.allow(self.client_ip(), "pay", *LIMITS["pay"]):
                return self.page_error(429, "Слишком много запросов", "Подождите немного и попробуйте снова.")
            store.log_event("pay_click", token, order)
            if not settings.payments_ready:
                if settings.demo_payments and order["demo"]:
                    store.mark_paid(token, "demo", f"demo-{order['id']}", float(order["price_rub"]))
                    store.log_event("payment_succeeded", token, order)
                    return self.redirect(f"/order/{token}")
                store.log_event("payment_error", token, order)
                return self.redirect(f"/order/{token}?retry=1&err=" + quote("Оплата временно недоступна. Напишите нам — пришлём счёт."))
            reuse = reusable_confirmation(settings, order, fetch=fetch)
            if reuse:
                return self.redirect(reuse)
            try:
                payment_id, url = create(settings, order, f"{settings.public_url}/order/{token}")
            except PaymentError as exc:
                store.log_event("payment_error", token, order)
                return self.redirect(f"/order/{token}?retry=1&err=" + quote(f"{exc}. Попробуйте ещё раз через минуту."))
            store.set_payment_pending(token, payment_id)
            store.log_event("payment_created", token, order)
            return self.redirect(url)

        def webhook(self):
            if not limiter.allow(self.client_ip(), "webhook", *LIMITS["webhook"]):
                return self.send(429, "slow down", "text/plain")
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                length = 0
            if length <= 0 or length > MAX_BODY or not settings.payments_ready:
                return self.send(400, "bad request", "text/plain")
            body = self.rfile.read(length)
            try:
                result = process_webhook(settings, store, body, fetch=fetch)
            except PaymentError:
                # 5xx — ЮKassa повторит уведомление позже.
                return self.send(503, "retry", "text/plain")
            LOG.info("webhook: %s", result)
            return self.send(200, "ok", "text/plain")

    return Handler


def _purge_loop(store: Store, days: int):
    while True:
        try:
            n = store.purge_unpaid(days)
            if n:
                LOG.info("purged %s unpaid orders", n)
        except Exception:  # pragma: no cover
            LOG.exception("purge failed")
        time.sleep(6 * 3600)


def serve() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    settings = load_settings()
    store = Store(settings.db_path)
    if not settings.payments_ready:
        LOG.warning("ЮKassa не настроена: %s", "демо-оплата включена" if settings.demo_payments else "оплата отключена")
    threading.Thread(target=_purge_loop, args=(store, settings.order_ttl_days), daemon=True).start()
    httpd = ThreadingHTTPServer((settings.host, settings.port), make_handler(settings, store, RateLimiter()))
    LOG.info("vu-paket on http://%s:%s", settings.host, settings.port)
    httpd.serve_forever()
