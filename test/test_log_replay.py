import sys
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
    """Поднимает OnlyOffice, открывает документ и SQL Manager (реплей из interaction-log)."""
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
        "sql_manager": sql_manager,
    }
    yield ctx

    try:
        driver.driver.quit()
    except Exception:
        pass


def test_replay_interaction_log_1770364153743(oo_ctx):
    """
    Реплей шагов из interaction-log-1770364153743.jsonl:
    - выбрать соединение pgl
    - создать запрос '123'
    - вставить большой SQL
    - предпросмотр, экспорт, подтверждение, OK
    """
    sqlm: SqlManagerPage = oo_ctx["sql_manager"]
    query_name = "123"

    sqlm.select_connection("pgl")
    sqlm.click_add_query_button()
    sqlm.enter_query_name(query_name)
    sqlm.confirm_add_query()
    card = sqlm.expand_query_card(query_name)

    sql_text = """
        select p.businessentityid
        , p.persontype
        , p.namestyle
        , p.title
        , p.firstname
        , p.middlename
        , p.lastname
        , p.suffix
        , p.emailpromotion
        , p.additionalcontactinfo
        , p.demographics
        , p.rowguid
        , p.modifieddate

        from person.person p
    """
    sqlm.set_query_text(card, sql_text)
    sqlm.click_query_preview(card, timeout=60)

    sqlm.click_export(card)
    # лог не фиксировал выбор направления, оставляем дефолт
    sqlm.confirm_export(timeout=60)
    sqlm.read_success_message()
    sqlm.click_success_ok(timeout=30)
