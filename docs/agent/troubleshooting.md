# Troubleshooting matrix

## Startup
- **OnlyOffice not found**: set env `ONLYOFFICE_PATH` or edit `scripts/start_onlyoffice.ps1/.bat` to point to `DesktopEditors.exe`.
- **Port 9222 already in use**: choose another port in start script and set the same in `DriverOnlyOffice` (`debuggerAddress`).
- **Chromedriver mismatch / SessionNotCreatedException**: rerun `scripts/install_chromedriver.ps1/.bat` with the correct version; ensure `CHROMEDRIVER_PATH` points to it.

## Test execution
- **Elements not found**: confirm correct iframe context; rely on `find_element_in_frames` via PageObjects, not raw driver calls.
- **Timeouts in SQL Manager**: wait for `wait_connections_ready` before clicking; ensure connections file imported.
- **Export/preview hangs**: increase timeouts in `click_query_preview` / `confirm_export`; check that OnlyOffice window is in foreground (some dialogs may require focus).
- **Replay stops on first failure**: this is expected in v1 (`interaction_log_executor.py` uses fail-fast). Fix the failing step first.
- **Keyboard event line in log**: keyboard events are skipped intentionally (`keydown`, `keyup`, `keypress`).
- **Expected seq-session split but got full replay**: v1 replays full file order and does not auto-cut by latest `seq` session.

## Environment
- **venv missing**: rerun `scripts/setup_env.ps1/.bat`; verify `%REPO_ROOT%\.venv\Scripts\python.exe` exists.
- **pip install fails**: upgrade pip inside venv; check proxy settings if behind corporate network.

## Housekeeping
- Do not restore deleted plugin artifacts (`plugin.plugin`, `plugin/` sources absent).
- Keep docs synchronized (EN primary, RU secondary `_RU`).
