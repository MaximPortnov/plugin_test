# AGENTS GUIDE — R7 Plugin Test Project

Primary audience: LLM/automation agents that need to set up, run, or extend the Selenium E2E suite for the OnlyOffice plugin.

## Quick start
1) Read `docs/AGENT_NOTES.md` (EN) or `docs/AGENT_NOTES_RU.md` (RU) for environment + test run steps.
2) Execute scripts from project root (PowerShell or CMD):
   - `scripts/setup_env.ps1` / `.bat` — create `.venv`, install deps.
   - `scripts/install_chromedriver.ps1` / `.bat` — fetch matching chromedriver.
   - `scripts/start_onlyoffice.ps1` / `.bat` — launch OnlyOffice with `--remote-debugging-port=9222`.
   - `scripts/run_tests.ps1` / `.bat` — run `test/my_test.py`.
3) Import `connections_2026-01-22.json` into the plugin manually before SQL tests.

## Repo map (agent-relevant)
- Application code: `src/` (PageObjects `src/pages/*`, utils in `src/utils`, driver in `src/driver.py`).
- Tests/examples: `test/` (`my_test.py`, `test.ipynb`).
- Config/data: `connections_2026-01-22.json`.
- Scripts: `scripts/` (venv, chromedriver, OnlyOffice, runner; .ps1 + .bat twins).
- Agent docs: `docs/AGENT_NOTES.md` (EN), `docs/AGENT_NOTES_RU.md` (RU), `docs/agent/` (deep dives).

## Expectations & guardrails
- Keep locators inside PageObjects; avoid embedding XPaths in tests.
- Verify chromedriver version matches embedded Chromium in OnlyOffice; reinstall if mismatch.
- Do not store real credentials; the provided connections file is for manual import/testing only.
- Avoid recreating deleted artifacts (`plugin.plugin`, plugin source missing in repo).
- **Feature lifecycle:** describe every new feature proposal in `features/*.md` first; move finalized, implemented behavior into `docs/*` only after validation.
- **Documentation hygiene:** whenever flows, scripts, or locators change, immediately update `docs/AGENT_NOTES.md` (EN), `docs/AGENT_NOTES_RU.md` (RU), and any relevant files under `docs/agent/` so instructions stay current.

## Deeper references
- Workflows & checklists: `docs/agent/workflow.md`
- Troubleshooting matrix: `docs/agent/troubleshooting.md`

## Extending
- Implement TODOs in `src/pages/sql_manager_page.py` and add timings in `src/utils/timer.py`.
- Maintain dual-language docs (EN primary, RU secondary with `_RU` suffix).
