from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import RelativeBy
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.remote.webelement import WebElement

from ..utils.logging_utils import get_logger
from ..utils.visual import assert_screenshot


class BasePage:
    """
    Базовый Page Object, использует find_element_in_frames для неявного поиска в iframe.
    """

    def __init__(self, driver, timeout: int = 10):
        self.driver = driver
        self.wait = WebDriverWait(driver.driver, timeout)
        self.logger = get_logger(self.__class__.__name__.lower())

    def _log(self, message: str, *args, level: str = "info") -> None:
        if self.logger:
            log_fn = getattr(self.logger, level, self.logger.info)
            log_fn(message, *args)

    def _find(
        self, by: str | RelativeBy = None, selector: str | None = None
    ) -> WebElement:
        def _locate(_):
            return self.driver.find_element_in_frames(by, selector)

        el = self.wait.until(_locate)
        if el is None:
            raise NoSuchElementException(
                f"Элемент {by}='{selector}' не найден в iframe"
            )
        return el
    
    def _wait_find(
        self, by: str | RelativeBy = None, selector: str | None = None, timeout: int = 10
    ) -> WebElement:
        def _locate(_):
            return self.driver.find_element_in_frames(by, selector)

        el = WebDriverWait(self.driver.driver, timeout).until(_locate)
        if el is None:
            raise NoSuchElementException(
                f"Элемент {by}='{selector}' не найден в iframe"
            )
        return el

    def _js_click(self, element: WebElement) -> None:
        # self.driver.driver.execute_script(
        #     "arguments[0].scrollIntoView({block:'center'});", element
        # )
        self.driver.driver.execute_script("arguments[0].click();", element)
        # element.click()
    def _click(self, element: WebElement) -> None:
        # self.driver.driver.execute_script(
        #     "arguments[0].scrollIntoView({block:'center'});", element
        # )
        self.driver.driver.execute_script("arguments[0].click();", element)
        # element.click()
    def _find_locator(self, locator: tuple[str, str]) -> WebElement:
        by, selector = locator
        return self._find(by, selector)
    def _wait_find_locator(self, locator: tuple[str, str], timeout:int = 10) -> WebElement:
        by, selector = locator
        return self._wait_find(by, selector, timeout)

    
    def _js_click_locator(self, locator: tuple[str, str]) -> WebElement:
        el = self._find_locator(locator)
        self._js_click(el)
        return el
    
    def _click_locator(self, locator: tuple[str, str]) -> WebElement:
        el = self._find_locator(locator)
        self._click(el)
        return el

    # --- Visual regression helpers ---
    def screenshot(self, name: str, element: WebElement | None = None, **kwargs):
        """Снимает скрин и сравнивает с baseline (см. utils.visual.assert_screenshot)."""
        return assert_screenshot(
            self.driver.driver, name=name, element=element, logger=self.logger, **kwargs
        )

    def screenshot_locator(self, locator: tuple[str, str], name: str, **kwargs):
        el = self._find_locator(locator)
        return self.screenshot(name, element=el, **kwargs)
    

    # def _try_click_locator(self, locator: tuple[str, str], timeout: int = 3) -> bool:
    #     """
    #     Пытается кликнуть локатор за отведённое время.
    #     Возвращает True при успехе, False если элемент не появился/недоступен.
    #     Ошибки других типов пробрасываются.
    #     """
    #     by, selector = locator
    #     try:
    #         el = WebDriverWait(self.driver.driver, timeout).until(
    #             lambda d: self.driver.find_element_in_frames(by, selector)
    #         )
    #         if el is None:
    #             return False
    #         self._click(el)
    #         return True
    #     except TimeoutException:
    #         return False

    def _wait_locator(
        self,
        locator: tuple[str, str],
        timeout: int = 3,
        require_displayed: bool = True,
        require_enabled: bool = True,
    ) -> WebElement | None:
        """
        Ждёт появления локатора (учитывая iframe), опционально проверяет visible/enabled,
        затем кликает. Возвращает True при успехе, False при таймауте.
        """
        by, selector = locator

        def _ready(_):
            el = self.driver.find_element_in_frames(by, selector)
            if not el:
                return False
            if require_displayed and not el.is_displayed():
                return False
            if require_enabled and not el.is_enabled():
                return False
            return el

        try:
            el = WebDriverWait(self.driver.driver, timeout).until(_ready)
            return el
        except TimeoutException:
            return None
