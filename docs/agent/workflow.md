# Agent workflow & checklists

## Minimal execution flow
1) **Setup Python env** — `scripts/setup_env.ps1` or `.bat`. Result: `.venv` with Selenium, pytest, ipykernel.
2) **Install chromedriver** — `scripts/install_chromedriver.ps1`/`.bat` (default 143.0.7499.169 to `chromedriver-win64/`). Confirm `chromedriver.exe` exists.
3) **Launch OnlyOffice** — `scripts/start_onlyoffice.ps1 -Port 9222` (or `.bat`). Keep process running; port 9222 must be free.
4) **Import connections** — manually load `connections_2026-01-22.json` via plugin UI (enables SQL tests).
5) **Run tests** — `scripts/run_tests.ps1`/`.bat` (uses `.venv`, points driver to chromedriver, attaches to debugger port).
6) **Run log replay (optional)** — `python -m src.interaction_log_executor --log .\interaction-log-*.jsonl`.

## Preconditions checklist
- Python 3.12+ installed and on PATH.
- OnlyOffice Desktop Editors installed; executable path known (set `ONLYOFFICE_PATH` if non-default).
- Remote debugging port available (default 9222) and not blocked by firewall.
- `chromedriver.exe` matches embedded Chromium version.
- Test data imported (connections file).

## When adjusting or extending tests
- Add locators/methods only in PageObject files under `src/pages/`; keep tests thin.
- For new SQL Manager flows, prefer reusing helpers in `SqlManagerPage`.
- For log-driven flows, use `src/interaction_log_executor.py` and keep manual compensations in `add_before_seq_hook` / `add_after_seq_hook`.
- For metrics, use `Timer` from `src/utils/timer.py` (`start()` → `mark()`/`step()` → `summary()`) inside tests.
- Logging: `setup_logging()` from `src/utils/logging_utils.py` (console + file under `artifacts/logs/`).
- Visual checks: `assert_screenshot` from `src/utils/visual.py` (baseline/actual/diff under `artifacts/visual`, set `VISUAL_MODE=update` to refresh baselines).
- Keep RU/EN documentation synced (EN is canonical).

## Feature lifecycle (features -> docs)
1) Write new feature proposals and scope in `features/*.md`.
2) Implement and validate the feature in code/tests.
3) Move stable runbooks and behavior descriptions into `docs/*`.
4) Keep `features/*.md` as planning/history or mark the item as done.

## CI/automation notes
- On headless/CI Windows runners: ensure DesktopEditors can start; may need virtual display or allow UI session.
- If running on a different port, pass `-Port <port>` to start script and set `debugger_address` in `DriverOnlyOffice` if overridden.

## Clean-up
- Remove temporary artifacts, screenshots, and any regenerated `plugin.plugin` files.
- Do not commit real credentials; keep `connections_2026-01-22.json` as the only shared sample.

## Documentation freshness
- After changing scripts, flows, or locators, update `docs/AGENT_NOTES.md` (EN), `docs/AGENT_NOTES_RU.md` (RU), and related `docs/agent/*` pages in the same PR to keep guidance accurate.
- Do not skip the planning step: new feature ideas must start in `features/*.md` before landing in `docs/*`.
