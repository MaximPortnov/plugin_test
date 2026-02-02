from __future__ import annotations

import os
from pathlib import Path

_loaded = False


def load_dotenv(path: str | Path | None = None) -> None:
    """
    Минималистичный загрузчик .env.
    - Читает файл .env в корне репо (или переданный path).
    - Не перезаписывает уже выставленные переменные окружения.
    Формат: KEY=VALUE, строки #... игнорируются.
    """
    global _loaded
    if _loaded:
        return

    base_dir = Path(__file__).resolve().parents[2]
    env_path = Path(path) if path else base_dir / ".env"
    if not env_path.exists():
        _loaded = True
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, val = line.split("=", 1)
        key, val = key.strip(), val.strip()
        # убираем кавычки по краям, если есть
        if (val.startswith("'") and val.endswith("'")) or (val.startswith('"') and val.endswith('"')):
            val = val[1:-1]
        if key and key not in os.environ:
            os.environ[key] = val

    _loaded = True


def env_get(key: str, default=None):
    """Читает переменную из окружения (с учётом подгруженного .env)."""
    load_dotenv()
    return os.getenv(key, default)


__all__ = ["load_dotenv", "env_get"]
