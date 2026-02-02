# Visual Regression Proposal (draft)

Цель: фиксировать скриншоты на ключевых шагах e2e, сравнивать с эталоном и сохранять расхождения (actual / baseline / diff) для ручной проверки после прогона.

## Как это может выглядеть

- Хелпер `assert_screenshot(driver, name, region=None, threshold=0.01)`:
  - делает скриншот всей страницы или заданного элемента/region;
  - сравнивает с baseline `artifacts/visual/baseline/{name}.png`;
  - если baseline отсутствует и режим `VISUAL_MODE=update` — сохраняет новый baseline;
  - при отличиях сохраняет:
    - actual: `artifacts/visual/actual/{name}.png`
    - diff (подсветка пикселей): `artifacts/visual/diff/{name}.png`
  - возвращает bool и/или кидает AssertionError с путями к файлам.
- Формат PNG, фиксированный размер окна (например 1280x720) перед тестами для стабильности.
- Сравнение через пер-пиксель + допуск: либо простая метрика (pct различающихся пикселей > threshold), либо SSIM/рогулин (Pillow + numpy/scikit-image). Начнём с Pillow + numpy (без тяжёлых зависимостей).
- Встраивание в тест: после шага `sql_manager.click_export(...)` вызываем `assert_screenshot(driver.driver, "export_dialog")`.
- Результаты логируются в консоль и могут собираться CI как артефакты `artifacts/visual/**`.

## Открытые вопросы (ответь прямо в этом файле или в чате)

1) Где хранить baseline?  
   → В репо: `artifacts/visual/baseline/*.png`. При желании потом вынесем в CI‑артефакты.

2) Нужен ли режим автогенерации baseline (`VISUAL_MODE=update`)?  
   → Да. Режим: при отсутствии файла baseline создаётся/перезаписывается автоматически.

3) Допуск и метрики:  
   - По умолчанию pixel‑diff с порогом 1% отличий (`threshold=0.01`).  
   - Дополнительно есть метод `ssim` (если установлен `scikit-image`): проходит, если SSIM ≥ 0.99 (1 - threshold). Можно переключать `method="ssim"`.

4) Область снимка: на выбор разработчика — полный экран, элемент (`element=`) или регион (`region=(x,y,w,h)`).

5) Маскировка динамики: пока пропускаем. При необходимости позже добавим маски по координатам/селектору.

6) Артефакты: сохраняем локально `artifacts/visual/{baseline,actual,diff}` и подхватываем в CI как артефакты (можно будет прикрутить позже).

7) Разрешение окна: не фиксируем; важно, чтобы baseline и актуальный снимок были одного размера. При несовпадении размеров сравнение падает с подсказкой пересоздать baseline или выровнять окно.

Реализация:
- `src/utils/visual.py` — `assert_screenshot(driver, name, element=None, region=None, method='pixel'|'ssim', threshold=0.01, VISUAL_MODE=update)`.
- `BasePage.screenshot(name, element=None, ...)` и `screenshot_locator(locator, name, ...)` проксируют к `assert_screenshot`.
- Пути: baseline/actual/diff под `artifacts/visual`.
- Настройки можно задать в `.env`: `VISUAL_MODE`, `VISUAL_DIR`, `LOG_LEVEL`, `LOG_DIR`, `LOG_ROOT`.
- Строгость падений: `VISUAL_STRICT=true|false` (по умолчанию true). Если false или передать `raise_on_fail=False` в вызове — тест не упадёт, но сохранит actual/diff.
