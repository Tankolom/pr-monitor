from __future__ import annotations

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path


_CONFIGURED = False


def configure_logging(log_dir: str = "data/logs") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    target_dir = Path(os.getenv("MENTION_MONITOR_LOG_DIR") or log_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    log_path = target_dir / "pr-monitor.log"
    formatter = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")

    root = logging.getLogger("mention_monitor")
    root.setLevel(logging.INFO)
    root.propagate = False

    file_handler = RotatingFileHandler(log_path, maxBytes=2_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    root.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root.addHandler(stream_handler)
    _CONFIGURED = True


def get_logger(name: str, log_dir: str = "data/logs") -> logging.Logger:
    configure_logging(log_dir=log_dir)
    return logging.getLogger(f"mention_monitor.{name}")
