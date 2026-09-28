"""Фоновый обработчик очереди. Запуск: python -m app.worker  (можно несколько процессов)."""
from __future__ import annotations

import json
import logging
import os
import signal
import time
import traceback

from . import config, db, services
from .audio.io import AudioError
from .audio.pipeline import Options, process

log = logging.getLogger("takt.worker")
STALE_AFTER = 15 * 60
_stop = False


def _claim():
    now = time.time()
    # задания, «застрявшие» после падения процесса, возвращаем в очередь (не больше 2 попыток)
    db.run("""UPDATE jobs SET status='queued', stage='В очереди' WHERE status='processing'
              AND started_at < ? AND attempts < 2""", now - STALE_AFTER)
    db.run("""UPDATE jobs SET status='failed', error=? WHERE status='processing' AND started_at < ?
              AND attempts >= 2""", "Не получилось обработать трек. Попробуйте другой файл.", now - STALE_AFTER)
    with db.tx() as c:
        row = c.execute("SELECT id FROM jobs WHERE status='queued' ORDER BY created_at LIMIT 1").fetchone()
        if row is None:
            return None
        c.execute("""UPDATE jobs SET status='processing', started_at=?, attempts=attempts+1, progress=1,
                     stage='Начинаем' WHERE id=?""", (now, row["id"]))
    return db.one("SELECT * FROM jobs WHERE id=?", row["id"])


def handle(job) -> None:
    opts = json.loads(job["options"])
    last = [0.0]

    def progress(p: int, stage: str) -> None:
        if time.time() - last[0] > 0.5 or p >= 100:
            last[0] = time.time()
            db.run("UPDATE jobs SET progress=?, stage=? WHERE id=?", p, stage, job["id"])

    try:
        meta = process(job["source_path"], services.job_dir(job["id"]),
                       Options(target=job["target"], ending=opts.get("ending", "natural"),
                               signal=bool(opts.get("signal")), tempo=float(opts.get("tempo", 1.0))),
                       progress=progress)
    except AudioError as e:
        db.run("UPDATE jobs SET status='failed', error=?, finished_at=? WHERE id=?", str(e), time.time(), job["id"])
        db.event("job_failed", job["id"], reason=str(e)[:120])
        return
    except Exception:
        log.error("job %s crashed:\n%s", job["id"], traceback.format_exc())
        db.run("UPDATE jobs SET status='failed', error=?, finished_at=? WHERE id=?",
               "Что-то пошло не так при обработке. Мы уже смотрим; попробуйте ещё раз или другой файл.",
               time.time(), job["id"])
        db.event("job_failed", job["id"], reason="crash")
        return
    db.run("UPDATE jobs SET status='done', progress=100, stage='Готово', meta=?, finished_at=? WHERE id=?",
           json.dumps(meta, ensure_ascii=False), time.time(), job["id"])
    db.event("job_done", job["id"], elapsed=meta["elapsed"], variants=len(meta["variants"]),
             rubato=meta["rubato"], quality=",".join(v["quality"] for v in meta["variants"]))


def run_forever(poll: float = 0.5) -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    os.makedirs(config.settings.jobs_dir, exist_ok=True)

    def stop(*_):
        global _stop
        _stop = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    # прогреваем модель заранее, чтобы первый пользователь не ждал её загрузку
    try:
        from .audio.analysis import _beat_model

        _beat_model()
    except Exception:
        log.exception("model warmup failed")
    last_cleanup = 0.0
    log.info("worker started")
    while not _stop:
        if time.time() - last_cleanup > 3600:
            try:
                n = services.cleanup()
                if n:
                    log.info("cleanup: expired %d jobs", n)
            except Exception:
                log.exception("cleanup failed")
            last_cleanup = time.time()
        job = _claim()
        if job is None:
            time.sleep(poll)
            continue
        log.info("job %s target=%.1f", job["id"], job["target"])
        handle(job)


def run_once() -> bool:
    """Для тестов: обработать одно задание из очереди."""
    job = _claim()
    if job is None:
        return False
    handle(job)
    return True


if __name__ == "__main__":
    run_forever()
