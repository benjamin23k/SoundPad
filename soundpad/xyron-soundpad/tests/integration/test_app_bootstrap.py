from soundpad.app import build_main_window
from soundpad.core.paths import AppPaths


def test_bootstrap_creates_data_layout_and_database(qtbot, tmp_path):
    paths = AppPaths.resolve(data_dir=tmp_path / "data")
    window, database = build_main_window(paths)
    qtbot.addWidget(window)
    try:
        assert paths.database_file.exists()
        assert paths.sounds_dir.is_dir()
        assert window.categories.count() == 6
    finally:
        database.dispose()
