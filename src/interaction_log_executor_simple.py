"""
Simple interaction log replay for OnlyOffice SQL plugin.

Design goals:
- flat replay loop in file order;
- explicit dict-based routing for known click targets;
- if a target is unknown, fallback to generic click by selector/testId/id.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Callable

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By

from .driver import DriverOnlyOffice
from .interaction_log_executor import (
    InteractionStep,
    find_latest_interaction_log,
    read_interaction_log,
)
from .pages.editor_page import EditorPage
from .pages.home_page import HomePage
from .pages.plugin_page import PluginPage
from .pages.sql_manager_page import SqlManagerPage
from .pages.sql_mode_page import SqlModePage
from .utils.logging_utils import get_logger


class SimpleInteractionLogExecutor:
    """
    Minimal replay executor:
    - for click/activate uses dict routes first;
    - if route is missing, does generic click;
    - keeps only lightweight helpers for inputs/select/codemirror.
    """
    DEFAULT_SKIP_RULES: list[dict[str, Any]] = [
        {
            "event": "input",
            "action": "set-value",
            "testId": "sql-manager-add-query-name",
        },
        {
            "event": "click",
            "action": "activate",
            "testId": "sql-codemirror",
        },
    ]

    def __init__(
        self,
        driver: DriverOnlyOffice | None = None,
        *,
        debugger_address: str = "127.0.0.1:9222",
        home_page: HomePage | None = None,
        editor_page: EditorPage | None = None,
        plugin_page: PluginPage | None = None,
        sql_mode_page: SqlModePage | None = None,
        sql_manager_page: SqlManagerPage | None = None,
    ):
        self.driver = driver or DriverOnlyOffice(debugger_address=debugger_address)
        self.home_page = home_page or HomePage(self.driver)
        self.editor_page = editor_page or EditorPage(self.driver)
        self.plugin_page = plugin_page or PluginPage(self.driver)
        self.sql_mode_page = sql_mode_page or SqlModePage(self.driver)
        self.sql_manager_page = sql_manager_page or SqlManagerPage(self.driver)
        self.logger = get_logger("interaction_log_executor_simple")

        self.preview_timeout = 60
        self.export_timeout = 60
        self.success_timeout = 30

        (
            self.click_routes_exact,
            self.click_routes_prefix,
        ) = self._build_click_routes()
        self.skip_rules: list[dict[str, Any]] = [dict(r) for r in self.DEFAULT_SKIP_RULES]

    # ---------- public API ----------
    def prepare_plugin_home(self) -> None:
        self.home_page.open_creation_cell()
        self.editor_page.click_plugin_button()
        self.editor_page.try_click_close()

    def replay_file(
        self,
        log_path: str | Path,
        *,
        prepare_plugin_home: bool = True,
        stop_on_error: bool = True,
    ) -> None:
        steps = read_interaction_log(log_path)
        if prepare_plugin_home:
            self.prepare_plugin_home()
        self.replay_steps(steps, stop_on_error=stop_on_error)

    def replay_steps(
        self,
        steps: list[InteractionStep],
        *,
        stop_on_error: bool = True,
    ) -> None:
        for step in steps:
            try:
                self.execute_step(step)
            except Exception as exc:
                message = (
                    f"Replay failed on line={step.index}, seq={step.seq}, "
                    f"event={step.event}/{step.action}, testId={step.test_id}"
                )
                if stop_on_error:
                    raise RuntimeError(message) from exc
                self.logger.exception(message)

    def execute_step(self, step: InteractionStep) -> None:
        if self._should_skip_step(step):
            return
        if self._dispatch_by_test_id(step):
            return
        if step.event == "click":
            self._click_generic(step)
            return

        self.logger.debug(
            "Skip line=%s event/action=%s/%s", step.index, step.event, step.action
        )

    def close(self) -> None:
        try:
            self.driver.driver.quit()
        except Exception:
            pass

    def __enter__(self) -> "SimpleInteractionLogExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def set_skip_rules(self, rules: list[dict[str, Any]]) -> None:
        self.skip_rules = [dict(rule) for rule in rules]

    def add_skip_rule(self, **rule: Any) -> None:
        if rule:
            self.skip_rules.append(rule)

    # ---------- routes ----------
    def _build_click_routes(
        self,
    ) -> tuple[
        dict[str, Callable[[InteractionStep], None]],
        dict[str, Callable[[InteractionStep], None]],
    ]:
        exact: dict[str, Callable[[InteractionStep], None]] = {
            "main-sql-mode": lambda _: self.plugin_page.click_main_sql_mode(),
            "main-olap-mode": lambda _: self.plugin_page.click_main_olap_mode(),
            "main-file-mode": lambda _: self.plugin_page.click_main_file_mode(),
            "main-smartdocs": lambda _: self.plugin_page.click_main_smartdocs(),
            "main-connection-manager": lambda _: self.plugin_page.click_main_connection_manager(),
            "main-settings": lambda _: self.plugin_page.click_main_settings(),
            "main-about": lambda _: self.plugin_page.click_main_about(),
            "sql-home-open-sql-manager": lambda _: self.sql_mode_page.click_sql_manager(),
            "sql-home-open-report-manager": lambda _: self.sql_mode_page.click_report_manager(),
            "sql-home-open-query-history": lambda _: self.sql_mode_page.click_query_history(),
            "sql-home-open-log": lambda _: self.sql_mode_page.click_log(),
            "sql-manager-add-query-open": lambda _: self.sql_manager_page.click_add_query_button(),
            "sql-manager-add-query-confirm": lambda _: self.sql_manager_page.confirm_add_query(),
            "sql-manager-add-query-name": lambda step: self._set_query_name_from_step(step),
            "sql-manager-export-confirm": lambda _: self.sql_manager_page.confirm_export(
                timeout=self.export_timeout
            ),
            "sql-manager-export-destination": lambda step: self._set_export_destination_from_step(step),
            "messagebox-button-OK-0": lambda _: self.sql_manager_page.click_success_ok(
                timeout=self.success_timeout
            ),
            "sql-manager-minimize": lambda _: self.sql_manager_page.minimize(),
            "sql-manager-toggle-left-panel": lambda _: self.sql_manager_page.toggle_left_panel_panel(),
        }

        prefix: dict[str, Callable[[InteractionStep], None]] = {
            "cm-tree-connection-": lambda step: (
                self.sql_manager_page.select_connection((step.connection_name or "").strip())
                if (step.connection_name or "").strip()
                else self._click_generic(step)
            ),
            "sql-manager-query-preview-": lambda _step: self.sql_manager_page.click_query_preview(
                timeout=self.preview_timeout
            ),
            "sql-manager-query-export-": lambda _step: self.sql_manager_page.click_export(),
            "sql-manager-query-delete-": lambda _step: self._delete_active_query(),
            "sql-manager-query-editor-": lambda step: self._set_query_text_from_step(step),
            "custom-select-item-sql_manager_export_destination-": lambda step: (
                self.sql_manager_page.select_export_destination(
                    ((step.text or "").strip() or (step.value or "").strip())
                )
                if ((step.text or "").strip() or (step.value or "").strip())
                else self._click_generic(step)
            ),
        }
        return exact, prefix

    def _dispatch_by_test_id(self, step: InteractionStep) -> bool:
        test_id = step.test_id or ""
        if not test_id:
            return False

        exact = self.click_routes_exact.get(test_id)
        if exact:
            exact(step)
            return True

        for prefix, handler in self.click_routes_prefix.items():
            if test_id.startswith(prefix):
                handler(step)
                return True
        return False

    def _should_skip_step(self, step: InteractionStep) -> bool:
        for rule in self.skip_rules:
            if self._rule_matches(step, rule):
                self.logger.debug(
                    "Skip line=%s by rule=%s", step.index, rule
                )
                return True
        return False

    def _rule_matches(self, step: InteractionStep, rule: dict[str, Any]) -> bool:
        for key, expected in rule.items():
            field_key, op = self._parse_rule_key(key)
            actual = self._get_step_field(step, field_key)
            if op == "startswith":
                if actual is None:
                    matched = False
                elif isinstance(expected, (set, tuple, list)):
                    matched = any(
                        str(actual).startswith(str(prefix)) for prefix in expected
                    )
                else:
                    matched = str(actual).startswith(str(expected))
            elif callable(expected):
                try:
                    matched = bool(expected(actual, step))
                except TypeError:
                    matched = bool(expected(actual))
            elif isinstance(expected, (set, tuple, list)):
                matched = actual in expected
            else:
                matched = actual == expected
            if not matched:
                return False
        return True

    @staticmethod
    def _parse_rule_key(key: str) -> tuple[str, str]:
        suffix = "__startswith"
        if key.endswith(suffix):
            return key[: -len(suffix)], "startswith"
        return key, "eq"

    @staticmethod
    def _get_step_field(step: InteractionStep, key: str) -> Any:
        alias = {
            "testId": "test_id",
            "elementId": "element_id",
            "id": "element_id",
            "queryKey": "query_key",
            "connectionName": "connection_name",
        }
        resolved = alias.get(key, key)
        if resolved.startswith("raw."):
            return step.raw.get(resolved.split(".", 1)[1])
        if hasattr(step, resolved):
            return getattr(step, resolved)
        return step.raw.get(key)

    # ---------- generic helpers ----------
    def _set_query_text_from_step(self, step: InteractionStep) -> None:
        if step.value is None:
            raise RuntimeError(
                f"codemirror-change has no value at line={step.index}"
            )
        self.sql_manager_page.set_query_text(step.value)

    def _set_query_name_from_step(self, step: InteractionStep) -> None:
        value = (step.value or "").strip()
        if not value:
            return
        self.sql_manager_page.enter_query_name(value)

    def _set_export_destination_from_step(self, step: InteractionStep) -> None:
        visible_text = ((step.text or "").strip() or (step.value or "").strip())
        if not visible_text:
            return
        self.sql_manager_page.select_export_destination(visible_text)

    def _click_generic(self, step: InteractionStep) -> None:
        locator = self._locator_from_step(step)
        if not locator:
            raise NoSuchElementException(
                f"Cannot build click locator for line={step.index}"
            )
        self.sql_manager_page._click_locator(locator)

    def _delete_active_query(self) -> None:
        self.sql_manager_page.click_query_delete()
        self.sql_manager_page.card = None

    @staticmethod
    def _locator_from_step(step: InteractionStep) -> tuple[str, str] | None:
        if step.selector:
            return By.CSS_SELECTOR, step.selector
        if step.test_id:
            safe = step.test_id.replace("'", "\\'")
            return By.CSS_SELECTOR, f"[data-testid='{safe}']"
        # if step.element_id:
        #     return By.ID, step.element_id
        return None

def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay interaction-log-*.jsonl using simple dict-based routes."
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=None,
        help=(
            "Path to interaction log JSONL. Defaults to latest "
            "interaction-log-*.jsonl in cwd."
        ),
    )
    parser.add_argument(
        "--debugger-address",
        default="127.0.0.1:9222",
        help="OnlyOffice remote debugger address.",
    )
    parser.add_argument(
        "--no-prepare",
        action="store_true",
        help="Do not auto-open cell and plugin home before replay.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_arg_parser()
    args = parser.parse_args(argv)

    log_path = args.log or find_latest_interaction_log()
    if not log_path:
        parser.error(
            "Log path is not provided and no interaction-log-*.jsonl was found in current directory."
        )
    if not log_path.exists():
        parser.error(f"Log file not found: {log_path}")

    executor = SimpleInteractionLogExecutor(debugger_address=args.debugger_address)
    try:
        executor.replay_file(
            log_path=log_path,
            prepare_plugin_home=not args.no_prepare,
            stop_on_error=True,
        )
    except Exception as exc:
        print(f"[replay-simple] failed: {exc}")
        return 2
    finally:
        executor.close()

    print("[replay-simple] completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
