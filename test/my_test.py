import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.driver import DriverOnlyOffice
from src.pages.home_page import HomePage
from src.pages.editor_page import EditorPage
from src.pages.plugin_page import PluginPage
from src.utils.timer import Timer, format_summary
from src.utils.logging_utils import setup_logging
import time

def main():
    logger = setup_logging()
    driver = DriverOnlyOffice()
    home = HomePage(driver)
    editorPage = EditorPage(driver)
    pluginPage = PluginPage(driver)

    timer = Timer().start()

    home.open_creation_cell()
    timer.mark("open_creation_cell")

    editorPage.click_plugin_button()
    editorPage.try_click_close()
    timer.mark("open_plugin_panel")

    pluginPage.click_sql_mode()
    pluginPage.sql_mode.click_make_sql()
    timer.mark("enter_sql_mode")
    pluginPage.screenshot("sql_mode_open", raise_on_fail=False)

    sql_manager = pluginPage.sql_mode.sql_manager

    sql_manager.select_connection("ora_ED733E60")
    sql_manager.click_add_query_button()
    sql_manager.enter_query_name("123")
    sql_manager.confirm_add_query()
    card = sql_manager.expand_query_card("123")
    sql_manager.select_query_connection(card, "pgl_ED733E60")
    timer.mark("prepare_query_card")

    sql_manager.set_query_text(
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

    sql_manager.click_query_preview(card, 30)
    timer.mark("preview_query")

    sql_manager.click_export(card)
    sql_manager.select_export_destination("В новый файл")
    time.sleep(2)
    sql_manager.select_export_destination("В текущий документ")
    sql_manager.confirm_export(30)
    # читает данные для вывода куда то 
    title, text = sql_manager.read_success_message()
    logger.info("Success dialog: %s | %s", title, text)
    pluginPage.screenshot("export_success_dialog", raise_on_fail=False)
    sql_manager.click_success_ok(30)
    timer.mark("export_flow")

    sql_manager.click_query_delete(card)
    timer.mark("cleanup")

    summary = timer.summary()
    logger.info("Timing summary (ms):\n%s", format_summary(summary))
    if hasattr(logger, "log_file"):
        logger.info("Log file: %s", logger.log_file)

if __name__ == "__main__":
    try:
        main()
    except Exception:
        import logging
        logging.getLogger("oo").exception("Test run failed")
        raise
