import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.driver import DriverOnlyOffice
from src.pages.home_page import HomePage
from src.pages.editor_page import EditorPage
from src.pages.plugin_page import PluginPage
from src.pages.sql_mode_page import SqlModePage
from src.pages.sql_manager_page import SqlManagerPage
from src.utils.timer import Timer, format_summary
from src.utils.logging_utils import setup_logging
import time

def main():
    logger = setup_logging()
    driver = DriverOnlyOffice()
    home_page = HomePage(driver)
    editor_page = EditorPage(driver)
    plugin_page = PluginPage(driver)
    sql_mode_page = SqlModePage(driver)
    sql_manager_page = SqlManagerPage(driver)

    timer = Timer().start()

    home_page.open_creation_cell()
    timer.mark("open_creation_cell")

    editor_page.click_plugin_button()
    editor_page.try_click_close()
    timer.mark("open_plugin_panel")

    plugin_page.click_main_sql_mode()
    sql_mode_page.click_sql_manager()
    timer.mark("enter_sql_mode")
    plugin_page.screenshot("sql_mode_open", raise_on_fail=False)


    sql_manager_page.select_connection("ora")
    sql_manager_page.click_add_query_button()
    sql_manager_page.enter_query_name("123")
    sql_manager_page.confirm_add_query()
    card = sql_manager_page.expand_query_card("123")
    sql_manager_page.select_query_connection( "pgl")
    timer.mark("prepare_query_card")

    sql_manager_page.set_query_text(
        card,
        """
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
        """,
    )
    timer.mark("set_query_text")

    sql_manager_page.click_query_preview( 30)
    timer.mark("preview_query")

    sql_manager_page.click_export()
    sql_manager_page.select_export_destination("В новый файл")
    time.sleep(2)
    sql_manager_page.select_export_destination("В текущий документ")
    sql_manager_page.confirm_export(30)
    # читает данные для вывода куда то 
    title, text = sql_manager_page.read_success_message()
    logger.info("Success dialog: %s | %s", title, text)
    plugin_page.screenshot("export_success_dialog", raise_on_fail=False)
    sql_manager_page.click_success_ok(30)
    timer.mark("export_flow")

    sql_manager_page.click_query_delete()
    timer.mark("cleanup")

    summary = timer.summary()
    logger.info("Timing summary (ms):\n%s", format_summary(summary))
    if hasattr(logger, "log_file"):
        logger.info("Log file: %s", logger.log_file)


# --- pytest entrypoint ---
def test_onlyoffice_e2e():
    """
    Полный E2E сценарий в одном тесте pytest.
    Использует ту же логику, что и main(), чтобы можно было запускать через `pytest`.
    """
    main()

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import logging
        logging.getLogger("oo").exception("Test run failed")
        raise
