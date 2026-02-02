import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from .base_page import BasePage


class SqlManagerPage(BasePage):
    """
    Страница «Менеджер SQL» (отдельный экран после клика по make_sql).
    Здесь будут локаторы и действия для элементов менеджера.
    """

    def __init__(self, driver):
        super().__init__(driver, timeout=10)

    HIDE_TREE_BTN = (
        By.XPATH,
        "//body/div[@id='text-res']/div/button[@id='btnHideTree']",
    )

    def toggle_tree_panel(self):
        """Кликает кнопку 'скрыть/показать боковую панель'."""
        self._log("toggle_tree_panel")
        self._js_click_locator(self.HIDE_TREE_BTN)

    ADD_QUERY_BTN = (
        By.XPATH,
        "//body/div[@id='text-res']/div/button[@id='btnAddQuery']",
    )
    ADD_QUERY_INPUT = (
        By.XPATH,
        "//input[@id='dialog-menu-name-sqlreq' and @class='dialog-input']",
    )
    ADD_QUERY_CONFIRM = (
        By.XPATH,
        "//button[@id='btn-add-request' and @class='btn btn-primary']",
    )
    ADD_QUERY_CANCEL = (
        By.XPATH,
        "//button[@id='btn-cancel-request' and @class='btn btn-secondary']",
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
        el = self._wait_locator(self.ADD_QUERY_BTN)
        if el:
            self._js_click(el)
        # self._wait_click_locator(self.ADD_QUERY_BTN)

    def enter_query_name(self, query_name: str):
        """Вводит название запроса в поле ввода."""
        self._log("enter_query_name %s", query_name)
        inp = self._find_locator(self.ADD_QUERY_INPUT)
        inp.clear()
        inp.send_keys(query_name)

    def confirm_add_query(self):
        """Подтверждает добавление запроса."""
        self._log("confirm_add_query")
        self._js_click_locator(self.ADD_QUERY_CONFIRM)
        # TODO: [EXTRA] добавить проверку на ошибку создания запроса, уточнить локатор для для ошибки 

    def cancel_add_query(self):
        """Отменяет добавление запроса."""
        self._log("cancel_add_query")
        self._js_click_locator(self.ADD_QUERY_CANCEL)


    QUERY_TYPE_SELECT = (
        By.XPATH,
        "//body/div[@id='text-res']/div/div/select[@id='queryTypeFilter']",
    )

    def select_query_type(self, value: str = "all"):
        """Выбирает тип запросов в фильтре queryTypeFilter (all/htg/connection)."""
        self._log("select_query_type %s", value)
        select_el = self._find_locator(self.QUERY_TYPE_SELECT)
        Select(select_el).select_by_value(value)


    CONNECTION_FILTER_SELECT = (
        By.XPATH,
        "//body/div[@id='text-res']/div/div/select[@id='connectionFilter']",
    )

    def select_connection_filter(self, value: str = "all"):
        """Выбирает соединение в фильтре connectionFilter (all или динамические значения)."""
        self._log("select_connection_filter %s", value)
        select_el = self._find_locator(self.CONNECTION_FILTER_SELECT)
        Select(select_el).select_by_value(value)

    MINIMIZE_BTN = (
        By.XPATH,
        "//body/div[@id='text-res']/div/div/button[@id='btnMinimizeSqlManager']",
    )

    def minimize(self):
        """Сворачивает окно SQL Manager."""
        self._log("minimize_sql_manager")
        self._js_click_locator(self.MINIMIZE_BTN)

    CONNECTION_LIST = (
        By.XPATH,
        "//div[@id='sql_div']/div[@id='left-column']/div[@id='tree-frame']/ul",
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
            list_root = self._find_locator(self.CONNECTION_LIST)
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
        list_root = self._find_locator(self.CONNECTION_LIST)
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
        list_root = self._find_locator(self.CONNECTION_LIST)
        items = list_root.find_elements(*self.CONNECTION_ITEM)
        for li in items:
            title_el = li.find_element(*self.CONNECTION_TITLE)
            if title_el.text.strip() == connection_title:
                li.click()
                time.sleep(1.5)
                return li
        raise NoSuchElementException(f"Connection '{connection_title}' not found")

    # ---------------- Правая колонка: карточки запросов ----------------

    # Правая колонка: список запросов
    QUERIES_CONTAINER = (
        By.XPATH,
        "//div[@id='right-column']/div[@id='queries_container']",
    )
    QUERY_CARD = (
        By.XPATH,
        "//div[@id='right-column']/div[@id='queries_container']/div[contains(@class,'query-card')]",
    )
    QUERY_CARD_HEADER = (By.XPATH, ".//div[contains(@class,'query-card-header')]")
    QUERY_CONN_SELECT = (
        By.XPATH,
        ".//div[@class='query-actions-right']/select[@class='query-connection-selector']",
    )
    QUERY_PREVIEW_BTN = (
        By.XPATH,
        ".//div[@class='query-actions-right']/button[contains(@class,'btn-preview')]",
    )
    PREVIEW_LOADER = (
        By.XPATH,
        "//div[@class='query-preview-container']/div[@class='local-loading-overlay']",
    )
    EXPORT_BTN = (
        By.XPATH,
        "//div[@class='query-preview-footer']/button[@class='query-preview-btn btn-export']",
    )
    EXPORT_CLOSE_BTN = (
        By.XPATH,
        "//div[@class='query-preview-footer']/button[@class='query-preview-btn btn-export-close']",
    )
    EXPORT_DEST_SELECT = (
        By.XPATH,
        "//div[@class='dialog-content']//select[@id='export-destination-select']",
    )
    EXPORT_CONFIRM_BTN = (
        By.XPATH,
        "//div[@class='dialog-content']/div/button[@id='btn-export-confirm']",
    )
    EXPORT_CANCEL_BTN = (
        By.XPATH,
        "//div[@class='dialog-content']/div/button[@id='btn-export-cancel']",
    )
    SUCCESS_TITLE = (
        By.XPATH,
        "//div[@class='message-dialog success-dialog']//h3[@class='message-dialog-title']",
    )
    SUCCESS_TEXT = (
        By.XPATH,
        "//div[@class='message-dialog success-dialog']//div[@class='message-text']",
    )
    SUCCESS_OK_BTN = (
        By.XPATH,
        "//div[@class='message-dialog success-dialog']//div[@class='message-dialog-footer']/button[@class='btn btn-primary']",
    )
    QUERY_DELETE_BTN = (
        By.XPATH,
        ".//div[@class='query-actions-right']/button[contains(@class,'btn-delete')]",
    )
    QUERY_EDITOR_CONTAINER = (
        By.XPATH,
        ".//div[@class='query-card-body']/div[@class='query-editor-container']",
    )

    def find_query_card(
        self, query_name: str | None = None, connection_name: str | None = None
    ):
        """Ищет карточку запроса по data-query-name/connection-name. Возвращает WebElement или None."""
        self._log("find_query_card name=%s conn=%s", query_name, connection_name)
        xpath = self.QUERY_CARD[1]
        if query_name:
            xpath += f"[@data-query-name='{query_name}']"
        if connection_name:
            xpath += f"[@data-connection-name='{connection_name}']"
        try:
            card = self.driver.find_element_in_frames(By.XPATH, xpath)
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
        header = card.find_element(*self.QUERY_CARD_HEADER)
        cls = card.get_attribute("class") or ""
        if "collapsed" in cls:
            header.click()
        return card

    def contract_query_card(
        self, query_name: str | None = None, connection_name: str | None = None
    ) -> WebElement:
        card = self.find_query_card(query_name, connection_name)
        header = card.find_element(*self.QUERY_CARD_HEADER)
        cls = header.get_attribute("class") or ""
        if "expanded" in cls:
            header.click()
        # return card

    def select_query_connection(self, card: WebElement, connection_name: str):
        """
        В карточке запроса выбирает подключение по имени в селекте query-connection-selector.
        """
        self._log("select_query_connection %s", connection_name)
        select_el = card.find_element(*self.QUERY_CONN_SELECT)
        Select(select_el).select_by_visible_text(connection_name)
        return select_el

    def click_query_preview(self, card: WebElement, timeout: int = 10):
        """
        Жмет кнопку предпросмотра в карточке.
        """
        self._log("click_query_preview timeout=%s", timeout)
        btn = card.find_element(*self.QUERY_PREVIEW_BTN)
        self._js_click(btn)
        try:
            WebDriverWait(self.driver.driver, timeout).until_not(
                lambda d: card.find_element(*self.PREVIEW_LOADER)
            )
        except TimeoutException:
            pass
        time.sleep(0.5)
        return btn

    def click_query_delete(self, card: WebElement):
        """
        Жмет кнопку удаления запроса в карточке.
        """
        self._log("click_query_delete")
        btn = card.find_element(*self.QUERY_DELETE_BTN)
        self._js_click(btn)
        return btn

    def set_query_text(self, card: WebElement, text: str):
        """
        Устанавливает текст запроса в CodeMirror внутри карточки через JS.
        """
        self._log("set_query_text")
        editor = card.find_element(*self.QUERY_EDITOR_CONTAINER)
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
    def click_export(self, card: WebElement):
        """Жмет кнопку 'выгрузить в документ' и ждёт исчезновения лоадера."""
        self._log("click_export")
        btn = card.find_element(*self.EXPORT_BTN)
        self._js_click(btn)
        return btn

    def click_export_close(self, card: WebElement):
        """Жмет кнопку 'выгрузить в документ и закрыть' и ждёт исчезновения лоадера."""
        self._log("click_export_close")
        btn = card.find_element(*self.EXPORT_CLOSE_BTN)
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
        # btn = self._click_locator(self.EXPORT_CONFIRM_BTN)
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
