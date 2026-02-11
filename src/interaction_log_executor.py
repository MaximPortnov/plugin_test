"""
Interaction log replay for OnlyOffice SQL plugin (v1).

This version intentionally keeps logic flat and explicit:
- process log lines in file order;
- fail fast on unexpected errors;
- no session filtering by seq in replay path.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterable

from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import Select

from .driver import DriverOnlyOffice
from .pages.editor_page import EditorPage
from .pages.home_page import HomePage
from .pages.plugin_page import PluginPage
from .pages.sql_manager_page import SqlManagerPage
from .pages.sql_mode_page import SqlModePage
from .utils.logging_utils import get_logger


KEYBOARD_EVENTS = {"keydown", "keyup", "keypress"}


@dataclass(slots=True)
class InteractionStep:
    index: int
    seq: int | None
    page: str | None
    url: str | None
    path: str | None
    event: str
    action: str
    key: str | None
    test_id: str | None
    selector: str | None
    tag: str | None
    element_id: str | None
    name: str | None
    role: str | None
    text: str | None
    value: str | None
    query_key: str | None
    connection_name: str | None
    raw: dict[str, Any]

    @property
    def action_key(self) -> tuple[str, str]:
        return self.event, self.action

    @classmethod
    def from_raw(cls, raw: dict[str, Any], index: int) -> "InteractionStep":
        return cls(
            index=index,
            seq=raw.get("seq"),
            page=raw.get("page"),
            url=raw.get("url"),
            path=raw.get("path"),
            event=(raw.get("event") or "").strip().lower(),
            action=(raw.get("action") or "").strip().lower(),
            key=raw.get("key"),
            test_id=raw.get("testId"),
            selector=raw.get("selector"),
            tag=raw.get("tag"),
            element_id=raw.get("id"),
            name=raw.get("name"),
            role=raw.get("role"),
            text=raw.get("text"),
            value=raw.get("value"),
            query_key=raw.get("queryKey"),
            connection_name=raw.get("connectionName"),
            raw=raw,
        )


@dataclass(slots=True)
class ReplayFailure:
    step: InteractionStep
    error: Exception


def read_interaction_log(log_path: str | Path) -> list[InteractionStep]:
    path = Path(log_path)
    if not path.exists():
        raise FileNotFoundError(f"Interaction log not found: {path}")

    steps: list[InteractionStep] = []
    with path.open("r", encoding="utf-8-sig") as stream:
        for line_number, line in enumerate(stream, start=1):
            payload = line.strip()
            if not payload:
                continue
            try:
                raw = json.loads(payload)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON at {path}:{line_number}") from exc
            if not isinstance(raw, dict):
                raise ValueError(f"JSON line must be an object at {path}:{line_number}")
            steps.append(InteractionStep.from_raw(raw, index=line_number))
    return steps


def split_sessions_by_seq(steps: Iterable[InteractionStep]) -> list[list[InteractionStep]]:
    """
    Utility for analysis/debugging. Replay v1 does not use this split.
    """
    sessions: list[list[InteractionStep]] = []
    current: list[InteractionStep] = []
    last_seq: int | None = None

    for step in steps:
        if current and step.seq is not None and last_seq is not None and step.seq < last_seq:
            sessions.append(current)
            current = []

        current.append(step)
        if step.seq is not None:
            last_seq = step.seq

    if current:
        sessions.append(current)
    return sessions


def find_latest_interaction_log(root: str | Path = ".") -> Path | None:
    base = Path(root)
    candidates = sorted(
        base.glob("interaction-log-*.jsonl"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return candidates[0] if candidates else None


class InteractionLogExecutor:
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
        self.logger = get_logger("interaction_log_executor")

        self.preview_timeout = 60
        self.export_timeout = 60
        self.success_timeout = 30

        self._active_card: WebElement | None = None

        self._handlers: dict[tuple[str, str], Callable[[InteractionStep], None]] = {
            ("click", "activate"): self._handle_click_activate,
            ("click", "preview"): self._handle_click_preview,
            ("click", "export"): self._handle_click_export,
            ("click", "delete"): self._handle_click_delete,
            ("input", "set-value"): self._handle_input_set_value,
            ("change", "set-value"): self._handle_change_set_value,
            ("codemirror-change", "set-value"): self._handle_codemirror_set_value,
        }

        self._exact_click_routes: dict[str, Callable[[], None]] = {
            "main-sql-mode": self.plugin_page.click_main_sql_mode,
            "main-olap-mode": self.plugin_page.click_main_olap_mode,
            "main-file-mode": self.plugin_page.click_main_file_mode,
            "main-smartdocs": self.plugin_page.click_main_smartdocs,
            "main-connection-manager": self.plugin_page.click_main_connection_manager,
            "main-settings": self.plugin_page.click_main_settings,
            "main-about": self.plugin_page.click_main_about,
            "sql-home-open-sql-manager": self.sql_mode_page.click_sql_manager,
            "sql-home-open-report-manager": self.sql_mode_page.click_report_manager,
            "sql-home-open-query-history": self.sql_mode_page.click_query_history,
            "sql-home-open-log": self.sql_mode_page.click_log,
            "sql-manager-add-query-open": self.sql_manager_page.click_add_query_button,
            "sql-manager-add-query-confirm": self.sql_manager_page.confirm_add_query,
            "sql-manager-export-confirm": lambda: self.sql_manager_page.confirm_export(
                timeout=self.export_timeout
            ),
            "messagebox-button-OK-0": lambda: self.sql_manager_page.click_success_ok(
                timeout=self.success_timeout
            ),
            "sql-manager-minimize": self.sql_manager_page.minimize,
            "sql-manager-toggle-left-panel": self.sql_manager_page.toggle_left_panel_panel,
        }

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
        use_last_session: bool = False,
        stop_on_error: bool = True,
    ) -> list[ReplayFailure]:
        steps = read_interaction_log(log_path)

        if use_last_session:
            self.logger.warning(
                "use_last_session is ignored in v1; replay uses full file order"
            )

        if prepare_plugin_home:
            self.prepare_plugin_home()

        return self.replay_steps(steps, stop_on_error=stop_on_error)

    def replay_steps(
        self,
        steps: Iterable[InteractionStep],
        *,
        stop_on_error: bool = True,
    ) -> list[ReplayFailure]:
        failures: list[ReplayFailure] = []

        for step in steps:
            try:
                self.execute_step(step)
            except Exception as exc:
                failure = ReplayFailure(step=step, error=exc)
                failures.append(failure)
                message = (
                    f"Replay failed on line={step.index}, seq={step.seq}, "
                    f"event={step.event}/{step.action}, testId={step.test_id}"
                )
                if stop_on_error:
                    raise RuntimeError(message) from exc
                self.logger.exception(message)

        return failures

    def execute_step(self, step: InteractionStep) -> None:
        handler = self._handlers.get(step.action_key)
        if handler:
            handler(step)
            return
        self._handle_unmapped_action(step)

    def close(self) -> None:
        try:
            self.driver.driver.quit()
        except Exception:
            pass

    def __enter__(self) -> "InteractionLogExecutor":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---------- dispatch handlers ----------
    def _handle_click_activate(self, step: InteractionStep) -> None:
        if self._dispatch_click_route(step):
            self._sync_active_card_from_page()
            return
        if self._is_connection_item(step):
            self._activate_connection(step)
            return
        if self._is_query_delete_button(step):
            self._handle_click_delete(step)
            return
        if self._is_export_destination_option(step):
            self._activate_export_destination_option(step)
            return
        if self._is_codemirror_target(step) and self._activate_codemirror(step):
            return

        self._click_generic(step)
        self._remember_active_card(step)

    def _handle_click_preview(self, step: InteractionStep) -> None:
        self._resolve_card(step, required=True)
        self.sql_manager_page.click_query_preview(timeout=self.preview_timeout)

    def _handle_click_export(self, step: InteractionStep) -> None:
        self._resolve_card(step, required=True)
        self.sql_manager_page.click_export()

    def _handle_click_delete(self, step: InteractionStep) -> None:
        self._resolve_card(step, required=True)
        self.sql_manager_page.click_query_delete()
        self._active_card = None
        self.sql_manager_page.card = None

    def _handle_input_set_value(self, step: InteractionStep) -> None:
        if self._is_query_name_input(step):
            self.sql_manager_page.enter_query_name(step.value or "")
            return
        if self._is_export_destination_select(step):
            self._set_export_destination(step)
            return
        self._set_value_generic(step)

    def _handle_change_set_value(self, step: InteractionStep) -> None:
        if self._is_query_name_input(step):
            self.sql_manager_page.enter_query_name(step.value or "")
            return
        if self._is_export_destination_select(step):
            self._set_export_destination(step)
            return
        self._set_value_generic(step)

    def _handle_codemirror_set_value(self, step: InteractionStep) -> None:
        card = self._resolve_card(step, required=False)
        if card:
            self.sql_manager_page.set_query_text(step.value or "")
            return
        self._set_codemirror_generic(step)

    def _handle_unmapped_action(self, step: InteractionStep) -> None:
        if step.event in KEYBOARD_EVENTS:
            self.logger.debug("Skipping keyboard event at line=%s", step.index)
            return
        if step.event == "click":
            self._click_generic(step)
            self._remember_active_card(step)
            return
        if step.event in {"input", "change"} and step.value is not None:
            self._set_value_generic(step)
            return
        if step.event == "codemirror-change" and step.value is not None:
            self._set_codemirror_generic(step)
            return

        raise RuntimeError(
            f"No handler for line={step.index} event/action={step.event}/{step.action}"
        )

    # ---------- route helpers ----------
    def _dispatch_click_route(self, step: InteractionStep) -> bool:
        test_id = step.test_id
        if not test_id:
            return False

        exact = self._exact_click_routes.get(test_id)
        if exact:
            exact()
            return True

        if test_id.startswith("main-"):
            method_name = f"click_{test_id.replace('-', '_')}"
            if self._call_noarg(self.plugin_page, method_name):
                return True

        if test_id.startswith("sql-home-open-"):
            suffix = test_id[len("sql-home-open-") :]
            method_name = f"click_{suffix.replace('-', '_')}"
            if self._call_noarg(self.sql_mode_page, method_name):
                return True

        return False

    @staticmethod
    def _call_noarg(page_obj: Any, method_name: str) -> bool:
        method = getattr(page_obj, method_name, None)
        if not callable(method):
            return False
        try:
            method()
            return True
        except TypeError:
            return False

    # ---------- action implementations ----------
    def _activate_codemirror(self, step: InteractionStep) -> bool:
        card = self._resolve_card(step, required=False)
        if not card:
            return False

        try:
            editor = self.sql_manager_page._find_child_by_testid(card, "sql-codemirror")
        except Exception:
            try:
                editor = self.sql_manager_page._find_child_by_testid(
                    card, "sql-manager-query-editor"
                )
            except Exception:
                return False

        self.sql_manager_page._js_click(editor)
        self._set_active_card(card)
        return True

    def _sync_active_card_from_page(self) -> None:
        card = getattr(self.sql_manager_page, "card", None)
        if card and self._element_is_alive(card):
            self._active_card = card

    def _set_active_card(self, card: WebElement) -> None:
        self._active_card = card
        self.sql_manager_page.card = card

    def _activate_connection(self, step: InteractionStep) -> None:
        connection_name = (step.connection_name or "").strip()
        if not connection_name:
            connection_name = self._clean_connection_title(step.text)

        if connection_name:
            self.sql_manager_page.select_connection(connection_name)
            return

        self._click_generic(step)

    def _activate_export_destination_option(self, step: InteractionStep) -> None:
        visible_text = self._infer_export_destination_visible_text(step)
        if not visible_text:
            self._click_generic(step)
            return
        self.sql_manager_page.select_export_destination(visible_text)

    def _click_generic(self, step: InteractionStep) -> None:
        locator = self._locator_from_step(step)
        if not locator:
            raise NoSuchElementException(
                f"Cannot build click locator for line={step.index}"
            )
        self.sql_manager_page._click_locator(locator)

    def _set_value_generic(self, step: InteractionStep) -> None:
        element = self._find_element(step)
        if not element:
            raise NoSuchElementException(
                f"Cannot locate input element for line={step.index}"
            )

        value = step.value or ""
        tag = (element.tag_name or "").lower()

        if tag in {"input", "textarea"}:
            element.clear()
            element.send_keys(value)
            return

        if tag == "select":
            self._set_select_value(element, value)
            return

        self.driver.driver.execute_script(
            """
            arguments[0].value = arguments[1];
            arguments[0].dispatchEvent(new Event('input', {bubbles:true}));
            arguments[0].dispatchEvent(new Event('change', {bubbles:true}));
            """,
            element,
            value,
        )

    def _set_codemirror_generic(self, step: InteractionStep) -> None:
        element = self._find_element(step)
        if not element:
            raise NoSuchElementException(
                f"Cannot locate codemirror element for line={step.index}"
            )

        value = step.value or ""
        applied = self.driver.driver.execute_script(
            """
            const host = arguments[0];
            const value = arguments[1];
            const candidates = [
              host,
              host.querySelector ? host.querySelector('.CodeMirror') : null,
              host.closest ? host.closest('.CodeMirror') : null,
            ];

            for (const node of candidates) {
              if (!node) continue;
              if (node.CodeMirror) {
                node.CodeMirror.setValue(value);
                return true;
              }
            }

            const ta = host.querySelector ? host.querySelector('textarea') : null;
            if (ta) {
              ta.value = value;
              ta.dispatchEvent(new Event('input', {bubbles:true}));
              ta.dispatchEvent(new Event('change', {bubbles:true}));
              return true;
            }

            return false;
            """,
            element,
            value,
        )

        if not applied:
            raise RuntimeError(f"Cannot apply codemirror value at line={step.index}")

    def _set_export_destination(self, step: InteractionStep) -> None:
        value = step.value or self._infer_export_destination_value(step.text)
        if not value:
            self._set_value_generic(step)
            return

        element = self._find_element(step)
        if not element:
            element = self.driver.find_element_in_frames(
                By.CSS_SELECTOR,
                "[data-testid='sql-manager-export-destination']",
            )
        if not element:
            raise NoSuchElementException("Export destination select not found")

        self._set_select_value(element, value)

    def _set_select_value(self, element: WebElement, value: str) -> None:
        try:
            Select(element).select_by_value(value)
        except Exception:
            try:
                Select(element).select_by_visible_text(value)
            except Exception:
                self.driver.driver.execute_script(
                    "arguments[0].value = arguments[1];",
                    element,
                    value,
                )

        self.driver.driver.execute_script(
            "arguments[0].dispatchEvent(new Event('change', {bubbles:true}));",
            element,
        )

    # ---------- card helpers ----------
    def _resolve_card(self, step: InteractionStep, *, required: bool) -> WebElement | None:
        page_card = getattr(self.sql_manager_page, "card", None)
        if page_card and self._element_is_alive(page_card):
            self._active_card = page_card
            return page_card

        if self._active_card and self._element_is_alive(self._active_card):
            self.sql_manager_page.card = self._active_card
            return self._active_card

        element = self._find_element(step)
        if element:
            card = self.driver.driver.execute_script(
                "return arguments[0].closest('.query-card');",
                element,
            )
            if card:
                self._set_active_card(card)
                return card

        query_name = (step.raw.get("queryName") or "").strip()
        connection_name = (step.connection_name or "").strip()
        if query_name or connection_name:
            try:
                card = self.sql_manager_page.expand_query_card(
                    query_name=query_name or None,
                    connection_name=connection_name or None,
                )
                if card:
                    self._set_active_card(card)
                    return card
            except Exception:
                pass

        if required:
            raise RuntimeError(f"Cannot resolve active query card for line={step.index}")
        return None

    def _remember_active_card(self, step: InteractionStep) -> None:
        self._sync_active_card_from_page()
        if self._active_card:
            return
        element = self._find_element(step)
        if not element:
            return
        card = self.driver.driver.execute_script(
            "return arguments[0].closest('.query-card');",
            element,
        )
        if card:
            self._set_active_card(card)

    @staticmethod
    def _element_is_alive(element: WebElement) -> bool:
        try:
            _ = element.tag_name
            return True
        except Exception:
            return False

    # ---------- locator helpers ----------
    def _find_element(self, step: InteractionStep) -> WebElement | None:
        locator = self._locator_from_step(step)
        if not locator:
            return None
        by, selector = locator
        return self.driver.find_element_in_frames(by, selector)

    @staticmethod
    def _locator_from_step(step: InteractionStep) -> tuple[str, str] | None:
        if step.selector:
            return By.CSS_SELECTOR, step.selector
        if step.test_id:
            safe = step.test_id.replace("'", "\\'")
            return By.CSS_SELECTOR, f"[data-testid='{safe}']"
        if step.element_id:
            return By.ID, step.element_id
        return None

    # ---------- recognizers ----------
    @staticmethod
    def _is_testid_prefix(step: InteractionStep, prefix: str) -> bool:
        if not step.test_id:
            return False
        return step.test_id == prefix or step.test_id.startswith(prefix + "-")

    def _is_query_name_input(self, step: InteractionStep) -> bool:
        return (
            step.element_id == "dialog-menu-name-sqlreq"
            or self._is_testid_prefix(step, "dialog-menu-name-sqlreq")
            or self._is_testid_prefix(step, "sql-manager-add-query-name")
        )

    def _is_export_destination_select(self, step: InteractionStep) -> bool:
        return (
            step.element_id == "export-destination-select"
            or self._is_testid_prefix(step, "export-destination-select")
            or self._is_testid_prefix(step, "sql-manager-export-destination")
        )

    @staticmethod
    def _is_export_destination_option(step: InteractionStep) -> bool:
        return bool(
            step.test_id
            and step.test_id.startswith("custom-select-item-sql_manager_export_destination-")
        )

    @staticmethod
    def _is_connection_item(step: InteractionStep) -> bool:
        return bool(step.test_id and step.test_id.startswith("cm-tree-connection-"))

    @staticmethod
    def _is_query_delete_button(step: InteractionStep) -> bool:
        return bool(step.test_id and step.test_id.startswith("sql-manager-query-delete-"))

    @staticmethod
    def _is_codemirror_target(step: InteractionStep) -> bool:
        return bool(
            step.test_id
            and (
                step.test_id.startswith("sql-codemirror-")
                or step.test_id.startswith("sql-manager-query-editor-")
            )
        )

    @staticmethod
    def _clean_connection_title(value: str | None) -> str:
        text = (value or "").replace("\u200b", "").strip()
        for prefix in ("▶", "▸", "►"):
            text = text.lstrip(prefix).strip()
        return text

    @staticmethod
    def _infer_export_destination_value(text: str | None) -> str | None:
        normalized = (text or "").lower()
        if "нов" in normalized:
            return "file"
        if "текущ" in normalized:
            return "document"
        if "new" in normalized or "nov" in normalized:
            return "file"
        if "current" in normalized or "tekusch" in normalized:
            return "document"
        return None

    @classmethod
    def _infer_export_destination_visible_text(cls, step: InteractionStep) -> str | None:
        text = (step.text or "").strip()
        if text:
            return text

        test_id = step.test_id or ""
        if test_id.endswith("-file"):
            return "В новый файл"
        if test_id.endswith("-document"):
            return "В текущий документ"

        value = cls._infer_export_destination_value(step.value)
        if value == "file":
            return "В новый файл"
        if value == "document":
            return "В текущий документ"
        return None


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Replay interaction-log-*.jsonl without pytest (v1 fail-fast)."
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
    parser.add_argument(
        "--dry-parse",
        action="store_true",
        help="Only parse log and print summary (does not start Selenium).",
    )

    # Deprecated compatibility flags. They are accepted but ignored in v1.
    parser.add_argument("--all-sessions", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--continue-on-error", action="store_true", help=argparse.SUPPRESS)
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

    steps = read_interaction_log(log_path)
    print(f"[log] file={log_path} lines={len(steps)}")

    if args.dry_parse:
        return 0

    if args.continue_on_error:
        print("[warn] --continue-on-error is ignored in v1; fail-fast is always used")
    if args.all_sessions:
        print("[warn] --all-sessions is ignored in v1; full file order is already used")

    executor = InteractionLogExecutor(debugger_address=args.debugger_address)
    try:
        executor.replay_file(
            log_path=log_path,
            prepare_plugin_home=not args.no_prepare,
            use_last_session=False,
            stop_on_error=True,
        )
    except Exception as exc:
        print(f"[replay] failed: {exc}")
        return 2
    finally:
        executor.close()

    print("[replay] completed successfully")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
