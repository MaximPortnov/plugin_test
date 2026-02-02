from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from time import perf_counter
from typing import Iterator


class TimerError(RuntimeError):
    """Raised when timer is used in an invalid state."""


@dataclass(frozen=True)
class Lap:
    """Single measurement point."""

    name: str
    delta: float  # seconds since previous mark/start
    total: float  # seconds since timer start


class Timer:
    """
    Лёгкий таймер для e2e: фиксирует время между действиями и итоговое время.

    Пример:
        timer = Timer().start()
        # ... открыть вкладку
        timer.mark("open_tab")
        # ... выполнить SQL
        timer.mark("run_query")
        print(timer.summary())  # [{'name': 'open_tab', 'delta_ms': ..., 'total_ms': ...}, ...]
    """

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> "Timer":
        """Сбрасывает накопленные метки, но не запускает таймер."""
        self._start_at: float | None = None
        self._last_at: float | None = None
        self._laps: list[Lap] = []
        return self

    def start(self) -> "Timer":
        """Запускает отсчёт и очищает старые метки."""
        self._start_at = self._last_at = perf_counter()
        self._laps.clear()
        return self

    def elapsed(self) -> float:
        """Возвращает время с момента start() в секундах."""
        self._ensure_started("elapsed")
        assert self._start_at is not None
        return perf_counter() - self._start_at

    def mark(self, name: str) -> Lap:
        """
        Фиксирует метку: время с последней mark/start и суммарно с начала.
        Подходит для измерения «между действиями».
        """
        self._ensure_started("mark")
        assert self._start_at is not None
        now = perf_counter()
        last = self._last_at or self._start_at
        lap = Lap(name=name, delta=now - last, total=now - self._start_at)
        self._laps.append(lap)
        self._last_at = now
        return lap

    @contextmanager
    def step(self, name: str) -> Iterator[None]:
        """
        Контекстный менеджер для замера блока:
            with timer.step("open_tab"):
                ...действие...
        """
        self._ensure_started("step")
        assert self._start_at is not None
        start = perf_counter()
        try:
            yield
        finally:
            now = perf_counter()
            lap = Lap(name=name, delta=now - start, total=now - self._start_at)
            self._laps.append(lap)
            self._last_at = now

    def stop(self) -> float:
        """Останавливает таймер и возвращает общее время (сек). Метки остаются доступными."""
        total = self.elapsed()
        self._start_at = None
        self._last_at = None
        return total

    def laps(self) -> list[Lap]:
        """Возвращает копию всех меток в порядке добавления."""
        return list(self._laps)

    def summary(self, unit: str = "ms", precision: int = 1) -> list[dict[str, float | str]]:
        """
        Сводка меток (dict) с округлением.
        unit: 'ms' или 's'; precision — количество знаков после запятой.
        """
        factor = 1000 if unit == "ms" else 1
        delta_key = "delta_ms" if unit == "ms" else "delta_s"
        total_key = "total_ms" if unit == "ms" else "total_s"

        return [
            {
                "name": lap.name,
                delta_key: round(lap.delta * factor, precision),
                total_key: round(lap.total * factor, precision),
            }
            for lap in self._laps
        ]


    def _ensure_started(self, method: str) -> None:
        if self._start_at is None:
            raise TimerError(f"Таймер не запущен — вызови start() перед {method}().")

    def __enter__(self) -> "Timer":
        return self.start()

    def __exit__(self, exc_type, exc, tb) -> None:
        self.stop()

def format_summary(summary: list[dict], unit_label: str = None) -> str:
    """
    Удобное представление summary в строках:
    01. step: Δ=10.5ms, Σ=30.9ms
    """
    if not summary:
        return ""

    def _humanize_ms(value_ms: float) -> str:
        """
        Форматирует миллисекунды:
        - <1000 → 123.4ms
        - <60s → 12.3s
        - <60m → 2m 03.4s
        - иначе → 1h 02m 05.4s
        """
        ms = value_ms
        if ms < 1000:
            return f"{ms:.1f}ms"
        sec = ms / 1000
        if sec < 60:
            return f"{sec:.3f}s"
        minutes, seconds = divmod(sec, 60)
        if minutes < 60:
            return f"{int(minutes)}m {seconds:05.2f}s"
        hours, minutes = divmod(minutes, 60)
        return f"{int(hours)}h {int(minutes):02d}m {seconds:05.2f}s"

    # подготовить строки и вычислить ширину колонок
    rows = []
    for lap in summary:
        name = lap.get("name", "")
        # summary по умолчанию в ms; если передан unit_label == "s", пересчитаем
        if unit_label == "s":
            delta_ms = float(lap.get("delta_s", 0)) * 1000
            total_ms = float(lap.get("total_s", 0)) * 1000
        else:
            delta_ms = float(lap.get("delta_ms", 0))
            total_ms = float(lap.get("total_ms", 0))
        rows.append((name, _humanize_ms(delta_ms), _humanize_ms(total_ms)))

    name_width = max(len(r[0]) for r in rows)
    delta_width = max(len(r[1]) for r in rows)
    total_width = max(len(r[2]) for r in rows)

    lines = []
    for idx, (name, delta_str, total_str) in enumerate(rows, start=1):
        lines.append(
            f"{idx:02d}. {name:<{name_width}}  Δ={delta_str:>{delta_width}}  Σ={total_str:>{total_width}}"
        )
    return "\n".join(lines)
