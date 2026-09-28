"""HTTP API и отдача сайта."""
from __future__ import annotations

import html
import ipaddress
import json
import logging
import os
import re
import time

from fastapi import FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles

from . import config, db, services
from .audio import io as aio
from .audio.pipeline import MAX_TARGET, MIN_TARGET, export, fmt_time
from .payments import PaymentError

log = logging.getLogger("takt")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC = os.path.join(ROOT, "static")

ALLOWED_EXT = {".mp3", ".m4a", ".aac", ".wav", ".ogg", ".oga", ".opus", ".flac", ".wma", ".mp4", ".mov",
               ".webm", ".3gp", ".amr", ".aif", ".aiff"}
CLIENT_EVENTS = {"landing_view", "upload_start", "upload_error", "preview_play", "seam_jump", "variant_selected",
                 "checkout_open", "download_click", "pack_offer_view", "faq_open", "demo_play", "rebuild_open",
                 "restore_open", "results_view"}
YOOKASSA_NETS = [ipaddress.ip_network(n) for n in (
    "185.71.76.0/27", "185.71.77.0/27", "77.75.153.0/25", "77.75.156.11/32", "77.75.156.35/32",
    "77.75.154.128/25", "2a02:5180::/32")]

app = FastAPI(title="Такт", docs_url=None, redoc_url=None, openapi_url=None)
app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    resp.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    if request.url.path.startswith("/api/"):
        resp.headers.setdefault("Cache-Control", "no-store")
    return resp


def client_ip(request: Request) -> str:
    if config.settings.trust_proxy:
        fwd = request.headers.get("x-forwarded-for")
        if fwd:
            return fwd.split(",")[0].strip()
    return request.client.host if request.client else "0.0.0.0"


def get_job(job_id: str, token: str | None):
    job = db.one("SELECT * FROM jobs WHERE id=?", job_id)
    if not services.check_token(job, token):
        raise HTTPException(404, "Задание не найдено")
    return job


def parse_time(value: str) -> float:
    value = (value or "").strip().replace(",", ".")
    m = re.fullmatch(r"(\d{1,2})[:.](\d{1,2}(?:\.\d+)?)", value)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    try:
        return float(value)
    except ValueError:
        raise HTTPException(400, "Не понял длительность. Пример: 1:30")


# ---------- страницы ----------

def _page(name: str) -> str:
    with open(os.path.join(STATIC, name), encoding="utf-8") as f:
        return f.read()


def _render_index() -> str:
    s = config.settings
    page = _page("index.html")
    metrika = ""
    if s.metrika_id.isdigit():
        metrika = (
            '<script>(function(m,e,t,r,i,k,a){m[i]=m[i]||function(){(m[i].a=m[i].a||[]).push(arguments)};'
            'm[i].l=1*new Date();for(var j=0;j<document.scripts.length;j++){if(document.scripts[j].src===r)'
            '{return;}}k=e.createElement(t),a=e.getElementsByTagName(t)[0],k.async=1,k.src=r,a.parentNode.'
            'insertBefore(k,a)})(window,document,"script","https://mc.yandex.ru/metrika/tag.js","ym");'
            f'ym({s.metrika_id},"init",{{clickmap:true,trackLinks:true,accurateTrackBounce:true,webvisor:true}});'
            f'window.METRIKA_ID={s.metrika_id};</script>'
        )
    cfg = {"brand": s.brand, "priceSingle": s.price_single, "pricePack": s.price_pack, "packSize": s.pack_size,
           "minTarget": MIN_TARGET, "maxTarget": MAX_TARGET, "maxUploadMb": s.max_upload_mb,
           "retentionDays": s.retention_days, "rebuilds": s.rebuilds_per_order,
           "contactEmail": s.contact_email, "contactTelegram": s.contact_telegram,
           "mockPayments": s.payment_provider == "mock", "requireEmail": s.yookassa_receipt}
    return (page.replace("<!--METRIKA-->", metrika)
                .replace("/*CONFIG*/{}", json.dumps(cfg, ensure_ascii=False))
                .replace("{{BRAND}}", html.escape(s.brand))
                .replace("{{PRICE_SINGLE}}", str(s.price_single))
                .replace("{{PRICE_PACK}}", str(s.price_pack))
                .replace("{{PACK_SIZE}}", str(s.pack_size))
                .replace("{{BASE_URL}}", s.base_url))


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(_render_index(), headers={"Cache-Control": "no-cache"})


def _legal(name: str) -> HTMLResponse:
    s = config.settings
    page = _page(name)
    for k, v in {"BRAND": s.brand, "SELLER_NAME": s.seller_name, "SELLER_INN": s.seller_inn,
                 "SELLER_STATUS": s.seller_status, "CONTACT_EMAIL": s.contact_email, "BASE_URL": s.base_url,
                 "PRICE_SINGLE": str(s.price_single), "PRICE_PACK": str(s.price_pack),
                 "PACK_SIZE": str(s.pack_size), "RETENTION_DAYS": str(s.retention_days),
                 "REBUILDS": str(s.rebuilds_per_order)}.items():
        page = page.replace("{{" + k + "}}", html.escape(v))
    return HTMLResponse(page)


@app.get("/offer", response_class=HTMLResponse)
def offer():
    return _legal("offer.html")


@app.get("/privacy", response_class=HTMLResponse)
def privacy():
    return _legal("privacy.html")


@app.get("/robots.txt")
def robots():
    return Response(f"User-agent: *\nDisallow: /api/\nDisallow: /d/\nDisallow: /admin\nDisallow: /mock-pay/\n"
                    f"Sitemap: {config.settings.base_url}/sitemap.xml\n", media_type="text/plain")


@app.get("/sitemap.xml")
def sitemap():
    b = config.settings.base_url
    urls = "".join(f"<url><loc>{b}{p}</loc></url>" for p in ("/", "/offer", "/privacy"))
    return Response(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/'
                    f'sitemap/0.9">{urls}</urlset>', media_type="application/xml")


@app.get("/healthz")
def healthz():
    db.one("SELECT 1")
    q = db.one("SELECT COUNT(*) c FROM jobs WHERE status IN ('queued','processing')")["c"]
    return {"ok": True, "queue": q}


# ---------- задания ----------

@app.post("/api/jobs")
async def create_job(request: Request, file: UploadFile = File(...), target: str = Form(...),
                     ending: str = Form("natural"), signal: str = Form("0"), tempo: str = Form("1"),
                     x_device: str | None = Header(None)):
    s = config.settings
    ip = client_ip(request)
    device = (x_device or "")[:64] or None
    per_hour, per_day = s.free_jobs_per_hour, s.free_jobs_per_day
    if services.is_customer(ip, device):
        per_hour, per_day = per_hour * 8, per_day * 15     # покупатели (тренеры с пакетами) работают пачками
    if services.jobs_today(ip, device, 3600) >= per_hour or services.jobs_today(ip, device, 86400) >= per_day:
        db.event("rate_limited", None, device, ip)
        raise HTTPException(429, "Слишком много треков за короткое время. Попробуйте позже или напишите нам.")
    t = parse_time(target)
    if not (MIN_TARGET <= t <= MAX_TARGET):
        raise HTTPException(400, f"Длительность — от {int(MIN_TARGET)} секунд до {int(MAX_TARGET // 60)} минут.")
    try:
        tempo_f = float(tempo)
    except ValueError:
        tempo_f = 1.0
    if not (0.85 <= tempo_f <= 1.15):
        raise HTTPException(400, "Темп можно менять не больше чем на 15 %.")
    name = os.path.basename(file.filename or "track")[:120]
    ext = os.path.splitext(name)[1].lower()
    if ext not in ALLOWED_EXT:
        raise HTTPException(400, "Нужен аудиофайл: MP3, M4A, WAV, OGG, FLAC (или видео MP4/MOV — возьмём звук).")
    job_id = services.new_id()
    up_dir = os.path.join(s.data_dir, "uploads")
    os.makedirs(up_dir, exist_ok=True)
    path = os.path.join(up_dir, job_id + ext)
    limit = s.max_upload_mb * 1024 * 1024
    size = 0
    with open(path, "wb") as out:
        while chunk := await file.read(1024 * 1024):
            size += len(chunk)
            if size > limit:
                out.close()
                os.remove(path)
                raise HTTPException(413, f"Файл больше {s.max_upload_mb} МБ.")
            out.write(chunk)
    try:
        info = aio.probe(path)
    except aio.AudioError as e:
        os.remove(path)
        db.event("upload_rejected", None, device, ip, reason="probe")
        raise HTTPException(400, str(e))
    if info["duration"] and info["duration"] > 12 * 60:
        os.remove(path)
        raise HTTPException(400, "Трек длиннее 12 минут. Загрузите фрагмент покороче.")
    options = {"ending": "fade" if ending == "fade" else "natural", "signal": signal in ("1", "true", "on"),
               "tempo": round(tempo_f, 3)}
    job = services.create_job(source_path=path, filename=os.path.splitext(name)[0], target=t, options=options,
                              ip=ip, device=device, job_id=job_id)
    return {"id": job["id"], "token": job["token"]}


@app.get("/api/jobs/{job_id}")
def job_status(job_id: str, token: str):
    return services.public_job(get_job(job_id, token))


@app.get("/api/jobs/{job_id}/preview/{index}")
def preview(job_id: str, index: int, token: str):
    job = get_job(job_id, token)
    path = os.path.join(services.job_dir(job["id"]), f"v{index}_preview.mp3")
    if job["status"] != "done" or not os.path.exists(path):
        raise HTTPException(404, "Превью не найдено")
    return FileResponse(path, media_type="audio/mpeg", headers={"Cache-Control": "private, max-age=3600"})


@app.post("/api/jobs/{job_id}/checkout")
async def checkout(job_id: str, request: Request):
    body = await request.json()
    job = get_job(job_id, body.get("token"))
    variant = _variant(job, body.get("variant"))
    product = "pack" if body.get("product") == "pack" else "single"
    email = (body.get("email") or "").strip()[:120] or None
    if email and not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "Проверьте e-mail.")
    if config.settings.yookassa_receipt and not email:
        raise HTTPException(400, "Укажите e-mail — пришлём чек и ссылку на трек.")
    if variant in services.unlocked(job["id"]):
        raise HTTPException(409, "Этот вариант уже оплачен.")
    try:
        order = services.create_order(job, variant, product, email)
    except PaymentError as e:
        log.error("payment create failed: %s", e)
        raise HTTPException(502, "Платёжный сервис не ответил. Попробуйте ещё раз через минуту.")
    db.event("checkout_start", job["id"], order_id=order["id"], product=product, amount=order["amount"])
    return {"order_id": order["id"], "order_token": order["token"], "confirmation_url": order["confirmation_url"]}


@app.get("/api/orders/{order_id}")
def order_status(order_id: str, token: str):
    row = db.one("SELECT * FROM orders WHERE id=?", order_id)
    if not services.check_token(row, token):
        raise HTTPException(404, "Заказ не найден")
    try:
        order = services.refresh_order(order_id)
    except PaymentError as e:
        log.error("payment status failed: %s", e)
        order = dict(row)
    out = {"status": order["status"], "product": order["product"], "job_id": order["job_id"],
           "variant": order["variant"]}
    if order["status"] == "paid" and order["pack_code"]:
        out["pack_code"] = order["pack_code"]
        out["pack_remaining"] = services.pack_remaining(order["pack_code"])
    return out


@app.post("/api/jobs/{job_id}/redeem")
async def redeem(job_id: str, request: Request):
    body = await request.json()
    job = get_job(job_id, body.get("token"))
    variant = _variant(job, body.get("variant"))
    try:
        services.redeem(job, variant, str(body.get("code") or ""))
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True, "remaining": services.pack_remaining(str(body.get("code")))}


@app.post("/api/jobs/{job_id}/claim")
async def claim(job_id: str, request: Request):
    body = await request.json()
    job = get_job(job_id, body.get("token"))
    variant = _variant(job, body.get("variant"))
    try:
        services.claim_rebuild(job, variant)
    except ValueError as e:
        raise HTTPException(400, str(e))
    db.event("rebuild_claim", job["id"], variant=variant)
    return {"ok": True}


@app.post("/api/jobs/{job_id}/rebuild")
async def rebuild(job_id: str, request: Request):
    body = await request.json()
    job = get_job(job_id, body.get("token"))
    if services.rebuilds_left(job) <= 0:
        raise HTTPException(403, "Бесплатные пересборки для этого трека закончились.")
    if not os.path.exists(job["source_path"]):
        raise HTTPException(410, "Исходный файл уже удалён. Загрузите трек заново.")
    t = parse_time(str(body.get("target", "")))
    if not (MIN_TARGET <= t <= MAX_TARGET):
        raise HTTPException(400, f"Длительность — от {int(MIN_TARGET)} секунд до {int(MAX_TARGET // 60)} минут.")
    opts = json.loads(job["options"])
    if "ending" in body:
        opts["ending"] = "fade" if body["ending"] == "fade" else "natural"
    if "signal" in body:
        opts["signal"] = bool(body["signal"])
    root = services.root_order_for(job)
    new = services.create_job(source_path=job["source_path"], filename=job["filename"], target=t, options=opts,
                              ip=client_ip(request), device=job["device"], parent_id=job["id"], entitlement=root)
    return {"id": new["id"], "token": new["token"]}


@app.post("/api/jobs/{job_id}/feedback")
async def feedback(job_id: str, request: Request):
    body = await request.json()
    job = get_job(job_id, body.get("token"))
    rating = body.get("rating")
    if rating not in ("ready", "needs_fix", "bad"):
        raise HTTPException(400, "bad rating")
    db.run("INSERT INTO feedback (ts, job_id, variant, rating, comment) VALUES (?,?,?,?,?)", time.time(), job["id"],
           body.get("variant"), rating, (body.get("comment") or "")[:1000] or None)
    db.event("feedback", job["id"], rating=rating)
    return {"ok": True}


@app.post("/api/events")
async def events(request: Request, x_device: str | None = Header(None)):
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "bad json")
    name = body.get("name")
    if name not in CLIENT_EVENTS:
        raise HTTPException(400, "unknown event")
    props = body.get("props") if isinstance(body.get("props"), dict) else {}
    props = {str(k)[:32]: (v if isinstance(v, (int, float, bool)) else str(v)[:200]) for k, v in list(props.items())[:12]}
    db.event(name, (body.get("job_id") or None) and str(body["job_id"])[:20], (x_device or "")[:64] or None,
             client_ip(request), **props)
    return {"ok": True}


@app.post("/api/restore")
async def restore(request: Request):
    """Повторно отправить ссылки на купленные треки на e-mail (за последние RETENTION_DAYS дней)."""
    body = await request.json()
    email = (body.get("email") or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        raise HTTPException(400, "Проверьте e-mail.")
    ip = client_ip(request)
    recent = db.one("SELECT COUNT(*) c FROM events WHERE name='restore' AND ip=? AND ts>?", ip, time.time() - 3600)["c"]
    if recent >= 3:
        raise HTTPException(429, "Слишком много запросов. Попробуйте через час.")
    db.event("restore", None, None, ip)
    s = config.settings
    rows = db.all_("""SELECT u.download_token, j.filename, j.target FROM orders o
                      JOIN unlocks u ON u.job_id = o.job_id
                      JOIN jobs j ON j.id = u.job_id
                      WHERE lower(o.email)=? AND o.status='paid' AND u.created_at > ? AND j.status='done'""",
                   email, time.time() - s.retention_days * 86400)
    packs = db.all_("SELECT code, remaining FROM packs WHERE lower(email)=? AND remaining > 0", email)
    if rows or packs:
        from . import mailer

        lines = [f"{r['filename']} — {fmt_time(r['target'])}: {s.base_url}/d/{r['download_token']}/mp3" for r in rows]
        lines += [f"Код пакета {p['code']}: осталось {p['remaining']}" for p in packs]
        mailer.send(email, f"{s.brand}: ваши треки", "Ваши покупки:\n\n" + "\n".join(lines) + f"\n\n{s.base_url}\n")
    # одинаковый ответ, чтобы нельзя было проверить, покупал ли кто-то с этим адресом
    return {"ok": True}


def _variant(job, value) -> int:
    if job["status"] != "done":
        raise HTTPException(409, "Трек ещё обрабатывается.")
    try:
        v = int(value)
    except (TypeError, ValueError):
        raise HTTPException(400, "Выберите вариант.")
    meta = json.loads(job["meta"] or "{}")
    if v not in {x["index"] for x in meta.get("variants", [])}:
        raise HTTPException(400, "Нет такого варианта.")
    return v


# ---------- скачивание ----------

@app.get("/d/{token}/{fmt}")
def download(token: str, fmt: str):
    if fmt not in ("mp3", "wav"):
        raise HTTPException(404)
    row = db.one("""SELECT u.job_id, u.variant, j.filename, j.target, j.status, j.meta FROM unlocks u
                    JOIN jobs j ON j.id = u.job_id WHERE u.download_token=?""", token)
    if row is None:
        raise HTTPException(404, "Ссылка не найдена")
    if row["status"] != "done":
        return HTMLResponse("<meta charset=utf-8><p style='font:18px sans-serif;padding:40px'>Срок хранения файла "
                            "истёк. Загрузите трек заново — пересобрать можно за пару минут.</p>", status_code=410)
    title = f"{row['filename']} ({fmt_time(row['target']).replace('.0', '')})"
    path = export(services.job_dir(row["job_id"]), row["variant"], fmt, title)
    db.event("download", row["job_id"], fmt=fmt, variant=row["variant"])
    safe = re.sub(r"[^\w\-. ()]+", "_", f"{row['filename']} — {fmt_time(row['target']).replace(':', '-')}")
    return FileResponse(path, media_type="audio/mpeg" if fmt == "mp3" else "audio/wav",
                        filename=f"{safe}.{fmt}")


# ---------- платёжные уведомления ----------

@app.post("/api/payments/yookassa")
async def yookassa_webhook(request: Request):
    ip = client_ip(request)
    try:
        allowed = any(ipaddress.ip_address(ip) in n for n in YOOKASSA_NETS)
    except ValueError:
        allowed = False
    if not allowed:
        log.warning("webhook from unexpected ip %s", ip)  # не отказываем: статус всё равно перепроверяем в API
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)
    pid = ((body or {}).get("object") or {}).get("id")
    if pid:
        row = db.one("SELECT id FROM orders WHERE provider_payment_id=?", pid)
        if row:
            try:
                services.refresh_order(row["id"], force=True)
            except PaymentError as e:
                log.error("webhook verify failed: %s", e)
                return JSONResponse({"ok": False}, status_code=502)  # ЮKassa повторит уведомление
    return {"ok": True}


# ---------- тестовая оплата ----------

@app.get("/mock-pay/{order_id}", response_class=HTMLResponse)
def mock_pay(order_id: str, token: str):
    if config.settings.payment_provider != "mock":
        raise HTTPException(404)
    row = db.one("SELECT * FROM orders WHERE id=?", order_id)
    if not services.check_token(row, token):
        raise HTTPException(404)
    return HTMLResponse(_page("mock-pay.html").replace("{{AMOUNT}}", str(row["amount"]))
                        .replace("{{ORDER}}", order_id).replace("{{TOKEN}}", html.escape(token)))


@app.post("/mock-pay/{order_id}")
async def mock_pay_submit(order_id: str, request: Request):
    if config.settings.payment_provider != "mock":
        raise HTTPException(404)
    form = await request.form()
    row = db.one("SELECT * FROM orders WHERE id=?", order_id)
    if not services.check_token(row, form.get("token")):
        raise HTTPException(404)
    if form.get("action") == "pay":
        services.mark_paid(order_id)
    else:
        db.run("UPDATE orders SET status='canceled' WHERE id=? AND status='pending'", order_id)
    job = db.one("SELECT token FROM jobs WHERE id=?", row["job_id"])
    return RedirectResponse(f"/?job={row['job_id']}&t={job['token']}&order={order_id}&ot={row['token']}",
                            status_code=303)


# ---------- админка ----------

@app.get("/admin", response_class=HTMLResponse)
def admin(token: str = "", days: int = 7):
    from .admin import render_admin

    s = config.settings
    if not s.admin_token or not token or token != s.admin_token:
        raise HTTPException(404)
    return HTMLResponse(render_admin(days, token))


@app.on_event("startup")
def _startup():
    os.makedirs(config.settings.jobs_dir, exist_ok=True)
    db.connect()
    if config.settings.payment_provider == "mock" and not config.settings.base_url.startswith("http://localhost"):
        log.warning("PAYMENT_PROVIDER=mock на боевом адресе — оплата не настоящая!")


