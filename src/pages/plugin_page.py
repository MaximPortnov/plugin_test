import time
import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage
from .sql_manager_page import SqlManagerPage


class PluginPage(BasePage):
    """Экран плагина с набором режимов/кнопок."""

    SQL_MODE_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='sql-mode']",
    )
    OLAP_MODE_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='olap-mode']",
    )
    FILE_MODE_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='file-mode']",
    )
    SMARTDOCS_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='smartdocs-btn']",
    )
    CONNECTION_MANAGER_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='connection-manager-btn']",
    )
    SETTINGS_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='settings-btn']",
    )
    ABOUT_BUTTON = (
        By.XPATH,
        "//div[@class='mode-buttons']/button[@id='about-page-btn']",
    )
    CLOSE_PLUGIN_BUTTON = (
        By.XPATH,
        "//div[@id='panel-plugins-slider-query']//div[@class='plugin-close close']/button",
    )

    def __init__(self, driver):
        super().__init__(driver, timeout=10)
        # Страница SQL-режима (кнопки на том же экране)
        self.sql_mode = SqlModePage(driver)

    def click_sql_mode(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Структурированные/реляционные данные (SQL,CSV,TXT)
        """
        self._log("click_sql_mode")
        self._js_click_locator(self.SQL_MODE_BUTTON)
        time.sleep(0.1)

    def click_olap_mode(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Аналитические базы данных (OLAP, Внешние сводные таблицы)
        """
        self._js_click_locator(self.OLAP_MODE_BUTTON)

    def click_file_mode(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Неструктурированные (PDF, Word)
        """
        self._js_click_locator(self.FILE_MODE_BUTTON)

    def click_smartdocs(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Документация
        """
        self._js_click_locator(self.SMARTDOCS_BUTTON)

    def click_connection_manager(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Менеджер соединений
        """
        self._js_click_locator(self.CONNECTION_MANAGER_BUTTON)

    def click_settings(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Настройки
        """
        self._js_click_locator(self.SETTINGS_BUTTON)

    def click_about(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        О программе
        """
        self._js_click_locator(self.ABOUT_BUTTON)

    def click_close_plugin(self) -> None:
        """
        Нажимает на кнопку закрытия плагина.
        """
        self._js_click_locator(self.CLOSE_PLUGIN_BUTTON)


class SqlModePage(BasePage):
    """
    Кнопки SQL-режима на том же экране (body_plugin > base_menu).
    """

    MAKE_SQL_BUTTON = (
        By.XPATH,
        "//div[@id='body_plugin']/div[@id='base_menu']/button[@id='make_sql']",
    )
    REPORT_MANAGER_BUTTON = (
        By.XPATH,
        "//div[@id='body_plugin']/div[@id='base_menu']/button[@id='report_manager']",
    )
    HISTORY_QUERY_BUTTON = (
        By.XPATH,
        "//div[@id='body_plugin']/div[@id='base_menu']/button[@id='history_query']",
    )
    SHOW_LOG_BUTTON = (
        By.XPATH,
        "//div[@id='body_plugin']/div[@id='base_menu']/button[@id='show_log']",
    )

    def __init__(self, driver):
        super().__init__(driver, timeout=10)
        self.sql_manager = SqlManagerPage(driver)

    def click_make_sql(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Менеджер SQL
        """
        self._log("click_make_sql")
        self._js_click_locator(self.MAKE_SQL_BUTTON)
        self.sql_manager.wait_connections_ready(timeout=100)
        

    def click_report_manager(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Менеджер отчетов
        """
        self._js_click_locator(self.REPORT_MANAGER_BUTTON)

    def click_history_query(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        История запросов
        """
        self._js_click_locator(self.HISTORY_QUERY_BUTTON)

    def click_show_log(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Журнал
        """
        self._js_click_locator(self.SHOW_LOG_BUTTON)
