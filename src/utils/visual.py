from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Literal

import numpy as np
from PIL import Image, ImageChops

from .config import env_get, load_dotenv

Method = Literal["pixel", "ssim"]


class VisualMismatch(Exception):
    """Поднимается при несовпадении скриншотов сверх допустимого порога."""


def _shots_root() -> Path:
    load_dotenv()
    base_dir = Path(__file__).resolve().parents[2]
    return Path(env_get("VISUAL_DIR", base_dir / "artifacts" / "visual"))


def _paths(name: str):
    root = _shots_root()
    return {
        "baseline": root / "baseline" / f"{name}.png",
        "actual": root / "actual" / f"{name}.png",
        "diff": root / "diff" / f"{name}.png",
    }


def _ensure_dirs(paths: dict[str, Path]) -> None:
    for p in paths.values():
        p.parent.mkdir(parents=True, exist_ok=True)


def _grab_image(driver, element=None, region=None) -> Image.Image:
    """
    Делает снимок экрана или элемента.
    element: WebElement — снимок только элемента.
    region: (left, top, right, bottom) или (x, y, w, h) для кропа из полного скрина.
    """
    if element is not None:
        png = element.screenshot_as_png
        return Image.open(BytesIO(png)).convert("RGB")

    png = driver.get_screenshot_as_png()
    img = Image.open(BytesIO(png)).convert("RGB")
    if region:
        if len(region) == 4:
            x1, y1, x2, y2 = region
            if region[2] > region[0] and region[3] > region[1]:
                # interpreted as x1,y1,x2,y2 already
                pass
            else:
                x, y, w, h = region
                x1, y1, x2, y2 = x, y, x + w, y + h
        else:
            raise ValueError("region must be (x1,y1,x2,y2) or (x,y,w,h)")
        img = img.crop((x1, y1, x2, y2))
    return img


def _pixel_diff(baseline: Image.Image, current: Image.Image):
    if baseline.size != current.size:
        raise VisualMismatch(
            f"Size mismatch: baseline {baseline.size} vs current {current.size}. "
            "Установите одинаковое окно или пересоздайте baseline (VISUAL_MODE=update)."
        )
    # разница по каналам
    b_arr = np.asarray(baseline, dtype=np.int16)
    c_arr = np.asarray(current, dtype=np.int16)
    diff = np.abs(b_arr - c_arr)
    mask = np.any(diff > 0, axis=2)
    ratio = float(mask.mean())

    # дифф‑картинка: baseline + красная подсветка
    diff_img = baseline.copy()
    # np.asarray может вернуть read-only view; делаем копию, чтобы была доступна запись
    highlight = np.asarray(diff_img).copy()
    highlight[mask] = [255, 0, 0]
    diff_img = Image.fromarray(highlight)
    return ratio, diff_img


def _ssim_score(baseline: Image.Image, current: Image.Image):
    try:
        from skimage.metrics import structural_similarity as ssim  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "Для метода 'ssim' установите scikit-image (pip install scikit-image)."
        ) from exc

    if baseline.size != current.size:
        raise VisualMismatch(
            f"Size mismatch: baseline {baseline.size} vs current {current.size}. "
            "Установите одинаковое окно или пересоздайте baseline (VISUAL_MODE=update)."
        )
    b_arr = np.asarray(baseline.convert("L"))
    c_arr = np.asarray(current.convert("L"))
    score, diff_arr = ssim(b_arr, c_arr, full=True)
    # diff_arr в [0,1]; превратим в heatmap серым
    diff_img = Image.fromarray((diff_arr * 255).astype("uint8")).convert("RGB")
    return score, diff_img


def assert_screenshot(
    driver,
    name: str,
    element=None,
    region=None,
    threshold: float = 0.01,
    method: Method = "pixel",
    update_mode: str | None = None,
    logger=None,
    raise_on_fail: bool = True,
):
    """
    Делает скриншот, сравнивает с baseline и сохраняет actual/diff при расхождениях.

    threshold:
      - pixel: доля отличающихся пикселей (0.01 = 1%)
      - ssim: допускаем ухудшение до (1 - threshold), т.е. 0.01 => SSIM >= 0.99
    method: 'pixel' (по умолчанию) или 'ssim' (требует scikit-image).
    update_mode: VISUAL_MODE env или аргумент: 'update' — перезаписывает baseline.
    """
    paths = _paths(name)
    _ensure_dirs(paths)
    load_dotenv()
    mode = (update_mode or env_get("VISUAL_MODE", "")).lower()
    strict_env = (env_get("VISUAL_STRICT", "true") or "").lower()
    strict = strict_env in ("1", "true", "yes", "on")
    effective_raise = raise_on_fail and strict

    current = _grab_image(driver, element=element, region=region)
    baseline_path = paths["baseline"]

    if not baseline_path.exists() or mode == "refresh":
        if mode in ("update", "refresh"):
            current.save(baseline_path)
            if logger:
                logger.info(
                    "Baseline %s: %s",
                    "refreshed" if baseline_path.exists() else "created",
                    baseline_path,
                )
            return True
        msg = f"Baseline not found for '{name}'. Run with VISUAL_MODE=update/refresh to create."
        if logger:
            logger.error(msg)
        if effective_raise:
            raise VisualMismatch(msg)
        return False

    baseline = Image.open(baseline_path).convert("RGB")

    if method == "pixel":
        metric, diff_img = _pixel_diff(baseline, current)
        passed = metric <= threshold
        detail = f"diff_ratio={metric:.4f} (threshold {threshold})"
    elif method == "ssim":
        metric, diff_img = _ssim_score(baseline, current)
        passed = metric >= (1 - threshold)
        detail = f"ssim={metric:.4f} (min {1 - threshold:.4f})"
    else:
        raise ValueError("method must be 'pixel' or 'ssim'")

    if passed:
        if logger:
            logger.info("Screenshot ok: %s (%s)", name, detail)
        return True

    # сохраняем actual и diff
    current.save(paths["actual"])
    diff_img.save(paths["diff"])
    msg = (
        f"Visual mismatch for '{name}': {detail}. "
        f"baseline={paths['baseline']}, actual={paths['actual']}, diff={paths['diff']}"
    )
    if logger:
        logger.warning(msg)
    if effective_raise:
        raise VisualMismatch(msg)
    return False


__all__ = [
    "assert_screenshot",
    "VisualMismatch",
]
