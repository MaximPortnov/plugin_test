from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from .base_page import BasePage


class HomePage(BasePage):
    """
    Пример стартовой страницы (вне iframe).
    """

    CREATION_CELL = (By.XPATH, "//div[@class='document-creation-grid']/div[@data-id='cell']")

    def open_creation_cell(
        self,
        locator: tuple[str, str] = CREATION_CELL,
        timeout: int = 10,
    ) -> None:
        """
        Берет window_handles, кликает по плитке создания документа и переключается в новое окно/вкладку.
        """
        self._log("open_creation_cell")
        before = set(self.driver.get_window_handles())
        self._js_click_locator(locator)

        def new_handle_available(drv):
            handles = set(drv.window_handles)
            diff = handles - before
            return diff.pop() if diff else False

        new_handle = WebDriverWait(self.driver.driver, timeout).until(
            new_handle_available
        )
        self.driver.set_window_handle(new_handle)
