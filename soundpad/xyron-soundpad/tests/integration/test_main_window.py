from PySide6.QtCore import Qt

from soundpad.core.config import SettingsStore
from soundpad.ui.theme.theme import apply_theme
from soundpad.ui.viewmodels.sound_table_model import COLUMN_NAME
from soundpad.ui.views.main_window import MainWindow


def make_window(qtbot, library, settings_store):
    apply_theme(qtbot._request.getfixturevalue("qapp"))
    window = MainWindow(library, settings_store)
    qtbot.addWidget(window)
    window.show()
    return window


def seed(library):
    entries = {e.name: e for e in library.category_entries()}
    library.add_sound_record("Airhorn", "a.wav", 1200, entries["Memes"].category_id)
    library.add_sound_record("Bruh", "b.wav", 800, entries["Memes"].category_id)
    library.add_sound_record("Victory", "c.wav", 3000, entries["Games"].category_id)
    library.add_sound_record("Loose", "d.wav", 500, None)


def test_layout_has_reference_structure(qtbot, library, settings_store):
    window = make_window(qtbot, library, settings_store)
    menu_titles = [a.text().replace("&", "") for a in window.menuBar().actions()]
    assert menu_titles == ["File", "Edit", "Play", "Window", "Help"]
    assert window.toolbar is not None
    assert window.categories.count() == 6
    headers = [
        window.proxy.headerData(i, Qt.Orientation.Horizontal) for i in range(window.proxy.columnCount())
    ]
    assert headers == ["#", "Tag / Name", "Duration", "Hotkey"]
    assert window.stats is not None
    assert window.statusBar() is not None


def test_categories_show_counts(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    labels = [window.categories.item(i).text() for i in range(window.categories.count())]
    assert labels[0] == "My Sounds  (4)"
    assert "Memes  (2)" in labels
    assert "Uncategorized  (1)" in labels


def test_selecting_category_filters_table(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    assert window.proxy.rowCount() == 4
    window.categories.select_key("uncategorized")
    assert window.proxy.rowCount() == 1
    assert window.stats.value("category") == "Uncategorized"
    assert window.stats.value("sounds") == "1"


def test_instant_search_filters_rows(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    qtbot.keyClicks(window.search, "air")
    assert window.proxy.rowCount() == 1
    assert window.proxy.index(0, COLUMN_NAME).data() == "Airhorn"
    window.search.clear()
    assert window.proxy.rowCount() == 4


def test_sorting_by_name_and_duration(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    window.table.sortByColumn(COLUMN_NAME, Qt.SortOrder.AscendingOrder)
    names = [window.proxy.index(r, COLUMN_NAME).data() for r in range(window.proxy.rowCount())]
    assert names == sorted(names, key=str.casefold)
    window.table.sortByColumn(2, Qt.SortOrder.DescendingOrder)
    assert window.proxy.index(0, COLUMN_NAME).data() == "Victory"


def test_multi_selection_updates_stats(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    window.table.selectAll()
    assert window.stats.value("selected") == "4"
    assert len(window.table.selected_sound_ids()) == 4


def test_rename_persists_to_database(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    index = window.proxy.index(0, COLUMN_NAME)
    assert window.proxy.setData(index, "Renamed", Qt.ItemDataRole.EditRole)
    entry = library.category_entries()[0]
    assert "Renamed" in [s.name for s in library.sounds_for(entry)]


def test_settings_persist_across_restart(qtbot, library, settings_store):
    seed(library)
    window = make_window(qtbot, library, settings_store)
    window.refresh_categories()
    window.categories.select_key("uncategorized")
    window.resize(900, 600)
    window.close()

    reloaded = SettingsStore(settings_store.path)
    reloaded.load()
    assert reloaded.settings.ui.last_category == "uncategorized"
    assert reloaded.settings.ui.window_width == 900

    second = MainWindow(library, reloaded)
    qtbot.addWidget(second)
    assert second.categories.current_key() == "uncategorized"


def test_audio_controls_disabled_until_engine_exists(qtbot, library, settings_store):
    window = make_window(qtbot, library, settings_store)
    assert not window.act_play.isEnabled()
    assert not window.toolbar.action_play.isEnabled()
