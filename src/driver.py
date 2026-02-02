from pathlib import Path
import os
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.relative_locator import RelativeBy
from selenium.common.exceptions import NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.remote.webelement import WebElement


class DriverOnlyOffice:
    def __init__(
        self,
        driver_path: Path | None = None,
        debugger_address: str = "127.0.0.1:9222",
    ):
        self._build_driver(driver_path, debugger_address)

    def _build_driver(
        self,
        driver_path: Path | None = None,
        debugger_address: str = "127.0.0.1:9222",
    ) -> webdriver.Chrome:
        chrome_options = Options()
        chrome_options.add_experimental_option("debuggerAddress", debugger_address)

        if driver_path is None:
            env_path = os.getenv("CHROMEDRIVER_PATH")
            if env_path:
                driver_path = Path(env_path)
            else:
                base = (
                    Path(__file__).resolve().parent
                    if "__file__" in globals()
                    else Path.cwd()
                )
                driver_path = (
                    base.parent / "chromedriver-win64" / "chromedriver.exe"
                ).resolve()

        self.driver = webdriver.Chrome(
            service=Service(str(driver_path)), options=chrome_options
        )
        return self.driver

    def find_element_in_frames(
        self, by: str | RelativeBy = By.ID, selector: str | None = None
    ) -> WebElement | None:
        """
        Рекурсивно ищет элемент во всех iframe.
        Возвращает WebElement или None.
        """
        self.driver.switch_to.default_content()

        def rec():
            try:
                return self.driver.find_element(by, selector)
            except NoSuchElementException:
                pass
            iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
            for iframe in iframes:
                try:
                    self.driver.switch_to.frame(iframe)
                    found = rec()
                    if found:
                        return found
                    self.driver.switch_to.parent_frame()
                except StaleElementReferenceException:
                    self.driver.switch_to.parent_frame()
                except Exception:
                    self.driver.switch_to.parent_frame()

            return None
        return rec()

    def switch_to_frame(self, frame: str | int | WebElement):
        self.driver.switch_to.frame(frame)

    def switch_window(self, id):
        handles = self.driver.window_handles
        target = handles[id]
        self.driver.switch_to.window(target)

    def get_window_handles(self) -> list[str]:
        return self.driver.window_handles

    def get_current_window_handle(self) -> str:
        return self.driver.current_window_handle

    def set_window_handle(self, window_name: str):
        self.driver.switch_to.window(window_name)
