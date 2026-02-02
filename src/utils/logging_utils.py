from __future__ import annotations

import logging
import sys
import os
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime
from pathlib import Path
from time import perf_counter

from .config import env_get, load_dotenv

_hook_installed = False

def setup_logging(
    level: str | None = None,
    log_dir: str | Path | None = None,
    root_name: str | None = None,
    install_excepthook: bool = True,
) -> logging.Logger:
    """
    Инициализирует логгер проекта (консоль + файл) с иерархическими отступами.

    Args:
        level: уровень логирования (строка как в logging). По умолчанию LOG_LEVEL или INFO.
        log_dir: каталог для логов. По умолчанию <repo>/artifacts/logs.
        root_name: корневое имя логгера. По умолчанию LOG_ROOT или 'oo'.
    Returns:
        Logger с именем <root_name>.
    """
    load_dotenv()
    if getattr(setup_logging, "_configured", False):
        return logging.getLogger(root_name or env_get("LOG_ROOT", "oo"))

    level_name = (level or env_get("LOG_LEVEL", "INFO")).upper()
    root = root_name or env_get("LOG_ROOT", "oo")

    base_dir = Path(__file__).resolve().parents[2]
    target_dir = Path(log_dir or env_get("LOG_DIR", base_dir / "artifacts" / "logs"))
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logfile = target_dir / f"run-{timestamp}.log"

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s %(message)s"
    )

    logger = logging.getLogger(root)
    logger.setLevel(level_name)
    logger.propagate = False

    file_handler = logging.FileHandler(logfile, encoding="utf-8")
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    logger.log_file = logfile  # type: ignore[attr-defined]

    setup_logging._configured = True

    if install_excepthook:
        _install_excepthook(logger)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Возвращает дочерний логгер с пространством <root>.<name>.
    """
    root = env_get("LOG_ROOT", "oo")
    setup_logging(root_name=root)
    return logging.getLogger(f"{root}.{name}")




def log_scope(logger: logging.Logger, name: str):
    """Совместимость: возвращает контекст, который просто пишет INFO start/failed."""
    @contextmanager
    def _inner():
        logger.info("%s", name)
        try:
            yield
        except Exception:
            logger.exception("%s failed", name)
            raise
    return _inner()


def _install_excepthook(logger: logging.Logger):
    global _hook_installed
    if _hook_installed:
        return

    orig_hook = sys.excepthook

    def _hook(exc_type, exc, tb):
        try:
            logger.exception("Uncaught exception", exc_info=(exc_type, exc, tb))
        finally:
            orig_hook(exc_type, exc, tb)

    sys.excepthook = _hook
    _hook_installed = True
