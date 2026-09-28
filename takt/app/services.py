"""Бизнес-логика: задания, оплата, разблокировка, пакеты, пересборка."""
from __future__ import annotations

import json
import os
import secrets
import shutil
import time

from . import config, db, mailer
from .audio.pipeline import fmt_time
from .payments import provider

ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def new_id(n: int = 12) -> str:
    return secrets.token_urlsafe(n)[:n].replace("-", "x").replace("_", "y")


def pack_code() -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(8))
    return f"TAKT-{raw[:4]}-{raw[4:]}"


def job_dir(job_id: str) -> str:
    return os.path.join(config.settings.jobs_dir, job_id)


def check_token(row, token: str | None) -> bool:
    return bool(row) and bool(token) and secrets.compare_digest(row["token"], token)


# ---------- задания ----------

def create_job(*, source_path: str, filename: str, target: float, options: dict, ip: str | None,
               device: str | None, parent_id: str | None = None, entitlement: str | None = None,
               job_id: str | None = None) -> dict:
    job_id = job_id or new_id()
    token = secrets.token_urlsafe(18)
    db.run("""INSERT INTO jobs (id, token, created_at, status, progress, stage, filename, source_path, target,
              options, ip, device, parent_id, entitlement) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
           job_id, token, time.time(), "queued", 0, "В очереди", filename, source_path, target,
           json.dumps(options), ip, device, parent_id, entitlement)
    db.event("job_created", job_id, device, ip, target=target, rebuild=bool(parent_id), **options)
    return {"id": job_id, "token": token}


def jobs_today(ip: str | None, device: str | None, seconds: float) -> int:
    since = time.time() - seconds
    row = db.one("""SELECT COUNT(*) c FROM jobs WHERE created_at > ? AND parent_id IS NULL
                    AND (ip = ? OR (device IS NOT NULL AND device = ?))""", since, ip, device)
    return int(row["c"])


def is_customer(ip: str | None, device: str | None, days: int = 60) -> bool:
    """Покупал ли этот посетитель (устройство или IP) за последние `days` дней — ему лимиты выше."""
    row = db.one("""SELECT 1 FROM unlocks u JOIN jobs j ON j.id = u.job_id
                    WHERE u.created_at > ? AND ((j.device IS NOT NULL AND j.device = ?) OR j.ip = ?) LIMIT 1""",
                 time.time() - days * 86400, device, ip)
    return row is not None


def queue_position(job) -> int:
    row = db.one("SELECT COUNT(*) c FROM jobs WHERE status='queued' AND created_at < ?", job["created_at"])
    return int(row["c"])


def unlocked(job_id: str) -> dict[int, str]:
    return {r["variant"]: r["download_token"] for r in db.all_("SELECT variant, download_token FROM unlocks WHERE job_id=?", job_id)}


def public_job(job) -> dict:
    base = config.settings.base_url
    out = {"id": job["id"], "status": job["status"], "progress": job["progress"], "stage": job["stage"],
           "error": job["error"], "filename": job["filename"], "target": job["target"],
           "options": json.loads(job["options"]), "rebuild": bool(job["parent_id"]),
           "entitled": bool(job["entitlement"])}
    if job["status"] == "queued":
        out["queue"] = queue_position(job)
    if job["status"] == "done" and job["meta"]:
        meta = json.loads(job["meta"])
        opened = unlocked(job["id"])
        vs = []
        for v in meta["variants"]:
            item = {k: v[k] for k in ("index", "kind", "duration", "music_duration", "tempo_change", "seams",
                                      "quality", "peaks", "fade_out")}
            item["preview_url"] = f"/api/jobs/{job['id']}/preview/{v['index']}?token={job['token']}"
            if v["index"] in opened:
                t = opened[v["index"]]
                item["downloads"] = {"mp3": f"{base}/d/{t}/mp3", "wav": f"{base}/d/{t}/wav"}
            vs.append(item)
        out["variants"] = vs
        out["analysis"] = {k: meta[k] for k in ("source_duration", "tempo", "meter", "rubato", "signal", "unit")}
        out["rebuilds_left"] = rebuilds_left(job)
    return out


# ---------- разблокировка ----------

def unlock(job_id: str, variant: int, source: str) -> str:
    token = secrets.token_urlsafe(24)
    with db.tx() as c:
        row = c.execute("SELECT download_token FROM unlocks WHERE job_id=? AND variant=?", (job_id, variant)).fetchone()
        if row:
            return row["download_token"]
        c.execute("INSERT INTO unlocks (job_id, variant, created_at, source, download_token) VALUES (?,?,?,?,?)",
                  (job_id, variant, time.time(), source, token))
    return token


def root_key_for(job) -> str | None:
    """Ключ бесплатных пересборок: «job:<исходное оплаченное задание>». None — трек не оплачен."""
    if job["entitlement"]:
        return job["entitlement"]
    if db.one("SELECT 1 FROM unlocks WHERE job_id=? LIMIT 1", job["id"]):
        return f"job:{job['id']}"
    return None


def rebuilds_left(job) -> int:
    root = root_key_for(job)
    if not root or not root.startswith("job:"):
        return 0
    root_job = root[4:]
    used = db.one("SELECT COUNT(*) c FROM jobs WHERE entitlement=?", root)["c"]
    first = db.one("SELECT MIN(created_at) m FROM unlocks WHERE job_id=?", root_job)["m"]
    if not first or time.time() - first > config.settings.retention_days * 86400:
        return 0
    return max(config.settings.rebuilds_per_order - int(used), 0)


# ---------- заказы ----------

def create_order(job, variant: int, product: str, email: str | None) -> dict:
    s = config.settings
    amount = s.price_pack if product == "pack" else s.price_single
    order = {"id": new_id(14), "token": secrets.token_urlsafe(18), "amount": amount, "email": email,
             "product": product}
    prov = provider()
    db.run("""INSERT INTO orders (id, token, created_at, product, amount, status, job_id, variant, email, provider)
              VALUES (?,?,?,?,?,?,?,?,?,?)""", order["id"], order["token"], time.time(), product, amount,
           "pending", job["id"], variant, email, prov.name)
    if product == "pack":
        desc = f"{s.brand}: пакет из {s.pack_size} треков нужной длины"
    else:
        desc = f"{s.brand}: трек {fmt_time(job['target'])} ({(job['filename'] or 'музыка')[:60]})"
    return_url = f"{s.base_url}/?job={job['id']}&t={job['token']}&order={order['id']}&ot={order['token']}"
    created = prov.create(order, desc, return_url)
    db.run("UPDATE orders SET provider_payment_id=?, confirmation_url=? WHERE id=?",
           created.payment_id, created.confirmation_url, order["id"])
    order["confirmation_url"] = created.confirmation_url
    return order


def refresh_order(order_id: str, force: bool = False) -> dict:
    """Проверяет статус у провайдера (не чаще раза в 3 с) и проводит оплату."""
    order = db.one("SELECT * FROM orders WHERE id=?", order_id)
    if order is None:
        raise KeyError(order_id)
    if order["status"] == "pending" and order["provider_payment_id"] and (
            force or not order["checked_at"] or time.time() - order["checked_at"] > 3):
        db.run("UPDATE orders SET checked_at=? WHERE id=?", time.time(), order_id)
        status = provider().status(order["provider_payment_id"])
        if status == "succeeded":
            mark_paid(order_id)
        elif status == "canceled":
            db.run("UPDATE orders SET status='canceled' WHERE id=? AND status='pending'", order_id)
            db.event("payment_canceled", order["job_id"], order_id=order_id)
        order = db.one("SELECT * FROM orders WHERE id=?", order_id)
    return dict(order)


def mark_paid(order_id: str) -> None:
    s = config.settings
    with db.tx() as c:
        cur = c.execute("UPDATE orders SET status='paid', paid_at=? WHERE id=? AND status='pending'",
                        (time.time(), order_id))
        if cur.rowcount == 0:
            return  # уже проведён
        order = c.execute("SELECT * FROM orders WHERE id=?", (order_id,)).fetchone()
        code = None
        if order["product"] == "pack":
            code = pack_code()
            c.execute("INSERT INTO packs (code, created_at, order_id, total, remaining, email) VALUES (?,?,?,?,?,?)",
                      (code, time.time(), order_id, s.pack_size, s.pack_size - 1, order["email"]))
            c.execute("UPDATE orders SET pack_code=? WHERE id=?", (code, order_id))
    token = unlock(order["job_id"], order["variant"], f"order:{order_id}")
    db.event("payment_success", order["job_id"], order_id=order_id, product=order["product"], amount=order["amount"])
    if order["email"]:
        link = f"{s.base_url}/d/{token}/mp3"
        text = (f"Спасибо за покупку!\n\nВаш трек: {link}\nWAV без сжатия: {s.base_url}/d/{token}/wav\n"
                f"Ссылки действуют {s.retention_days} дней.\n")
        if code:
            text += (f"\nКод пакета: {code}\nОсталось треков: {s.pack_size - 1}. "
                     f"Введите код на странице результата вместо оплаты.\n")
        text += f"\nНужна другая длительность этого же трека? До {s.rebuilds_per_order} пересборок бесплатно — " \
                f"откройте страницу результата.\n\n{s.brand}\n{s.base_url}\n"
        mailer.send(order["email"], f"{s.brand}: ваш трек готов", text)


def redeem(job, variant: int, code: str) -> str:
    code = code.strip().upper()
    with db.tx() as c:
        pack = c.execute("SELECT * FROM packs WHERE code=?", (code,)).fetchone()
        if pack is None:
            raise ValueError("Код не найден. Проверьте, нет ли опечатки.")
        exists = c.execute("SELECT 1 FROM unlocks WHERE job_id=? AND variant=?", (job["id"], variant)).fetchone()
        if not exists:
            if pack["remaining"] <= 0:
                raise ValueError("В этом пакете не осталось треков.")
            c.execute("UPDATE packs SET remaining = remaining - 1 WHERE code=?", (code,))
    token = unlock(job["id"], variant, f"pack:{code}")
    db.event("pack_redeem", job["id"], code=code, variant=variant)
    return token


def claim_rebuild(job, variant: int) -> str:
    if not job["entitlement"]:
        raise ValueError("Этот вариант нужно оплатить.")
    if unlocked(job["id"]):
        raise ValueError("По пересборке можно забрать один вариант.")
    return unlock(job["id"], variant, f"rebuild:{job['entitlement']}")


def pack_remaining(code: str) -> int | None:
    row = db.one("SELECT remaining FROM packs WHERE code=?", code.strip().upper())
    return None if row is None else int(row["remaining"])


# ---------- уборка ----------

def cleanup() -> int:
    """Удаляет файлы старше RETENTION_DAYS. Записи в базе остаются для статистики."""
    cutoff = time.time() - config.settings.retention_days * 86400
    rows = db.all_("SELECT id, source_path FROM jobs WHERE created_at < ? AND status != 'expired'", cutoff)
    for r in rows:
        shutil.rmtree(job_dir(r["id"]), ignore_errors=True)
        db.run("UPDATE jobs SET status='expired', meta=NULL WHERE id=?", r["id"])
    # исходники, на которые больше не ссылается ни одно живое задание
    live = {r["source_path"] for r in db.all_("SELECT source_path FROM jobs WHERE status != 'expired'")}
    src_dir = os.path.join(config.settings.data_dir, "uploads")
    if os.path.isdir(src_dir):
        for name in os.listdir(src_dir):
            p = os.path.join(src_dir, name)
            if p not in live and os.path.getmtime(p) < cutoff:
                os.remove(p)
    return len(rows)
