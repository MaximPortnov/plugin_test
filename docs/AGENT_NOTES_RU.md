# Памятка для LLM-агента — R7 Plugin Tests (RU)

> Основная (английская) версия: `docs/AGENT_NOTES.md`.

## 1. Назначение
- End-to-end сценарии Selenium для плагина OnlyOffice (режимы SQL/OLAP/File и интерфейс SQL Manager).
- Агент должен уметь: подготовить окружение, запустить OnlyOffice с remote debugging, прогнать тесты, помогать расширять Page Object’ы.

## 2. Структура репозитория
- `test/driver.py` — подключение к запущенному Chrome/OnlyOffice через `debuggerAddress=127.0.0.1:9222`; ищет chromedriver в `chromedriver-win64/chromedriver.exe` или `CHROMEDRIVER_PATH`.
- `src/pages/*.py` — Page Object слой: `base_page`, `home_page`, `editor_page`, `plugin_page` (+ `SqlModePage`), `sql_manager_page`.
- `test/my_test.py`, `test/test.ipynb` — пример e2e.
- `src/utils/timer.py` — таймер (`Timer.start()`, `mark()`, `step()`, `summary()`).
- `src/utils/logging_utils.py` — настройка логов (консоль + файл `artifacts/logs/run-<ts>.log`, env `LOG_LEVEL`/`LOG_DIR`).
- `src/utils/visual.py` — `assert_screenshot` (baseline/actual/diff в `artifacts/visual`, env `VISUAL_MODE=update`).
- `src/interaction_log_executor.py` — исполнитель JSONL-логов (`InteractionLogExecutor`) с обработчиками по `event/action` и хуками по `seq`.
- `connections_2026-01-22.json` — тестовые подключения; импортировать вручную в плагин.
- `scripts/` — настройка venv, chromedriver, запуск OnlyOffice, запуск тестов.
- `.vscode/launch.json` — отладка текущего файла в VS Code.

## 3. Подготовка окружения
1) Установите Python 3.12+ (Windows).  
2) `scripts/setup_env.ps1` или `.bat` — создаёт `.venv`, обновляет pip, ставит зависимости из `requirements.txt`.  
3) `scripts/install_chromedriver.ps1`/`.bat` — скачивает нужный chromedriver в `chromedriver-win64/` (совместим с `driver.py`).  
4) Убедитесь, что OnlyOffice Desktop Editors установлены. Если путь иной, передайте `-OnlyOfficePath` (ps1) или установите переменную `ONLYOFFICE_PATH`.

Опционально: вынесите настройки в `.env` в корне репо (используют логирование/визуальные проверки):
```
LOG_LEVEL=INFO
LOG_DIR=artifacts/logs
LOG_ROOT=oo
VISUAL_MODE=update
VISUAL_DIR=artifacts/visual
```

## 4. Запуск OnlyOffice с remote debugging
- `scripts/start_onlyoffice.ps1 -Port 9222` (или `.bat`) запускает DesktopEditors с флагом `--remote-debugging-port`.
- Проверьте, что порт 9222 свободен и процесс жив.

## 5. Импорт тестовых подключений
- В менеджере соединений плагина импортируйте `connections_2026-01-22.json`.  
- Файл предназначен только для ручного использования; реальные креды не коммитим.

## 6. Запуск тестов
PowerShell пример:
```powershell
.\scripts\setup_env.ps1
.\scripts\install_chromedriver.ps1
.\scripts\start_onlyoffice.ps1 -Port 9222
.\scripts\run_tests.ps1
```
Если OnlyOffice уже запущен с нужным портом, запускать повторно не нужно.

Запуск replay без pytest:
```powershell
python -m src.interaction_log_executor --log .\interaction-log-1770560528478.jsonl
```
Полезные флаги:
- `--dry-parse` (только парсинг, без Selenium)
- `--no-prepare` (пропустить стандартные pre-step: открытие ячейки и панели плагина)

## 7. Правила для агента
- Не хранить пароли открыто; файл соединений закодирован, но не зашифрован.
- Локаторы держать в Page Object’ах, а не в тестах.
- Перед запуском убедиться, что версия chromedriver совпадает с встроенным Chromium/OnlyOffice.
- Удалять артефакты вида `plugin.plugin`; исходников плагина в репо нет.
- Жизненный цикл фич: каждую новую фичу сначала описывать в `features/*.md`; в `docs/*` переносить только после реализации и валидации.

## 8. Дальнейшие задачи
- При необходимости метрик используйте `Timer` из `src/utils/timer.py` для замеров вкладок/шагов (`start()` → `mark()/step()` → `summary()`).
- Закрыть TODO в `sql_manager_page.py` (верхняя левая панель, сценарии экспорта/импорта).
- Поддерживать отдельные файлы документации RU/EN.

## 9. Troubleshooting
- `src/interaction_log_executor.py` — исполнитель JSONL-логов в порядке строк файла с fail-fast политикой (первая ошибка останавливает прогон).
- Клавиатурные события (`keydown`, `keyup`, `keypress`) по умолчанию пропускаются.
- В v1 лог не обрезается по последней `seq`-сессии: выполняется весь файл по порядку.
- `SessionNotCreatedException`: почти всегда несовместимая версия chromedriver — переустановите через `install_chromedriver.ps1`.
- Не находятся элементы: убедитесь, что активна нужная вкладка/iframe; используйте `find_element_in_frames`.
- Порт 9222 занят: завершите процесс или запустите на другом порту и передайте `debugger_address` в `DriverOnlyOffice`.
