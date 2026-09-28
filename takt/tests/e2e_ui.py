"""Сквозной сценарий в настоящем браузере (Chromium через Playwright).

Нужны запущенные сервер (PAYMENT_PROVIDER=mock) и воркер:
    python tests/e2e_ui.py [http://localhost:8000] [папка_для_скриншотов]
"""
from __future__ import annotations

import os
import sys
import tempfile

import soundfile as sf
from playwright.sync_api import expect, sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from conftest import SR, make_song  # noqa: E402

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
SHOTS = sys.argv[2] if len(sys.argv) > 2 else tempfile.mkdtemp()


def launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        return p.chromium.launch(executable_path="/opt/pw-browsers/chromium")


def main() -> None:
    os.makedirs(SHOTS, exist_ok=True)
    song = os.path.join(tempfile.mkdtemp(), "Вальс для теста.wav")
    sf.write(song, make_song(), SR, subtype="PCM_16")
    errors: list[str] = []
    with sync_playwright() as p:
        b = launch(p)
        for width, name in ((1280, "desktop"), (390, "mobile")):
            ctx = b.new_context(viewport={"width": width, "height": 900}, accept_downloads=True)
            page = ctx.new_page()
            page.on("pageerror", lambda e: errors.append(f"{name}: {e}"))
            page.on("console", lambda m: errors.append(f"{name} console: {m.text}") if m.type == "error" and "404" not in m.text else None)
            page.goto(BASE + "/", wait_until="load")
            # ошибка без файла
            page.click("#go")
            expect(page.locator("#formerr")).to_contain_text("выберите файл")
            page.set_input_files("#file", song)
            expect(page.locator("#fname")).to_have_text("Вальс для теста.wav")
            expect(page.locator("#fmeta")).to_contain_text("1:23", timeout=5000)
            page.click('#presets .chip[data-t="1:15"]')
            expect(page.locator("#target")).to_have_value("1:15")
            expect(page.locator("#durhint")).to_contain_text("Сократим")
            page.click("#more summary")
            page.check("#signal", force=True)
            page.click("#go")
            expect(page.locator("#busy")).to_be_visible()
            page.screenshot(path=f"{SHOTS}/{name}_2_busy.png")
            expect(page.locator("#results")).to_be_visible(timeout=240_000)
            variants = page.locator("#variants .variant")
            n = variants.count()
            assert 1 <= n <= 3, n
            page.screenshot(path=f"{SHOTS}/{name}_3_results.png", full_page=False)
            page.locator("#tool").screenshot(path=f"{SHOTS}/{name}_3_tool.png")
            first = variants.nth(0)
            # прослушивание: превью действительно отдаётся
            first.locator(".play").click()
            page.wait_for_timeout(800)
            seam = first.locator(".seamlink")
            if seam.count():
                seam.first.click()
                page.wait_for_timeout(500)
            first.get_by_role("button", name="Выбрать").click()
            expect(first.locator(".checkout")).to_be_visible()
            first.locator('.checkout input[type="email"]').fill("test@example.ru")
            page.locator("#tool").screenshot(path=f"{SHOTS}/{name}_4_checkout.png")
            first.get_by_role("button", name="Оплатить").click()
            page.wait_for_url("**/mock-pay/**")
            page.screenshot(path=f"{SHOTS}/{name}_5_mockpay.png")
            page.click("#mockpay")
            page.wait_for_url("**/?job=**")
            paid = page.locator(".variant.sel")
            expect(paid.locator(".b-paid")).to_be_visible(timeout=30_000)
            with page.expect_download() as dl:
                paid.get_by_role("link", name="Скачать MP3").click()
            d = dl.value
            path = d.path()
            assert os.path.getsize(path) > 500_000, "MP3 слишком маленький"
            assert d.suggested_filename.endswith(".mp3"), d.suggested_filename
            paid.get_by_role("button", name="Готово к выступлению").click()
            expect(paid.get_by_text("Спасибо!")).to_be_visible()
            page.locator("#tool").screenshot(path=f"{SHOTS}/{name}_6_paid.png")
            # бесплатная пересборка
            paid.locator(".rebuild input").fill("1:10")
            paid.get_by_role("button", name="Пересобрать").click()
            expect(page.locator("#busy")).to_be_visible(timeout=15_000)
            expect(page.locator("#results")).to_be_visible(timeout=240_000)
            expect(page.get_by_text("бесплатная пересборка")).to_be_visible()
            page.locator("#variants .variant").nth(0).get_by_role("button", name="Забрать бесплатно").click()
            expect(page.locator(".variant.sel .b-paid")).to_be_visible(timeout=15_000)
            # полная страница для проверки вёрстки
            page.goto(BASE + "/", wait_until="load")
            page.wait_for_timeout(700)
            page.screenshot(path=f"{SHOTS}/{name}_1_landing.png", full_page=True)
            overflow = page.evaluate("() => document.documentElement.scrollWidth > window.innerWidth + 1")
            assert not overflow, f"{name}: горизонтальная прокрутка страницы"
            ctx.close()
        b.close()
    real = [e for e in errors if "Failed to load resource" not in e]
    assert not real, real
    print("E2E OK, скриншоты:", SHOTS)


if __name__ == "__main__":
    main()
