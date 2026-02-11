import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from typing import Optional
from .base_page import BasePage


class SqlManagerPage(BasePage):
    """
    Страница «Менеджер SQL» (отдельный экран после клика по make_sql).
    Здесь будут локаторы и действия для элементов менеджера.
    """

    def __init__(self, driver):
        super().__init__(driver, timeout=10)
        self.query_name = None
        self.card = None

    TOGGLE_LEFT_PANEL_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-manager-toggle-left-panel']"
    )

    def toggle_left_panel_panel(self):
        """Кликает кнопку 'скрыть/показать боковую панель'."""
        self._log("toggle_tree_panel")
        self._js_click_locator(self.TOGGLE_LEFT_PANEL_BUTTON)

    ADD_QUERY_OPEN_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-manager-add-query-open']"
    )
    ADD_QUERY_NAME_INPUT = (
        By.CSS_SELECTOR,
        "input[data-testid='sql-manager-add-query-name']"
    )
    ADD_QUERY_CONFIRM_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-manager-add-query-confirm']"
    )
    ADD_QUERY_CANCEL_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-manager-add-query-cancel']"
    )

    def add_query(self, query_name: str):
        """
        Нажимает 'Добавить запрос', вводит имя и подтверждает.
        Требует, чтобы предварительно было выбрано соединение (кнопка разблокирована).
        """
        self._log("add_query %s", query_name)
        self.click_add_query_button()
        self.enter_query_name(query_name)
        self.confirm_add_query()

    def click_add_query_button(self):
        """Кликает по кнопке 'Добавить запрос'."""
        self._log("click_add_query_button")
        el = self._wait_locator(self.ADD_QUERY_OPEN_BUTTON)
        if el:
            self._js_click(el)
        # self._wait_click_locator(self.ADD_QUERY_BTN)

    def enter_query_name(self, query_name: str):
        """Вводит название запроса в поле ввода."""
        self._log("enter_query_name %s", query_name)
        inp = self._find_locator(self.ADD_QUERY_NAME_INPUT)
        inp.clear()
        inp.send_keys(query_name)
        self.query_name = query_name

    def confirm_add_query(self):
        """Подтверждает добавление запроса."""
        self._log("confirm_add_query")
        self._js_click_locator(self.ADD_QUERY_CONFIRM_BUTTON)
        self.expand_query_card(self.query_name)
        # TODO: [EXTRA] добавить проверку на ошибку создания запроса, уточнить локатор для для ошибки 

    def cancel_add_query(self):
        """Отменяет добавление запроса."""
        self._log("cancel_add_query")
        self._js_click_locator(self.ADD_QUERY_CANCEL_BUTTON)


    FILTER_TYPE_SELECT = (
        By.XPATH,
        "//select[@data-testid='sql-manager-filter-type']"
    )

    def select_query_type(self, value: str = "all"):
        """Выбирает тип запросов в фильтре queryTypeFilter (all/htg/connection)."""
        self._log("select_query_type %s", value)
        select_el = self._find_locator(self.FILTER_TYPE_SELECT)
        Select(select_el).select_by_value(value)


    FILTER_CONNECTION_SELECT = (
        By.XPATH,
        "//select[@data-testid='sql-manager-filter-connection']"
    )

    def select_connection_filter(self, value: str = "all"):
        """Выбирает соединение в фильтре connectionFilter (all или динамические значения)."""
        self._log("select_connection_filter %s", value)
        select_el = self._find_locator(self.FILTER_CONNECTION_SELECT)
        Select(select_el).select_by_value(value)

    MINIMIZE_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-manager-minimize']"
    )

    def minimize(self):
        """Сворачивает окно SQL Manager."""
        self._log("minimize_sql_manager")
        self._js_click_locator(self.MINIMIZE_BUTTON)

    CONNECTION_LIST_UL = (
        By.XPATH,
        "//ul[@data-testid='cm-tree-connections-list']"
    )
    CONNECTION_ITEM = (By.XPATH, ".//li[contains(@class,'connection-item')]")
    CONNECTION_TITLE = (By.XPATH, ".//span[contains(@class,'connection-title')]")
    CONNECTION_ARROW = (By.XPATH, ".//span[contains(@class,'expand-arrow')]")

    def wait_connections_ready(self, timeout: int = 10) -> bool:
        """
        Ждет, пока все элементы списка соединений станут либо connection-success, либо connection-error.
        Возвращает True при успехе, бросает TimeoutException при превышении таймаута.
        """
        self._log("wait_connections_ready timeout=%s", timeout)

        def _all_success(_):
            list_root = self._find_locator(self.CONNECTION_LIST_UL)
            items = list_root.find_elements(*self.CONNECTION_ITEM)
            if not items:
                return False
            for li in items:
                cls = li.get_attribute("class") or ""
                if "connection-item" not in cls:
                    return False
                if "connection-success" not in cls and "connection-error" not in cls:
                    return False
            return True

        try:
            WebDriverWait(self.driver.driver, timeout).until(_all_success)
            return True
        except TimeoutException:
            raise TimeoutException(
                f"Не все соединения стали connection-success за {timeout}с"
            )

    def expand_connection(self, connection_title: str):
        """Кликает по стрелке expand у соединения с указанным заголовком."""
        self._log("expand_connection %s", connection_title)
        list_root = self._find_locator(self.CONNECTION_LIST_UL)
        items = list_root.find_elements(*self.CONNECTION_ITEM)
        for li in items:
            title_el = li.find_element(*self.CONNECTION_TITLE)
            if title_el.text.strip() == connection_title:
                try:
                    arrow = li.find_element(*self.CONNECTION_ARROW)
                    arrow.click()
                except Exception:
                    pass
                return li
        raise NoSuchElementException(f"Connection '{connection_title}' not found")

    def select_connection(self, connection_title: str):
        """Выбирает соединение (клик по элементу), разблокируя кнопку создания запроса."""
        self._log("select_connection %s", connection_title)
        list_root = self._find_locator(self.CONNECTION_LIST_UL)
        items = list_root.find_elements(*self.CONNECTION_ITEM)
        for li in items:
            title_el = li.find_element(*self.CONNECTION_TITLE)
            if title_el.text.strip() == connection_title:
                li.click()
                time.sleep(1.5)
                return li
        raise NoSuchElementException(f"Connection '{connection_title}' not found")

    # ---------------- Правая колонка: карточки запросов ----------------

    # Правая колонка: список запросов (через data-testid)
    QUERIES_CONTAINER = (
        By.CSS_SELECTOR,
        "[data-testid='sql-manager-queries-container']",
    )
    QUERY_CARD = (
        By.CSS_SELECTOR,
        "div.query-card",  # у каждой карточки есть data-query-name и data-query-key
    )
    PREVIEW_LOADER = (
        By.CSS_SELECTOR,
        "[data-testid^='sql-manager-query-preview-container-'] .local-loading-overlay",
    )
    EXPORT_DEST_SELECT = (
        By.CSS_SELECTOR,
        "[data-testid='sql-manager-export-destination']",
    )
    EXPORT_CONFIRM_BTN = (
        By.CSS_SELECTOR,
        "[data-testid='sql-manager-export-confirm']",
    )
    EXPORT_CANCEL_BTN = (
        By.CSS_SELECTOR,
        "[data-testid='sql-manager-export-cancel']",
    )
    SUCCESS_TITLE = (
        By.CSS_SELECTOR,
        "[data-testid='messagebox-title']",
    )
    SUCCESS_TEXT = (
        By.CSS_SELECTOR,
        "[data-testid='messagebox-body']",
    )
    SUCCESS_OK_BTN = (
        By.CSS_SELECTOR,
        "[data-testid='messagebox-button-OK-0']",
    )
    QUERY_EDITOR_CONTAINER = (
        By.CSS_SELECTOR,
        "[data-testid^='sql-manager-query-editor-']",
    )

    def find_query_card(
        self, query_name: str | None = None, connection_name: str | None = None
    ):
        """Ищет карточку запроса по data-query-name/connection-name. Возвращает WebElement или None."""
        self._log("find_query_card name=%s conn=%s", query_name, connection_name)
        css = self.QUERY_CARD[1]
        if query_name:
            css += f"[data-query-name='{query_name}']"
        if connection_name:
            css += f"[data-connection-name='{connection_name}']"
        try:
            card = self.driver.find_element_in_frames(By.CSS_SELECTOR, css)
            return card
        except Exception:
            raise NoSuchElementException(
                f"Query card '{query_name}'/'{connection_name}' не найдена"
            )

    def expand_query_card(
        self, query_name: str | None = None, connection_name: str | None = None
    ) -> WebElement:
        """Ищет карточку, раскрывает если collapsed, возвращает элемент."""
        self._log("expand_query_card name=%s conn=%s", query_name, connection_name)
        card = self.find_query_card(query_name, connection_name)
        header = self._find_child_by_testid(card, "sql-manager-query-card-header")
        if not header:
            header = card
        cls = card.get_attribute("class") or ""
        if "collapsed" in cls:
            header.click()
        self.card = card
        return card

    def contract_query_card(
        self, query_name: str | None = None, connection_name: str | None = None
    ) -> WebElement:
        card = self.find_query_card(query_name, connection_name)
        header = card.find_element(*self.QUERY_CARD_HEADER)
        cls = header.get_attribute("class") or ""
        if "expanded" in cls:
            header.click()
        self.card = None
        # return card

    def select_query_connection(self, connection_name: str):
        """
        В карточке запроса выбирает подключение по имени в селекте query-connection-selector.
        """
        self._log("select_query_connection %s", connection_name)
        select_el = self._find_child_by_testid(self.card, "sql-manager-query-connection-select")
        Select(select_el).select_by_visible_text(connection_name)
        return select_el

    def click_query_preview(self, timeout: int = 10):
        """
        Жмет кнопку предпросмотра в карточке.
        """
        self._log("click_query_preview timeout=%s", timeout)
        btn = self._find_child_by_testid(self.card, "sql-manager-query-preview")
        self._js_click(btn)
        try:
            WebDriverWait(self.driver.driver, timeout).until_not(
                lambda d: self.card.find_element(*self.PREVIEW_LOADER)
            )
        except TimeoutException:
            pass
        time.sleep(0.5)
        return btn

    def click_query_delete(self):
        """
        Жмет кнопку удаления запроса в карточке.
        """
        self._log("click_query_delete")
        btn = self._find_child_by_testid(self.card, "sql-manager-query-delete")
        self._js_click(btn)
        return btn

    def set_query_text(self, text: str):
        """
        Устанавливает текст запроса в CodeMirror внутри карточки через JS.
        """
        self._log("set_query_text")
        editor = self._find_child_by_testid(self.card, "sql-manager-query-editor")
        # Пытаемся использовать CodeMirror API, если он есть
        self.driver.driver.execute_script(
            """
            const container = arguments[0];
            const cmHost = container.querySelector('.CodeMirror');
            if (cmHost && cmHost.CodeMirror) {
                cmHost.CodeMirror.setValue(arguments[1]);
                return true;
            }
            const ta = container.querySelector('textarea');
            if (ta) {
                ta.value = arguments[1];
                ta.dispatchEvent(new Event('input', {bubbles:true}));
                return true;
            }
            return false;
            """,
            editor,
            text,
        )
        time.sleep(0.5)
        return editor

    # -------- Экспорт предпросмотра ----------
    def click_export(self):
        """Жмет кнопку 'выгрузить в документ' и ждёт исчезновения лоадера."""
        self._log("click_export")
        btn = self._find_child_by_testid(self.card, "sql-manager-query-export")
        self._js_click(btn)
        return btn

    def click_export_close(self ):
        """Жмет кнопку 'выгрузить в документ и закрыть' и ждёт исчезновения лоадера."""
        self._log("click_export_close")
        btn = self._find_child_by_testid(self.card, "sql-manager-query-export-close")
        self._js_click(btn)
        return btn

    def select_export_destination(self, visible_text: str):
        """Выбирает пункт в селекте назначения выгрузки (например 'В текущий документ' или 'В новый файл')."""
        self._log("select_export_destination %s", visible_text)
        sel = self._find_locator(self.EXPORT_DEST_SELECT)
        Select(sel).select_by_visible_text(visible_text)
        return sel

    def confirm_export(self, timeout: int = 10):
        """
        Жмет кнопку 'Выгрузить', ждёт исчезновения лоадера предпросмотра,
        возвращает (title, text) из success-диалога.
        """
        self._log("confirm_export timeout=%s", timeout)
        btn = self._find_locator(self.EXPORT_CONFIRM_BTN)
        ActionChains(self.driver.driver).move_to_element(btn).click().perform()
        # ждём появления лоадера
        try:
            WebDriverWait(self.driver.driver, timeout).until(
                lambda d: self.driver.find_element_in_frames(*self.PREVIEW_LOADER)
            )
        except TimeoutException:
            pass
        # ждём исчезновения лоадера
        try:
            WebDriverWait(self.driver.driver, timeout).until_not(
                lambda d: self.driver.find_element_in_frames(*self.PREVIEW_LOADER)
            )
        except TimeoutException:
            pass
        return btn

    def cancel_export(self):
        """Жмет кнопку отмены в диалоге выгрузки."""
        self._log("cancel_export")
        return self._js_click_locator(self.EXPORT_CANCEL_BTN)

    def read_success_message(self):
        """Читает заголовок и текст из success-диалога выгрузки."""
        self._log("read_success_message")
        title_el = self._find_locator(self.SUCCESS_TITLE)
        text_el = self._find_locator(self.SUCCESS_TEXT)
        return title_el.text.strip(), text_el.text.strip()

    def click_success_ok(self, timeout: int = 5):
        """Жмет 'ОК' в success-диалоге, можно задать timeout ожидания появления кнопки."""
        self._log("click_success_ok timeout=%s", timeout)
        btn = self._wait_find_locator(self.SUCCESS_OK_BTN, timeout=timeout)
        if btn:
            self._js_click(btn)
        return btn

    # ---------- helpers ---------
    def _query_suffix(self, card: WebElement) -> Optional[str]:
        key = card.get_attribute("data-query-key") or card.get_attribute("data-query-name")
        if not key:
            return None
        return key.replace("-", "_")

    def _find_child_by_testid(self, card: WebElement, prefix: str) -> WebElement:
        """
        Ищет элемент внутри карточки по data-testid, который начинается с prefix и содержит query-key.
        """
        suffix = self._query_suffix(card)
        candidates = []
        if suffix:
            candidates.append(f"[data-testid='{prefix}-{suffix}']")
            candidates.append(f"[data-testid^='{prefix}-{suffix}']")
        candidates.append(f"[data-testid^='{prefix}-']")
        for css in candidates:
            try:
                el = card.find_element(By.CSS_SELECTOR, css)
                if el:
                    return el
            except Exception:
                continue
        # fallback: search in descendants globally
        return self.driver.find_element_in_frames(By.CSS_SELECTOR, candidates[-1])
