import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.driver import DriverOnlyOffice
from src.pages.home_page import HomePage
from src.pages.editor_page import EditorPage
from src.pages.plugin_page import PluginPage
from src.pages.sql_mode_page import SqlModePage
from src.pages.sql_manager_page import SqlManagerPage


@pytest.fixture(scope="module")
def oo_ctx():
    """Поднимает драйвер OnlyOffice и открывает SQL Manager один раз на модуль."""
    driver = DriverOnlyOffice()
    home = HomePage(driver)
    editor = EditorPage(driver)
    plugin = PluginPage(driver)
    sql_mode = SqlModePage(driver)
    sql_manager = SqlManagerPage(driver)

    home.open_creation_cell()
    editor.click_plugin_button()
    editor.try_click_close()
    plugin.click_main_sql_mode()
    sql_mode.click_sql_manager()

    ctx = {
        "driver": driver,
        "home": home,
        "editor": editor,
        "plugin": plugin,
        "sql_mode": sql_mode,
        "sql_manager": sql_manager,
    }
    yield ctx

    try:
        driver.driver.quit()
    except Exception:
        pass


def test_sql_manager_full_flow(oo_ctx):
    """
    В одной функции последовательно проверяются все ключевые действия SQL Manager.
    """
    sqlm: SqlManagerPage = oo_ctx["sql_manager"]
    query_name = f"pytest_{int(time.time())%100000}"

    # 1. выбрать соединение слева
    sqlm.select_connection("ora")

    # 2. добавить запрос
    sqlm.click_add_query_button()
    sqlm.enter_query_name(query_name)
    sqlm.confirm_add_query()
    card = sqlm.expand_query_card(query_name)

    # 3. выбрать соединение в карточке
    sqlm.select_query_connection(card, "pgl")

    # 4. задать текст и предпросмотр
    sqlm.set_query_text(card, "select 1 as one")
    sqlm.click_query_preview(card, timeout=30)

    # 5. экспорт (без подтверждения завершения)
    sqlm.click_export(card)
    sqlm.select_export_destination("В новый файл")

    # 6. удалить созданный запрос
    sqlm.click_query_delete(card)
