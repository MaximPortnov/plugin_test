# LLM Agent Playbook — R7 Plugin Tests (EN)

> Russian version: see `docs/AGENT_NOTES_RU.md`.

## 1. Purpose
- End-to-end Selenium scenarios for the OnlyOffice plugin (SQL/OLAP/File modes and SQL Manager UI).
- The agent must: prepare the environment, launch OnlyOffice with remote debugging, run tests, and help extend Page Objects.

## 2. Repository map
- `test/driver.py` — attaches to running Chrome/OnlyOffice via `debuggerAddress=127.0.0.1:9222`; finds chromedriver in `chromedriver-win64/chromedriver.exe` or `CHROMEDRIVER_PATH`.
- `src/pages/*.py` — Page Objects: `base_page`, `home_page`, `editor_page`, `plugin_page` (+ `SqlModePage`), `sql_manager_page`.
- `test/my_test.py`, `test/test.ipynb` — sample e2e flow.
- `src/utils/timer.py` — timing helper (`Timer.start()`, `mark()`, `step()`, `summary()`).
- `src/utils/logging_utils.py` — logger setup (console + file `artifacts/logs/run-<ts>.log`, env `LOG_LEVEL`/`LOG_DIR`).
- `src/utils/visual.py` — `assert_screenshot` (visual baseline/actual/diff under `artifacts/visual`, env `VISUAL_MODE=update`).
- `connections_2026-01-22.json` — test connections; import manually in the plugin.
- `scripts/` — setup venv, chromedriver, OnlyOffice, test runner (see below).
- `.vscode/launch.json` — VS Code debug current file.

## 3. Environment setup
1) Install Python 3.12+ (Windows).  
2) `scripts/setup_env.ps1` (or `.bat`) — create `.venv`, upgrade pip, install `requirements.txt`.  
3) `scripts/install_chromedriver.ps1`/`.bat` — download chromedriver to `chromedriver-win64/` (compatible with `driver.py`).  
4) Ensure OnlyOffice Desktop Editors are installed. If the path differs, pass `-OnlyOfficePath` (ps1) or set `ONLYOFFICE_PATH`.

Optional: put settings in `.env` at repo root (used by logging/visual):
```
LOG_LEVEL=INFO
LOG_DIR=artifacts/logs
LOG_ROOT=oo
VISUAL_MODE=update
VISUAL_DIR=artifacts/visual
```

## 4. Launch OnlyOffice with remote debugging
- `scripts/start_onlyoffice.ps1 -Port 9222` (or `.bat`) starts DesktopEditors with `--remote-debugging-port`.
- Verify port 9222 is free and the process stays alive.

## 5. Import test connections
- In the plugin’s connection manager, import `connections_2026-01-22.json`.  
- For manual use only; do not commit real credentials.

## 6. Run tests
PowerShell example:
```powershell
.\scripts\setup_env.ps1
.\scripts\install_chromedriver.ps1           # first time or version change
.\scripts\start_onlyoffice.ps1 -Port 9222    # keep it running
.\scripts\run_tests.ps1                      # runs test/my_test.py via .venv
```
If OnlyOffice is already running on the port, skip step 3.

## 7. Guardrails for LLM
- Do not store plain credentials; `connections_2026-01-22.json` is encoded, not encrypted.
- Keep locators inside Page Objects, not in tests.
- Ensure chromedriver version matches the embedded Chromium/OnlyOffice before running tests.
- Remove artifacts like `plugin.plugin`; plugin source is not in this repo.

## 8. Next steps
- Use `Timer` from `src/utils/timer.py` to log load times for tabs/actions (`start()` → `mark()/step()` → `summary()`).
- Finish TODOs in `sql_manager_page.py` (upper-left panel, extra export/import flows).
- Maintain RU/EN docs in separate files.

## 9. Troubleshooting
- `SessionNotCreatedException`: usually chromedriver version mismatch — reinstall via `install_chromedriver.ps1`.
- Elements not found: check correct tab/iframe; use `find_element_in_frames` from `driver.py`.
- Port 9222 busy: kill conflicting process or run OnlyOffice on another port and pass `debugger_address` to `DriverOnlyOffice`.
