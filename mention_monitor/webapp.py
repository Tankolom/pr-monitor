from __future__ import annotations

from http import cookies
import hmac
import json
import os
import secrets
import string
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlencode, urlparse

from .agent import analyze_project
from .collector import collect_once
from .config import load_config, load_secrets, save_secrets, secret_value
from .db import (
    authenticate_user,
    connect,
    create_email_verification_token,
    create_password_reset_token,
    create_public_user,
    create_session,
    consume_email_verification_token,
    consume_password_reset_token,
    dashboard_stats,
    delete_session,
    get_user_by_email,
    get_user_by_id,
    get_session_user,
    has_valid_password_reset_token,
    latest_mentions,
    mark_user_email_verified,
    purge_expired_sessions,
    update_user_password,
)
from .helpers import VK_REDIRECT_URI, account_id_of, esc, first_param, normalize_project_filter, visible_projects
from .logging_utils import get_logger
from .mailer import build_public_url, send_password_reset_email, send_verification_email, smtp_status
from .pages import (
    handle_admin_post,
    handle_billing_post,
    handle_dashboard_project_post,
    handle_pay,
    handle_settings_post,
    handle_topics_post,
    project_autofill,
    render_admin,
    render_analytics,
    render_billing,
    render_payment_return,
    render_upgrade,
    render_agent_page,
    render_claude_test,
    render_yandex_gpt_test,
    render_auth_notice,
    render_dashboard,
    render_forgot_password,
    render_google_test,
    render_login,
    render_ollama_test,
    render_register,
    render_reset_password,
    render_serper_test,
    render_settings,
    render_topics,
    render_vk_test,
    render_yandex_test,
)
from .reporting import export_xlsx
from .styles import STYLE
from .vk_auth import begin_vk_id_connection, finish_vk_id_connection

COLLECT_LOCK = threading.Lock()
COLLECTION_STATE_LOCK = threading.Lock()
COLLECTION_STATE = {
    "status": "idle",
    "project": "",
    "started_at": None,
    "finished_at": None,
    "found": 0,
    "inserted": 0,
    "error": None,
}
TG_INGEST_RATE_LOCK = threading.Lock()
TG_INGEST_RATE_STATE: dict[str, list[float]] = {}
NEWS_SLICE_SOURCE_TYPES = [
    "google_news", "rss", "serper_google", "yandex_search",
    "gdelt_news", "newsdata", "web_pages",
]
LOGGER = get_logger("webapp")


def _generate_temp_password(length: int = 12) -> str:
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
    return "".join(secrets.choice(alphabet) for _ in range(max(length, 10)))


def _collection_state(**updates) -> dict:
    with COLLECTION_STATE_LOCK:
        if updates:
            COLLECTION_STATE.update(updates)
        return dict(COLLECTION_STATE)


def _run_collection(config_path: str, options: dict) -> None:
    try:
        result = collect_once(config_path, **options)
        _collection_state(
            status=result.get("status", "finished"),
            finished_at=datetime.now(timezone.utc).isoformat(),
            found=result.get("found", 0),
            inserted=result.get("inserted", 0),
            error=result.get("error"),
        )
    except Exception as exc:
        LOGGER.exception("Collection crashed for project %s", options.get("project"))
        _collection_state(
            status="failed",
            finished_at=datetime.now(timezone.utc).isoformat(),
            error=str(exc),
        )
    finally:
        COLLECT_LOCK.release()


def _is_superadmin(user: dict | None) -> bool:
    if not user:
        return False
    try:
        return bool(user["is_superadmin"])
    except (KeyError, IndexError, TypeError):
        return False


def _match_tg_project(projects: list[dict], text: str) -> dict | None:
    """Определяет проект мониторинга по ключевым словам запросов. Возвращает dict проекта
    (с name и account_id) или None, если проектов нет."""
    text_lower = text.lower()
    for project in projects:
        for query in project.get("queries", []):
            keyword = query.strip('"').lower()
            if keyword and keyword in text_lower:
                return project
    return projects[0] if projects else None


def _allow_tg_ingest(client_ip: str, limit: int = 12, window_seconds: int = 60) -> bool:
    now = time.time()
    with TG_INGEST_RATE_LOCK:
        bucket = [ts for ts in TG_INGEST_RATE_STATE.get(client_ip, []) if now - ts < window_seconds]
        if len(bucket) >= limit:
            TG_INGEST_RATE_STATE[client_ip] = bucket
            return False
        bucket.append(now)
        TG_INGEST_RATE_STATE[client_ip] = bucket
        return True


def _safe_int(value: str | None, default: int) -> int:
    try:
        return int(value or default)
    except (TypeError, ValueError):
        return default


_LAST_SESSION_PURGE = 0.0


class App(BaseHTTPRequestHandler):
    config_path = "config.json"

    def session_token(self) -> str:
        header = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie()
        try:
            jar.load(header)
        except cookies.CookieError:
            return ""
        morsel = jar.get("mm_session")
        return morsel.value if morsel else ""

    def current_user(self):
        if hasattr(self, "_current_user"):
            return self._current_user
        config = load_config(self.config_path)
        conn = connect(config["database"])
        try:
            # get_session_user сам отсекает протухшие сессии (expires_at > now),
            # поэтому чистку делаем редко (раз в 10 мин), а не на каждом запросе —
            # это убирает запись в БД из горячего пути чтения страниц.
            global _LAST_SESSION_PURGE
            now = time.time()
            if now - _LAST_SESSION_PURGE > 600:
                purge_expired_sessions(conn)
                _LAST_SESSION_PURGE = now
            self._current_user = get_session_user(conn, self.session_token())
        finally:
            conn.close()
        return self._current_user

    def require_auth(self) -> bool:
        if self.current_user():
            return True
        self.redirect("/login")
        return False

    def respond(self, status: int, body: str | bytes, content_type: str = "text/html; charset=utf-8"):
        payload = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def redirect(self, location: str, cookie_header: str | None = None):
        self.send_response(303)
        self.send_header("Location", location)
        if cookie_header:
            self.send_header("Set-Cookie", cookie_header)
        self.end_headers()

    def send_file(self, path: str, content_type: str, filename: str):
        with open(path, "rb") as fh:
            payload = fh.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    # ── Static assets ────────────────────────────────────────────────────────
    _ICON_SVG = """\
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0d3340"/>
      <stop offset="100%" stop-color="#173f4c"/>
    </linearGradient>
    <linearGradient id="shine" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="rgba(255,255,255,0.14)"/>
      <stop offset="100%" stop-color="rgba(255,255,255,0)"/>
    </linearGradient>
  </defs>
  <rect width="512" height="512" rx="114" fill="url(#bg)"/>
  <rect width="512" height="280" rx="114" fill="url(#shine)"/>
  <text x="256" y="318"
    font-family="Inter, system-ui, -apple-system, Arial, sans-serif"
    font-size="196" font-weight="900" letter-spacing="4"
    fill="white" text-anchor="middle">PR</text>
</svg>"""

    _MANIFEST_JSON = """\
{
  "name": "PR Monitor",
  "short_name": "PR Monitor",
  "description": "media intelligence",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0b3d52",
  "theme_color": "#147487",
  "icons": [
    {"src": "/icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}
  ]
}"""

    def do_GET(self):
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if parsed.path == "/icon.svg":
            self.respond(200, self._ICON_SVG.encode(), "image/svg+xml")
            return
        if parsed.path == "/manifest.json":
            self.respond(200, self._MANIFEST_JSON.encode(), "application/manifest+json")
            return
        if parsed.path == "/login":
            if self.current_user():
                self.redirect("/")
            else:
                self.respond(200, render_login())
            return
        if parsed.path == "/register":
            self.respond(200, render_register())
            return
        if parsed.path == "/forgot-password":
            self.respond(200, render_forgot_password())
            return
        if parsed.path == "/reset-password":
            token = first_param(params, "token")
            config = load_config(self.config_path)
            conn = connect(config["database"])
            try:
                if not token or not has_valid_password_reset_token(conn, token):
                    self.respond(
                        200,
                        render_auth_notice(
                            "Ссылка недействительна",
                            "Эта ссылка для смены пароля уже использована или срок её действия закончился.",
                            [("/forgot-password", "Запросить новую ссылку"), ("/login", "Вернуться ко входу")],
                        ),
                    )
                    return
            finally:
                conn.close()
            self.respond(200, render_reset_password(token))
            return
        if parsed.path == "/verify-email":
            token = first_param(params, "token")
            config = load_config(self.config_path)
            conn = connect(config["database"])
            try:
                row = consume_email_verification_token(conn, token) if token else None
                if not row:
                    self.respond(
                        200,
                        render_auth_notice(
                            "Ссылка недействительна",
                            "Ссылка подтверждения уже использована или больше не действует.",
                            [("/login", "Перейти ко входу"), ("/forgot-password", "Восстановить доступ")],
                        ),
                    )
                    return
                mark_user_email_verified(conn, int(row["user_id"]))
            finally:
                conn.close()
            self.respond(
                200,
                render_auth_notice(
                    "Почта подтверждена",
                    "Кабинет активирован. Теперь можно войти в сервис по почте и паролю из письма.",
                    [("/login", "Открыть вход")],
                ),
            )
            return
        if parsed.path == "/logout":
            config = load_config(self.config_path)
            conn = connect(config["database"])
            try:
                delete_session(conn, self.session_token())
            finally:
                conn.close()
            self.redirect("/login", "mm_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax")
            return
        # VK returns here from another domain, so the browser may not have a
        # session cookie when authorization was started from the old IP URL.
        if parsed.path != "/vk-oauth-callback" and not self.require_auth():
            return
        user = self.current_user()
        if parsed.path == "/":
            self.respond(200, render_dashboard(self.config_path, params, user))
            return
        if parsed.path == "/api/collection-status":
            self.respond(
                200,
                json.dumps(_collection_state(), ensure_ascii=False),
                "application/json; charset=utf-8",
            )
            return
        if parsed.path == "/settings":
            if not _is_superadmin(user):
                self.respond(403, "Недостаточно прав")
                return
            self.respond(200, render_settings(self.config_path, user=user))
            return
        if parsed.path == "/topics":
            self.respond(200, render_topics(self.config_path, query_params=params, user=user))
            return
        if parsed.path == "/agent":
            self.respond(200, render_agent_page(self.config_path, params, user))
            return
        if parsed.path == "/admin":
            if user["role"] != "admin":
                self.respond(403, "Недостаточно прав")
                return
            self.respond(200, render_admin(self.config_path, user, query_params=params))
            return
        if parsed.path == "/billing":
            if not _is_superadmin(user):
                self.respond(403, "Недостаточно прав")
                return
            self.respond(200, render_billing(self.config_path, user, query_params=params))
            return
        if parsed.path == "/analytics":
            if not _is_superadmin(user):
                self.respond(403, "Недостаточно прав")
                return
            self.respond(200, render_analytics(self.config_path, user, query_params=params))
            return
        if parsed.path == "/upgrade":
            self.respond(200, render_upgrade(self.config_path, user))
            return
        if parsed.path == "/billing/return":
            self.respond(200, render_payment_return(self.config_path, user))
            return
        if parsed.path == "/ollama-test":
            self.respond(200, render_ollama_test(self.config_path, user))
            return
        if parsed.path == "/claude-test":
            self.respond(200, render_claude_test(self.config_path, user))
            return
        if parsed.path == "/yandex-gpt-test":
            self.respond(200, render_yandex_gpt_test(self.config_path, user))
            return
        if parsed.path == "/vk-id-connect":
            config = load_config(self.config_path)
            try:
                self.redirect(begin_vk_id_connection(config))
            except Exception as exc:
                self.respond(
                    400,
                    f"<html><body><h2>VK ID</h2><p>{esc(str(exc))}</p>"
                    "<a href='/settings#social'>Вернуться в настройки</a></body></html>",
                )
            return
        if parsed.path == "/vk-token-capture":
            # Страница для implicit flow: JS читает токен из URL-фрагмента и POST-ит на сервер
            self.respond(200, """<!doctype html>
<html lang="ru"><head><meta charset="utf-8">
<title>VK — сохранение токена</title>
<style>body{font-family:Inter,Arial,sans-serif;display:grid;place-items:center;min-height:100vh;margin:0;background:#f4f7f9}
.card{background:#fff;border-radius:12px;padding:32px 40px;box-shadow:0 10px 40px rgba(0,0,0,.12);text-align:center;max-width:440px}
h2{margin:0 0 10px;color:#173a47}.hint{color:#667782;margin-bottom:20px}
.btn{background:#1f6f85;color:#fff;border:0;border-radius:8px;padding:12px 24px;font-size:16px;font-weight:700;cursor:pointer}
.ok{color:#116038;background:#dff5e8;border-radius:8px;padding:14px;margin-top:16px}
.err{color:#9c2a24;background:#fde2e0;border-radius:8px;padding:14px;margin-top:16px}</style>
</head><body><div class="card">
  <h2>VK авторизация</h2>
  <p class="hint" id="msg">Читаю токен...</p>
  <div id="result"></div>
</div>
<script>
(function(){
  var hash = location.hash.slice(1);
  var params = {};
  hash.split('&').forEach(function(p){ var kv=p.split('='); params[kv[0]]=decodeURIComponent(kv[1]||''); });
  if(!params.access_token){ document.getElementById('msg').textContent='Токен не найден в URL. Попробуйте ещё раз.'; return; }
  document.getElementById('msg').textContent='Сохраняю токен...';
  fetch('/vk-save-token', {method:'POST', headers:{'Content-Type':'application/json'},
    body: JSON.stringify({token: params.access_token})
  }).then(function(r){ return r.json(); }).then(function(data){
    if(data.ok){
      document.getElementById('result').innerHTML = '<div class="ok">✅ Токен сохранён! <br><a href="/vk-test">Проверить VK</a> &nbsp; <a href="/settings#social">Настройки</a></div>';
      document.getElementById('msg').textContent = '';
    } else {
      document.getElementById('result').innerHTML = '<div class="err">Ошибка: '+data.error+'</div>';
    }
  }).catch(function(e){ document.getElementById('result').innerHTML='<div class="err">'+e+'</div>'; });
})();
</script></body></html>""")
            return
        if parsed.path == "/vk-oauth-callback":
            code = first_param(params, "code")
            device_id = first_param(params, "device_id")
            state = first_param(params, "state")
            error = first_param(params, "error")
            if error:
                self.respond(200, f"<html><body><h2>VK OAuth: отказано</h2><p>{esc(first_param(params,'error_description',''))}</p><a href='/settings#social'>← Назад</a></body></html>")
                return
            if not code:
                self.respond(200, "<html><body><h2>VK OAuth: код не получен</h2><a href='/settings#social'>← Назад</a></body></html>")
                return
            config = load_config(self.config_path)
            if device_id and state:
                ok, result_message = finish_vk_id_connection(
                    config,
                    code=code,
                    device_id=device_id,
                    state=state,
                )
                heading = "VK подключён" if ok else "VK ID не подходит для сбора"
                self.respond(
                    200,
                    f"""<!doctype html><html lang="ru"><head><meta charset="utf-8">
                    <title>{esc(heading)}</title><style>{STYLE}</style></head><body>
                    <main class="wrap"><section class="card"><h2>{esc(heading)}</h2>
                    <p>{esc(result_message)}</p>
                    <div class="bar"><a class="btn" href="/vk-test">Проверить VK</a>
                    <a class="btn light" href="/settings#social">Вернуться в настройки</a></div>
                    </section></main></body></html>""",
                )
                return
            vk_app_id = secret_value(config, "VK_APP_ID")
            vk_secret = secret_value(config, "VK_CLIENT_SECRET")
            try:
                token_url = (
                    "https://oauth.vk.com/access_token?"
                    + urlencode({"client_id": vk_app_id, "client_secret": vk_secret,
                                 "redirect_uri": VK_REDIRECT_URI, "code": code})
                )
                import urllib.request as _ur
                resp = json.loads(_ur.urlopen(token_url, timeout=10).read())
                if "access_token" in resp:
                    secrets = load_secrets(config)
                    secrets["VK_ACCESS_TOKEN"] = resp["access_token"]
                    save_secrets(config, secrets)
                    self.respond(200, """<html><head><meta charset="utf-8"></head><body>
                        <h2>✅ VK токен получен и сохранён</h2>
                        <p>Токен выдан с IP сервера — теперь VK будет работать в сборе.</p>
                        <a href='/vk-test'>Проверить VK</a> &nbsp; <a href='/settings#social'>← Настройки</a>
                    </body></html>""")
                else:
                    err = resp.get("error_description") or resp.get("error") or str(resp)
                    self.respond(200, f"<html><body><h2>❌ Ошибка получения токена</h2><p>{esc(err)}</p><a href='/settings#social'>← Назад</a></body></html>")
            except Exception as exc:
                self.respond(200, f"<html><body><h2>❌ Ошибка</h2><p>{esc(str(exc))}</p><a href='/settings#social'>← Назад</a></body></html>")
            return
        if parsed.path == "/vk-test":
            self.respond(200, render_vk_test(self.config_path, user))
            return
        if parsed.path == "/yandex-test":
            self.respond(200, render_yandex_test(self.config_path, user))
            return
        if parsed.path == "/google-test":
            self.respond(200, render_google_test(self.config_path, user))
            return
        if parsed.path == "/serper-test":
            self.respond(200, render_serper_test(self.config_path, user))
            return
        if parsed.path == "/collect":
            self.redirect("/")
            return
        if parsed.path == "/api/agent":
            config = load_config(self.config_path)
            project = normalize_project_filter(config, user, first_param(params, "project", "all"))
            conn = connect(config["database"])
            analysis = analyze_project(
                conn,
                config,
                project,
                sentiment=first_param(params, "sentiment", "all"),
                search=first_param(params, "q"),
                collected_from=first_param(params, "collected_from"),
                collected_to=first_param(params, "collected_to"),
                account_id=account_id_of(user),
            )
            conn.close()
            self.respond(200, json.dumps(analysis, ensure_ascii=False, indent=2), "application/json; charset=utf-8")
            return
        if parsed.path == "/report":
            config = load_config(self.config_path)
            project = normalize_project_filter(config, user, first_param(params, "project", "all"))
            conn = connect(config["database"])
            filters = {
                "project": project,
                "sentiment": first_param(params, "sentiment", "all"),
                "search": first_param(params, "q"),
                "collected_from": first_param(params, "collected_from"),
                "collected_to": first_param(params, "collected_to"),
                "account_id": account_id_of(user),
            }
            path = export_xlsx(conn, **filters)
            conn.close()
            self.send_file(path, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", os.path.basename(path))
            return
        if parsed.path == "/api/mentions":
            config = load_config(self.config_path)
            project = normalize_project_filter(config, user, first_param(params, "project", "all"))
            conn = connect(config["database"])
            limit = max(1, min(_safe_int(first_param(params, "limit", "500"), 500), 5000))
            offset = max(0, _safe_int(first_param(params, "offset", "0"), 0))
            rows = [
                dict(row)
                for row in latest_mentions(
                    conn,
                    limit=limit,
                    offset=offset,
                    project=project,
                    sentiment=first_param(params, "sentiment", "all"),
                    search=first_param(params, "q"),
                    collected_from=first_param(params, "collected_from"),
                    collected_to=first_param(params, "collected_to"),
                    account_id=account_id_of(user),
                )
            ]
            conn.close()
            self.respond(200, json.dumps(rows, ensure_ascii=False, indent=2), "application/json; charset=utf-8")
            return
        if parsed.path == "/api/stats":
            if not user:
                self.respond(401, '{"error":"unauthorized"}', "application/json")
                return
            config = load_config(self.config_path)
            project = normalize_project_filter(config, user, first_param(params, "project", "all"))
            conn = connect(config["database"])
            stats = dashboard_stats(
                conn,
                sentiment=first_param(params, "sentiment"),
                search=first_param(params, "q"),
                collected_from=first_param(params, "collected_from"),
                collected_to=first_param(params, "collected_to"),
                project=project,
                account_id=account_id_of(user),
            )
            conn.close()
            self.respond(200, json.dumps(stats, ensure_ascii=False, indent=2), "application/json; charset=utf-8")
            return
        if parsed.path == "/api/projects":
            if not user:
                self.respond(401, '{"error":"unauthorized"}', "application/json")
                return
            config = load_config(self.config_path)
            projects = [
                {"name": p["name"], "queries": p.get("queries", []), "language": p.get("language", "ru")}
                for p in visible_projects(config, user)
            ]
            self.respond(200, json.dumps(projects, ensure_ascii=False, indent=2), "application/json; charset=utf-8")
            return
        if parsed.path == "/api/project-autofill":
            name = first_param(params, "name")
            result = project_autofill(
                self.config_path,
                name,
                city=first_param(params, "city"),
                industry=first_param(params, "industry"),
            )
            status = 200 if result.get("ok") else 400
            self.respond(status, json.dumps(result, ensure_ascii=False, indent=2), "application/json; charset=utf-8")
            return
        self.respond(404, "Not found")

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/tg-ingest":
            self._handle_tg_ingest()
            return
        if parsed.path == "/yookassa-webhook":
            # Публичный вебхук ЮKassa (без сессии). Подлинность платежа проверяется
            # повторным запросом к API ЮKassa внутри process_webhook.
            from .yookassa import process_webhook
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length else b""
            try:
                ok, msg = process_webhook(load_config(self.config_path), raw)
            except Exception:
                LOGGER.exception("YooKassa webhook failed")
                ok, msg = False, "error"
            # ЮKassa ждёт 200, иначе будет повторять. На ошибки парсинга отвечаем 400.
            self.respond(200 if ok else 400, json.dumps({"ok": ok, "msg": msg}), "application/json")
            return
        if parsed.path == "/vk-save-token":
            user = get_session_user(connect(load_config(self.config_path)["database"]),
                                    self.session_token())
            if not _is_superadmin(user):
                self.respond(403, '{"ok":false,"error":"forbidden"}', content_type="application/json")
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                body = json.loads(self.rfile.read(length))
                token = (body.get("token") or "").strip()
                if not token:
                    self.respond(200, '{"ok":false,"error":"empty token"}', content_type="application/json")
                    return
                config = load_config(self.config_path)
                secrets = load_secrets(config)
                secrets["VK_ACCESS_TOKEN"] = token
                save_secrets(config, secrets)
                self.respond(200, '{"ok":true}', content_type="application/json")
            except Exception as exc:
                self.respond(200, json.dumps({"ok": False, "error": str(exc)}), content_type="application/json")
            return
        if parsed.path == "/login":
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
            username = first_param(form, "username")
            password = first_param(form, "password")
            config = load_config(self.config_path)
            conn = connect(config["database"])
            try:
                user = authenticate_user(conn, username, password)
                if not user:
                    self.respond(200, render_login("Неверный логин или пароль.", email=username))
                    return
                if user["email"] and not bool(user["email_verified"]):
                    self.respond(
                        200,
                        render_login(
                            "Почта ещё не подтверждена.",
                            "Подтвердите адрес по ссылке из письма, после этого вход сразу заработает.",
                            email=user["email"],
                        ),
                    )
                    return
                token = create_session(conn, user["id"])
            finally:
                conn.close()
            self.redirect("/", f"mm_session={token}; Path=/; Max-Age=2592000; HttpOnly; SameSite=Lax")
            return
        if parsed.path == "/register":
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
            full_name = first_param(form, "full_name")
            email = first_param(form, "email").strip().lower()
            if not email:
                self.respond(200, render_register("Укажите рабочую почту.", full_name=full_name, email=email))
                return
            config = load_config(self.config_path)
            smtp_info = smtp_status(config)
            if not smtp_info["ready"]:
                self.respond(
                    200,
                    render_register(
                        "Регистрация пока недоступна.",
                        f"Сервис ещё не настроил отправку писем: {smtp_info['message']}",
                        full_name=full_name,
                        email=email,
                    ),
                )
                return
            conn = connect(config["database"])
            try:
                existing = get_user_by_email(conn, email)
                password = _generate_temp_password()
                if existing and bool(existing["email_verified"]):
                    self.respond(
                        200,
                        render_register(
                            "Такой кабинет уже существует.",
                            "Попробуйте восстановить пароль или войти по уже созданному адресу.",
                            full_name=full_name,
                            email=email,
                        ),
                    )
                    return
                if existing:
                    # Существующий неподтверждённый: пароль НЕ трогаем до успешной отправки —
                    # иначе при сбое SMTP человек останется с новым, никому не известным паролем.
                    user_id = int(existing["id"])
                    verify_token = create_email_verification_token(conn, user_id, email)
                    verify_url = build_public_url(config, "/verify-email", token=verify_token)
                    mailed, mail_message = send_verification_email(config, email, full_name or email, password, verify_url)
                    if mailed:
                        update_user_password(conn, user_id, password)
                else:
                    user_id = create_public_user(conn, email, password, full_name)
                    verify_token = create_email_verification_token(conn, user_id, email)
                    verify_url = build_public_url(config, "/verify-email", token=verify_token)
                    mailed, mail_message = send_verification_email(config, email, full_name or email, password, verify_url)
            finally:
                conn.close()
            if not mailed:
                self.respond(
                    200,
                    render_register(
                        "Не удалось отправить письмо.",
                        f"Сервис сохранил заявку, но почта пока не настроена: {mail_message}",
                        full_name=full_name,
                        email=email,
                    ),
                )
                return
            self.respond(
                200,
                render_auth_notice(
                    "Письмо отправлено",
                    "Мы отправили на вашу почту временный пароль и ссылку подтверждения. После подтверждения адреса вход сразу станет доступен.",
                    [("/login", "Перейти ко входу")],
                ),
            )
            return
        if parsed.path == "/forgot-password":
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
            email = first_param(form, "email").strip().lower()
            config = load_config(self.config_path)
            smtp_info = smtp_status(config)
            if not smtp_info["ready"]:
                self.respond(
                    200,
                    render_forgot_password(
                        error="Восстановление пока недоступно.",
                        info=f"Сервис ещё не настроил отправку писем: {smtp_info['message']}",
                        email=email,
                    ),
                )
                return
            mailed = True
            mail_message = ""
            if email:
                conn = connect(config["database"])
                try:
                    existing = get_user_by_email(conn, email)
                    if existing:
                        token = create_password_reset_token(conn, int(existing["id"]), email)
                        reset_url = build_public_url(config, "/reset-password", token=token)
                        mailed, mail_message = send_password_reset_email(config, email, existing["full_name"] or email, reset_url)
                finally:
                    conn.close()
            info = "Если адрес есть в системе, письмо со ссылкой уже отправлено."
            if email and not mailed:
                info = f"Не удалось отправить письмо: {mail_message}"
            self.respond(200, render_forgot_password(info=info, email=email))
            return
        if parsed.path == "/reset-password":
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
            token = first_param(form, "token")
            password = first_param(form, "password")
            confirm = first_param(form, "password_confirm")
            if not token:
                self.respond(200, render_auth_notice("Ссылка недействительна", "Не найден токен для смены пароля.", [("/forgot-password", "Запросить новую ссылку")]))
                return
            if not password or len(password) < 8:
                self.respond(200, render_reset_password(token, error="Новый пароль должен быть не короче 8 символов."))
                return
            if password != confirm:
                self.respond(200, render_reset_password(token, error="Пароли не совпадают."))
                return
            config = load_config(self.config_path)
            conn = connect(config["database"])
            try:
                row = consume_password_reset_token(conn, token)
                if not row:
                    self.respond(
                        200,
                        render_auth_notice(
                            "Ссылка недействительна",
                            "Ссылка для смены пароля уже использована или больше не действует.",
                            [("/forgot-password", "Запросить новую ссылку"), ("/login", "Вернуться ко входу")],
                        ),
                    )
                    return
                update_user_password(conn, int(row["user_id"]), password)
            finally:
                conn.close()
            self.respond(
                200,
                render_auth_notice(
                    "Пароль обновлён",
                    "Новый пароль сохранён. Теперь можно войти в кабинет.",
                    [("/login", "Перейти ко входу")],
                ),
            )
            return
        if not self.require_auth():
            return
        user = self.current_user()
        if parsed.path == "/dashboard-project":
            length = int(self.headers.get("Content-Length", "0"))
            project_name, run_now = handle_dashboard_project_post(self.config_path, self.rfile.read(length), user)
            if run_now:
                if COLLECT_LOCK.acquire(blocking=False):
                    try:
                        collect_once(
                            self.config_path,
                            fetch_pages=False,
                            source_types=NEWS_SLICE_SOURCE_TYPES,
                            period="30d",
                            depth="standard",
                            project_name=project_name,
                            expand_queries=True,
                        )
                    finally:
                        COLLECT_LOCK.release()
            self.redirect("/?project=" + quote(project_name))
            return
        if parsed.path == "/collect":
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
            fetch_pages = True if not length else "fetch_pages" in form
            expand_queries = True if not length else "expand_queries" in form
            mode = first_param(form, "mode")
            period = first_param(form, "period", "30d")
            if period not in {"1d", "3d", "7d", "14d", "30d", "60d", "90d"}:
                period = "30d"
            depth = first_param(form, "depth", "standard")
            if depth not in {"fast", "standard", "deep"}:
                depth = "standard"
            project_name = first_param(form, "project")
            config = load_config(self.config_path)
            project_name = normalize_project_filter(config, user, project_name)
            source_types = None
            if length:
                source_types = NEWS_SLICE_SOURCE_TYPES if mode == "news_slice" else (form.get("source_types") or None)
            if not COLLECT_LOCK.acquire(blocking=False):
                result = _collection_state()
                result["error"] = "Сбор уже выполняется"
            else:
                started_at = datetime.now(timezone.utc).isoformat()
                result = _collection_state(
                    status="starting",
                    project=project_name or "все проекты",
                    started_at=started_at,
                    finished_at=None,
                    found=0,
                    inserted=0,
                    error=None,
                )
                options = {
                    "fetch_pages": fetch_pages,
                    "source_types": source_types,
                    "period": period,
                    "depth": depth,
                    "project_name": project_name or None,
                    "expand_queries": expand_queries,
                }
                threading.Thread(
                    target=_run_collection,
                    args=(self.config_path, options),
                    daemon=True,
                    name="mention-collection",
                ).start()
                result["status"] = "starting"
            if "application/json" in self.headers.get("Accept", ""):
                self.respond(202, json.dumps(result, ensure_ascii=False), "application/json; charset=utf-8")
                return
            self.redirect("/?project=" + quote(project_name or "all") + "&collect_started=1#collect")
            return
        if parsed.path == "/correct-sentiment":
            length = int(self.headers.get("Content-Length", "0"))
            form = parse_qs(self.rfile.read(length).decode("utf-8")) if length else {}
            project_name = first_param(form, "project")

            def _run_correction(cfg_path: str) -> None:
                try:
                    from .ai_audit import correct_all_pending
                    correct_all_pending(cfg_path, max_items=800)
                except Exception:
                    LOGGER.exception("Manual sentiment correction failed")

            threading.Thread(target=_run_correction, args=(self.config_path,), daemon=True,
                             name="sentiment-correction").start()
            self.redirect("/admin?sentiment_correcting=1")
            return
        if parsed.path == "/settings":
            if not _is_superadmin(user):
                self.respond(403, "Недостаточно прав")
                return
            length = int(self.headers.get("Content-Length", "0"))
            handle_settings_post(self.config_path, self.rfile.read(length))
            self.respond(200, render_settings(self.config_path, "Интеграции сохранены", user))
            return
        if parsed.path == "/topics":
            length = int(self.headers.get("Content-Length", "0"))
            topics_message = handle_topics_post(self.config_path, self.rfile.read(length), user)
            self.respond(200, render_topics(self.config_path, topics_message or "Тема мониторинга сохранена", user=user))
            return
        if parsed.path == "/admin":
            if user["role"] != "admin":
                self.respond(403, "Недостаточно прав")
                return
            length = int(self.headers.get("Content-Length", "0"))
            message = handle_admin_post(self.config_path, self.rfile.read(length), user)
            self.respond(200, render_admin(self.config_path, user, message))
            return
        if parsed.path == "/billing":
            if not _is_superadmin(user):
                self.respond(403, "Недостаточно прав")
                return
            length = int(self.headers.get("Content-Length", "0"))
            message = handle_billing_post(self.config_path, self.rfile.read(length), user)
            self.respond(200, render_billing(self.config_path, user, message))
            return
        if parsed.path == "/pay":
            length = int(self.headers.get("Content-Length", "0"))
            ok, result = handle_pay(self.config_path, self.rfile.read(length), user)
            if ok:
                self.redirect(result)  # ссылка оплаты ЮKassa
            else:
                self.respond(200, render_upgrade(self.config_path, user, result))
            return
        self.respond(404, "Not found")

    def _handle_tg_ingest(self):
        config = load_config(self.config_path)
        expected_token = secret_value(config, "TG_RELAY_TOKEN").strip()
        if not expected_token:
            self.respond(403, '{"ok":false,"error":"TG_RELAY_TOKEN не настроен"}', "application/json")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length <= 0 or length > 2_000_000:
                self.respond(413, '{"ok":false,"error":"payload too large"}', "application/json")
                return
            body = json.loads(self.rfile.read(length))
        except Exception:
            self.respond(400, '{"ok":false,"error":"invalid json"}', "application/json")
            return
        authorization = self.headers.get("Authorization", "")
        supplied_token = authorization[7:].strip() if authorization.startswith("Bearer ") else ""
        if not supplied_token or not hmac.compare_digest(supplied_token, expected_token):
            self.respond(403, '{"ok":false,"error":"unauthorized"}', "application/json")
            return
        client_ip = (self.client_address[0] or "unknown").strip()
        if not _allow_tg_ingest(client_ip):
            self.respond(429, '{"ok":false,"error":"too many requests"}', "application/json")
            return
        posts = body.get("posts") or []
        if not isinstance(posts, list):
            self.respond(400, '{"ok":false,"error":"posts must be a list"}', "application/json")
            return
        posts = posts[:200]

        from .analysis import detect_language, extract_entities, normalize_text, sentiment
        from .collector import content_hash, utc_now
        from .db import insert_mention, list_projects

        conn = connect(config["database"])
        tg_projects = list_projects(conn)  # загружаем один раз, не на каждый пост
        inserted = 0
        for post in posts:
            channel = (post.get("channel") or "").strip()
            text = (post.get("text") or "").strip()[:20_000]
            url = (post.get("url") or "").strip()
            if not channel or not text or not url:
                continue

            channel_display = f"TG: @{channel}"
            title = text[:120].replace("\n", " ")
            norm = normalize_text(text)
            sent_label, sent_score = sentiment(norm)
            entities = extract_entities(text)
            lang = detect_language(text)
            digest = content_hash(url, title)

            matched = _match_tg_project(tg_projects, text)
            if not matched:
                continue  # нет проектов — некуда привязать упоминание
            mention = {
                "account_id": matched.get("account_id"),
                "project": matched["name"],
                "query": f"@{channel}",
                "title": title,
                "snippet": text[:300],
                "text": text,
                "url": url,
                "source": channel_display,
                "published_at": post.get("date"),
                "collected_at": utc_now(),
                "sentiment": sent_label,
                "sentiment_score": sent_score,
                "language": lang,
                "entities": entities,
                "raw_path": None,
                "content_hash": digest,
                "likes": 0,
                "reposts": int(post.get("forwards") or 0),
                "comments": 0,
                "views": int(post.get("views") or 0),
            }
            if insert_mention(conn, mention):
                inserted += 1

        conn.close()
        self.respond(200, json.dumps({"ok": True, "received": len(posts), "inserted": inserted}), "application/json")

    def log_message(self, fmt, *args):
        LOGGER.info(fmt, *args)


def run_server(host: str = "127.0.0.1", port: int = 8765, config_path: str = "config.json"):
    App.config_path = config_path
    server = ThreadingHTTPServer((host, port), App)
    LOGGER.info("Dashboard: http://%s:%s", host, port)
    server.serve_forever()
