from selenium.webdriver.common.by import By
from .base_page import BasePage


class EditorPage(BasePage):
    """
    Пример страницы редактора OnlyOffice.
    """

    def __init__(self, driver):
        super().__init__(driver, timeout=10)

    PLUGIN_BUTTON = (
        By.XPATH,
        "//section[@id='plugins-panel']/div/span/button[descendant::*[text()='Слайдер'] and descendant::*[text()='Данные']]",
    )
    PLUGINS_TAB = (
        By.XPATH,
        "//ul[@role='tablist']/li[@data-layout-name='toolbar-plugins']/a",
    )
    CLOSE_BUTTON = (By.XPATH, "//div[@class='tool close']")

    def open_plugins_tab(self) -> None:
        """
        Клик по вкладке тулбара 'Плагины'.
        """
        self._log("open_plugins_tab")
        self._js_click_locator(self.PLUGINS_TAB)

    def click_plugin_button(self) -> None:
        """
        Клик по кнопке плагина с текстами "Слайдер" и "Данные".
        """
        self._log("click_plugin_button")
        self._js_click_locator(self.PLUGIN_BUTTON)

    def click_close(self) -> None:
        """
        Кликает по кнопке закрытия всплывающего окна (div.tool.close).
        """
        self._log("click_close")
        self._js_click_locator(self.CLOSE_BUTTON)

    def try_click_close(self) -> bool:
        """
        Пытается кликнуть по кнопке закрытия всплывающего окна (div.tool.close).
        """
        self._log("try_click_close")
        el = self._wait_locator(self.CLOSE_BUTTON, timeout=1)
        if el:
            self._js_click(el)
        # self._try_click_locator(self.CLOSE_BUTTON, timeout=1)
