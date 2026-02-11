import time
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
from .base_page import BasePage
from .sql_manager_page import SqlManagerPage


class PluginPage(BasePage):
    """Экран плагина с набором режимов/кнопок."""

    MAIN_SQL_MODE_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-sql-mode']",
    )
    MAIN_OLAP_MODE_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-olap-mode']",
    )
    MAIN_FILE_MODE_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-file-mode']",
    )
    MAIN_SMARTDOCS_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-smartdocs']",
    )
    MAIN_CONNECTION_MANAGER_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-connection-manager']",
    )
    MAIN_SETTINGS_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-settings']",
    )
    MAIN_ABOUT_BUTTON = (
        By.XPATH,
        "//button[@data-testid='main-about']",
    )
    CLOSE_PLUGIN_BUTTON = (
        By.XPATH,
        "//div[@id='panel-plugins-slider-query']//div[@class='plugin-close close']/button",
    )

    def __init__(self, driver):
        super().__init__(driver, timeout=10)

    def click_main_sql_mode(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Структурированные/реляционные данные (SQL,CSV,TXT)
        """
        self._log("click_sql_mode")
        self._js_click_locator(self.MAIN_SQL_MODE_BUTTON)
        time.sleep(0.1)

    def click_main_olap_mode(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Аналитические базы данных (OLAP, Внешние сводные таблицы)
        """
        self._js_click_locator(self.MAIN_OLAP_MODE_BUTTON)

    def click_main_file_mode(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Неструктурированные (PDF, Word)
        """
        self._js_click_locator(self.MAIN_FILE_MODE_BUTTON)

    def click_main_smartdocs(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Документация
        """
        self._js_click_locator(self.MAIN_SMARTDOCS_BUTTON)

    def click_main_connection_manager(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Менеджер соединений
        """
        self._js_click_locator(self.MAIN_CONNECTION_MANAGER_BUTTON)

    def click_main_settings(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        Настройки
        """
        self._js_click_locator(self.MAIN_SETTINGS_BUTTON)

    def click_main_about(self) -> None:
        """
        Нажимает на кнопку в левом меню под названием\n
        О программе
        """
        self._js_click_locator(self.MAIN_ABOUT_BUTTON)

    def click_close_plugin(self) -> None:
        """
        Нажимает на кнопку закрытия плагина.
        """
        self._js_click_locator(self.CLOSE_PLUGIN_BUTTON)

