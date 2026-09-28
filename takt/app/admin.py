"""Простая админ-страница: воронка, заказы, выручка, оценки качества, ошибки."""
from __future__ import annotations

import html
import json
import time

from . import db

FUNNEL = [
    ("landing_view", "Открыли сайт"),
    ("upload_start", "Начали загрузку"),
    ("job_created", "Загрузили трек"),
    ("job_done", "Получили варианты"),
    ("preview_play", "Слушали превью"),
    ("checkout_start", "Перешли к оплате"),
    ("payment_success", "Оплатили"),
    ("download", "Скачали"),
]


def _count(name: str, since: float) -> int:
    """Уникальные посетители (устройство, иначе IP) на шаге воронки; пересборки не считаются."""
    return int(db.one("""SELECT COUNT(DISTINCT COALESCE(e.device, j.device, e.ip, j.ip)) c
                         FROM events e LEFT JOIN jobs j ON j.id = e.job_id
                         WHERE e.name=? AND e.ts>? AND j.parent_id IS NULL""", name, since)["c"])


def render_admin(days: int, token: str = "") -> str:
    days = max(1, min(days, 365))
    since = time.time() - days * 86400
    rows = []
    first = None
    for name, label in FUNNEL:
        n = _count(name, since)
        first = first or n or None
        pct = f"{n / first * 100:.1f}%" if first else "—"
        rows.append(f"<tr><td>{label}</td><td class=n>{n}</td><td class=n>{pct}</td></tr>")
    rev = db.one("SELECT COUNT(*) c, COALESCE(SUM(amount),0) s FROM orders WHERE status='paid' AND paid_at>?", since)
    by_product = db.all_("SELECT product, COUNT(*) c, SUM(amount) s FROM orders WHERE status='paid' AND paid_at>? "
                         "GROUP BY product", since)
    repeat = db.one("""SELECT COUNT(*) c FROM (SELECT lower(email) e FROM orders WHERE status='paid' AND email IS NOT NULL
                       GROUP BY lower(email) HAVING COUNT(*) > 1)""")["c"]
    redeems = _count("pack_redeem", since)
    fb = db.all_("SELECT rating, COUNT(*) c FROM feedback WHERE ts>? GROUP BY rating", since)
    fails = db.all_("SELECT error, COUNT(*) c FROM jobs WHERE status='failed' AND created_at>? GROUP BY error "
                    "ORDER BY c DESC LIMIT 10", since)
    perf = db.one("SELECT AVG(finished_at-started_at) a, MAX(finished_at-started_at) m, COUNT(*) c FROM jobs "
                  "WHERE status IN ('done','expired') AND finished_at IS NOT NULL AND created_at>?", since)
    quality = {}
    for r in db.all_("SELECT props FROM events WHERE name='job_done' AND ts>?", since):
        for q in json.loads(r["props"] or "{}").get("quality", "").split(","):
            if q:
                quality[q] = quality.get(q, 0) + 1
    orders = db.all_("SELECT o.*, j.filename, j.target FROM orders o LEFT JOIN jobs j ON j.id=o.job_id "
                     "ORDER BY o.created_at DESC LIMIT 30")
    comments = db.all_("SELECT * FROM feedback WHERE comment IS NOT NULL ORDER BY ts DESC LIMIT 20")
    e = html.escape

    def t(ts):
        return time.strftime("%d.%m %H:%M", time.localtime(ts)) if ts else "—"

    order_rows = "".join(
        f"<tr><td>{t(o['created_at'])}</td><td>{e(o['product'])}</td><td class=n>{o['amount']}</td>"
        f"<td>{e(o['status'])}</td><td>{e((o['filename'] or '')[:40])}</td><td>{e(o['email'] or '')}</td></tr>"
        for o in orders)
    return f"""<!doctype html><meta charset=utf-8><meta name=viewport content="width=device-width,initial-scale=1">
<title>Админка</title>
<style>body{{font:15px/1.45 system-ui,sans-serif;margin:24px;max-width:1000px;color:#1b1530}}
table{{border-collapse:collapse;margin:8px 0 24px;width:100%}}td,th{{border-bottom:1px solid #e5e2ee;padding:6px 8px;
text-align:left}}.n{{text-align:right;font-variant-numeric:tabular-nums}}h2{{margin-top:28px}}
.kpi{{display:flex;gap:16px;flex-wrap:wrap}}.kpi div{{background:#f4f1fb;border-radius:12px;padding:12px 16px}}
.kpi b{{display:block;font-size:24px}}a{{color:#6d28d9}}</style>
<h1>Статистика за {days} дн.</h1>
<p>Период: <a href="?token={e(token)}&days=1">1</a> · <a href="?token={e(token)}&days=7">7</a> ·
<a href="?token={e(token)}&days=30">30</a> · <a href="?token={e(token)}&days=90">90</a> дней</p>
<div class=kpi><div>Оплат<b>{rev['c']}</b></div><div>Выручка, ₽<b>{rev['s']}</b></div>
<div>Использовано кодов пакета<b>{redeems}</b></div><div>Покупателей с 2+ заказами (всё время)<b>{repeat}</b></div>
<div>Обработка, сек (сред/макс)<b>{(perf['a'] or 0):.0f} / {(perf['m'] or 0):.0f}</b></div></div>
<h2>Воронка (уникальные посетители)</h2><table><tr><th>Шаг</th><th class=n>Уникальных</th><th class=n>От первого шага</th></tr>{''.join(rows)}</table>
<h2>Продажи по продуктам</h2><table>{''.join(f"<tr><td>{e(r['product'])}</td><td class=n>{r['c']}</td><td class=n>{r['s']} ₽</td></tr>" for r in by_product) or '<tr><td>Пока нет</td></tr>'}</table>
<h2>Оценки пользователей</h2><table>{''.join(f"<tr><td>{e(r['rating'])}</td><td class=n>{r['c']}</td></tr>" for r in fb) or '<tr><td>Пока нет</td></tr>'}</table>
<h2>Качество склеек (оценка алгоритма, по вариантам)</h2><table>{''.join(f"<tr><td>{e(k)}</td><td class=n>{v}</td></tr>" for k, v in sorted(quality.items())) or '<tr><td>Пока нет</td></tr>'}</table>
<h2>Ошибки обработки</h2><table>{''.join(f"<tr><td>{e(r['error'] or '')}</td><td class=n>{r['c']}</td></tr>" for r in fails) or '<tr><td>Нет</td></tr>'}</table>
<h2>Последние заказы</h2><table><tr><th>Когда</th><th>Продукт</th><th class=n>₽</th><th>Статус</th><th>Трек</th><th>E-mail</th></tr>{order_rows}</table>
<h2>Комментарии</h2><table>{''.join(f"<tr><td>{t(c['ts'])}</td><td>{e(c['rating'])}</td><td>{e(c['comment'])}</td></tr>" for c in comments) or '<tr><td>Пока нет</td></tr>'}</table>
"""
