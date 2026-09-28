import re

import httpx
import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def client(app_env):
    from app.main import app

    with TestClient(app) as c:
        yield c


def upload(client, path, target="1:00", **extra):
    with open(path, "rb") as f:
        r = client.post("/api/jobs", files={"file": ("Моя песня.wav", f, "audio/wav")},
                        data={"target": target, **extra}, headers={"X-Device": "dev1"})
    return r


def process_all():
    from app import worker

    n = 0
    while worker.run_once():
        n += 1
    return n


def done_job(client, song_path, target="1:00", **extra):
    r = upload(client, song_path, target, **extra)
    assert r.status_code == 200, r.text
    job = r.json()
    assert process_all() == 1
    st = client.get(f"/api/jobs/{job['id']}", params={"token": job["token"]}).json()
    assert st["status"] == "done", st
    return job, st


def mock_pay(client, order_id, order_token, action="pay"):
    r = client.post(f"/mock-pay/{order_id}", data={"token": order_token, "action": action}, follow_redirects=False)
    assert r.status_code == 303
    return r


def test_pages(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "490" in r.text and "window.TAKT=" in r.text and "{{" not in r.text
    for p in ("/offer", "/privacy", "/robots.txt", "/sitemap.xml", "/healthz", "/static/app.js", "/static/styles.css"):
        assert client.get(p).status_code == 200, p
    assert "{{" not in client.get("/offer").text


def test_full_purchase_flow(client, song_path):
    job, st = done_job(client, song_path, "1:00", signal="1")
    assert 1 <= len(st["variants"]) <= 3
    v = st["variants"][0]
    assert v["duration"] == pytest.approx(62.0, abs=0.01)   # 60 + сигнал 2 с
    assert "downloads" not in v
    prev = client.get(v["preview_url"])
    assert prev.status_code == 200 and prev.headers["content-type"] == "audio/mpeg"
    # чужой токен не работает
    assert client.get(f"/api/jobs/{job['id']}", params={"token": "nope"}).status_code == 404
    # оплата одного трека
    r = client.post(f"/api/jobs/{job['id']}/checkout",
                    json={"token": job["token"], "variant": v["index"], "product": "single", "email": "a@b.ru"})
    assert r.status_code == 200, r.text
    order = r.json()
    assert "/mock-pay/" in order["confirmation_url"]
    st_order = client.get(f"/api/orders/{order['order_id']}", params={"token": order["order_token"]}).json()
    assert st_order["status"] == "pending"
    page = client.get(order["confirmation_url"].replace("http://testserver", ""))
    assert page.status_code == 200 and "Оплатить" in page.text
    mock_pay(client, order["order_id"], order["order_token"])
    st_order = client.get(f"/api/orders/{order['order_id']}", params={"token": order["order_token"]}).json()
    assert st_order["status"] == "paid"
    st = client.get(f"/api/jobs/{job['id']}", params={"token": job["token"]}).json()
    paid = [x for x in st["variants"] if x["index"] == v["index"]][0]
    assert "downloads" in paid
    others = [x for x in st["variants"] if x["index"] != v["index"]]
    assert all("downloads" not in x for x in others)
    mp3 = client.get(paid["downloads"]["mp3"].replace("http://testserver", ""))
    assert mp3.status_code == 200 and mp3.headers["content-type"] == "audio/mpeg"
    assert "filename" in mp3.headers["content-disposition"]
    wav = client.get(paid["downloads"]["wav"].replace("http://testserver", ""))
    assert wav.status_code == 200 and wav.content[:4] == b"RIFF"
    # повторная оплата того же варианта не нужна
    r = client.post(f"/api/jobs/{job['id']}/checkout", json={"token": job["token"], "variant": v["index"]})
    assert r.status_code == 409
    # отзыв
    assert client.post(f"/api/jobs/{job['id']}/feedback",
                       json={"token": job["token"], "variant": 0, "rating": "ready"}).status_code == 200
    # пересборка на другую длительность — бесплатно
    assert st["rebuilds_left"] == 3
    r = client.post(f"/api/jobs/{job['id']}/rebuild", json={"token": job["token"], "target": "0:50"})
    assert r.status_code == 200, r.text
    child = r.json()
    process_all()
    cst = client.get(f"/api/jobs/{child['id']}", params={"token": child["token"]}).json()
    assert cst["status"] == "done" and cst["entitled"]
    assert client.post(f"/api/jobs/{child['id']}/claim", json={"token": child["token"], "variant": 0}).status_code == 200
    # второй вариант той же пересборки бесплатно не отдаём
    idx = [x["index"] for x in cst["variants"]]
    if len(idx) > 1:
        r = client.post(f"/api/jobs/{child['id']}/claim", json={"token": child["token"], "variant": idx[1]})
        assert r.status_code == 400
    cst = client.get(f"/api/jobs/{child['id']}", params={"token": child["token"]}).json()
    assert "downloads" in cst["variants"][0]
    assert cst["rebuilds_left"] == 2


def test_pack_flow(client, song_path):
    job, st = done_job(client, song_path, "0:45")
    r = client.post(f"/api/jobs/{job['id']}/checkout",
                    json={"token": job["token"], "variant": 0, "product": "pack"}).json()
    mock_pay(client, r["order_id"], r["order_token"])
    o = client.get(f"/api/orders/{r['order_id']}", params={"token": r["order_token"]}).json()
    assert o["status"] == "paid" and re.fullmatch(r"TAKT-[A-Z0-9]{4}-[A-Z0-9]{4}", o["pack_code"])
    assert o["pack_remaining"] == 4
    code = o["pack_code"]
    job2, st2 = done_job(client, song_path, "0:40")
    bad = client.post(f"/api/jobs/{job2['id']}/redeem", json={"token": job2["token"], "variant": 0, "code": "TAKT-0000-0000"})
    assert bad.status_code == 400
    ok = client.post(f"/api/jobs/{job2['id']}/redeem", json={"token": job2["token"], "variant": 0, "code": code.lower()})
    assert ok.status_code == 200 and ok.json()["remaining"] == 3
    # повторное применение к тому же варианту не списывает трек
    again = client.post(f"/api/jobs/{job2['id']}/redeem", json={"token": job2["token"], "variant": 0, "code": code})
    assert again.json()["remaining"] == 3
    st2 = client.get(f"/api/jobs/{job2['id']}", params={"token": job2["token"]}).json()
    assert "downloads" in st2["variants"][0]


def test_cancelled_payment(client, song_path):
    job, st = done_job(client, song_path, "0:45")
    r = client.post(f"/api/jobs/{job['id']}/checkout", json={"token": job["token"], "variant": 0}).json()
    mock_pay(client, r["order_id"], r["order_token"], action="cancel")
    o = client.get(f"/api/orders/{r['order_id']}", params={"token": r["order_token"]}).json()
    assert o["status"] == "canceled"
    st = client.get(f"/api/jobs/{job['id']}", params={"token": job["token"]}).json()
    assert all("downloads" not in v for v in st["variants"])


def test_validation_and_limits(client, song_path, tmp_path, monkeypatch):
    assert upload(client, song_path, "abc").status_code == 400
    assert upload(client, song_path, "0:05").status_code == 400
    assert upload(client, song_path, "1:00", tempo="1.5").status_code == 400
    bad = tmp_path / "x.exe"
    bad.write_bytes(b"MZ" * 100)
    with open(bad, "rb") as f:
        r = client.post("/api/jobs", files={"file": ("x.exe", f)}, data={"target": "1:00"})
    assert r.status_code == 400
    fake = tmp_path / "fake.mp3"
    fake.write_bytes(b"\x00" * 5000)
    with open(fake, "rb") as f:
        r = client.post("/api/jobs", files={"file": ("fake.mp3", f)}, data={"target": "1:00"})
    assert r.status_code == 400 and "файл" in r.json()["detail"].lower()
    # лимит бесплатных обработок
    from app import config

    monkeypatch.setenv("FREE_JOBS_PER_HOUR", "2")
    config.reload()
    codes = [upload(client, song_path, "1:00").status_code for _ in range(3)]
    assert codes[-1] == 429


def test_failed_job_message(client, tmp_path):
    import numpy as np
    import soundfile as sf

    silent = tmp_path / "silence.wav"
    sf.write(str(silent), np.zeros((44100 * 20, 2), np.float32), 44100)
    r = upload(client, str(silent), "0:30")
    assert r.status_code == 200
    process_all()
    job = r.json()
    st = client.get(f"/api/jobs/{job['id']}", params={"token": job["token"]}).json()
    assert st["status"] == "failed" and st["error"]


def test_events_and_admin(client):
    assert client.post("/api/events", json={"name": "landing_view", "props": {"ref": "x"}}).status_code == 200
    assert client.post("/api/events", json={"name": "hack"}).status_code == 400
    assert client.get("/admin").status_code == 404
    r = client.get("/admin", params={"token": "secret-admin"})
    assert r.status_code == 200 and "Воронка" in r.text


def test_restore_same_answer(client):
    r1 = client.post("/api/restore", json={"email": "nobody@example.ru"})
    assert r1.status_code == 200 and r1.json() == {"ok": True}
    assert client.post("/api/restore", json={"email": "bad"}).status_code == 400


# ---------- ЮKassa ----------

def test_yookassa_client(monkeypatch, app_env):
    monkeypatch.setenv("YOOKASSA_SHOP_ID", "123")
    monkeypatch.setenv("YOOKASSA_SECRET_KEY", "test_key")
    monkeypatch.setenv("YOOKASSA_SEND_RECEIPT", "1")
    from app import config

    config.reload()
    from app.payments.yookassa import YooKassa

    seen = {}

    def handler(request: httpx.Request):
        if request.method == "POST":
            import json

            seen["body"] = json.loads(request.content)
            seen["idem"] = request.headers.get("Idempotence-Key")
            seen["auth"] = request.headers.get("Authorization")
            return httpx.Response(200, json={"id": "pay_1", "status": "pending",
                                             "confirmation": {"type": "redirect", "confirmation_url": "https://yoomoney.ru/pay/1"}})
        return httpx.Response(200, json={"id": "pay_1", "status": "succeeded"})

    yk = YooKassa(transport=httpx.MockTransport(handler))
    created = yk.create({"id": "ord1", "amount": 490, "email": "a@b.ru"}, "Такт: трек", "https://x/return")
    assert created.payment_id == "pay_1" and created.confirmation_url.startswith("https://yoomoney.ru")
    assert seen["body"]["amount"] == {"value": "490.00", "currency": "RUB"}
    assert seen["body"]["capture"] is True
    assert seen["body"]["receipt"]["customer"]["email"] == "a@b.ru"
    assert seen["body"]["receipt"]["items"][0]["payment_subject"] == "service"
    assert seen["idem"] and seen["auth"].startswith("Basic ")
    assert yk.status("pay_1") == "succeeded"


def test_yookassa_webhook_verifies_via_api(client, song_path, monkeypatch):
    """Уведомление само по себе ничего не открывает: статус перепроверяется у провайдера."""
    job, st = done_job(client, song_path, "0:45")
    r = client.post(f"/api/jobs/{job['id']}/checkout", json={"token": job["token"], "variant": 0}).json()
    from app import db
    from app.payments import mock

    pid = db.one("SELECT provider_payment_id FROM orders WHERE id=?", r["order_id"])["provider_payment_id"]
    # подделка: провайдер говорит «pending» — заказ не оплачивается
    monkeypatch.setattr(mock.MockProvider, "status", lambda self, p: "pending")
    client.post("/api/payments/yookassa", json={"event": "payment.succeeded", "object": {"id": pid, "status": "succeeded"}})
    assert db.one("SELECT status FROM orders WHERE id=?", r["order_id"])["status"] == "pending"
    # провайдер подтверждает — заказ оплачен
    monkeypatch.setattr(mock.MockProvider, "status", lambda self, p: "succeeded")
    client.post("/api/payments/yookassa", json={"event": "payment.succeeded", "object": {"id": pid}})
    assert db.one("SELECT status FROM orders WHERE id=?", r["order_id"])["status"] == "paid"


def test_parse_time():
    from app.main import parse_time

    assert parse_time("1:30") == 90
    assert parse_time("1.30") == 90
    assert parse_time("90") == 90
    assert parse_time("2:15,5") == 135.5


def test_customers_get_higher_limits(client, song_path, monkeypatch):
    from app import config

    job, st = done_job(client, song_path, "0:45")
    r = client.post(f"/api/jobs/{job['id']}/checkout", json={"token": job["token"], "variant": 0}).json()
    mock_pay(client, r["order_id"], r["order_token"])
    monkeypatch.setenv("FREE_JOBS_PER_HOUR", "1")
    config.reload()
    # у покупателя лимит ×8: вторая загрузка за час проходит
    assert upload(client, song_path, "0:50").status_code == 200
