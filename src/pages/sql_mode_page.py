import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException

from .sql_manager_page import SqlManagerPage
from .base_page import BasePage


class SqlModePage(BasePage):
    """
    Кнопки SQL-режима на том же экране (body_plugin > base_menu).
    """

    SQL_MANAGER_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-home-open-sql-manager']",
    )
    REPORT_MANAGER_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-home-open-report-manager']",
    )
    QUERY_HISTORY_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-home-open-query-history']",
    )
    LOG_BUTTON = (
        By.XPATH,
        "//button[@data-testid='sql-home-open-log']",
    )

    def __init__(self, driver):
        super().__init__(driver, timeout=10)
        self.sql_manager = SqlManagerPage(driver)

    def click_sql_manager(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Менеджер SQL
        """
        self._log("click_make_sql")
        self._js_click_locator(self.SQL_MANAGER_BUTTON)
        self.sql_manager.wait_connections_ready(timeout=40)

    def click_report_manager(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Менеджер отчетов
        """
        self._js_click_locator(self.REPORT_MANAGER_BUTTON)

    def click_query_history(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        История запросов
        """
        self._js_click_locator(self.QUERY_HISTORY_BUTTON)

    def click_log(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Журнал
        """
        self._js_click_locator(self.LOG_BUTTON)
